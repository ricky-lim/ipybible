"""Module for ipybible app"""
import ipyvuetify as v  # type: ignore
import traitlets  # type: ignore
import bqplot as bq  # type: ignore
import pandas as pd  # type: ignore

from dataclasses import dataclass
from typing import List, Dict, ClassVar, Tuple
from bqplot.market_map import MarketMap  # type: ignore

from ipybible.bible import Bible, Verse
from ipybible.bible_cloud import generate_cloud
from ipybible.misc import count_words

BookName = str
# Similarity Ratio
SimRatio = float
LANGUAGE_TO_VERSIONS = {"EN": ["kjv", "basicenglish"], "NL": ["statenvertaling"]}
VERSION_TO_LANGUAGE = {"kjv": "EN", "statenvertaling": "NL", "basicenglish": "EN"}


def get_default_bible_version(language):
    return LANGUAGE_TO_VERSIONS[language][0]


class VerseList(v.VuetifyTemplate):
    """Show a list of verses in a given chapter of a book from a bible's version"""

    items = traitlets.List([]).tag(sync=True)
    title = traitlets.Unicode("").tag(sync=True)
    template = traitlets.Unicode(
        """
        <v-flex xs12 sm12 md5 lg5 xl5 offset-xs1>
          <h2 class="justify-center">{{ title }}</h2>
          <v-card flat style="background: rgba(255,255,255,0);"
                  v-for="(item, index) in items">
            <v-card-text>
              <v-badge left color="red">
                  <template v-slot:badge>
                    <span>{{ index + 1 }}</span>
                  </template>
                  <span>
                    {{ item }}
                   </span>
              </v-badge>
            </v-card-text>
          </v-card>
        </v-flex>
    """
    ).tag(sync=True)

    def __init__(self, verses: List[Verse], title, **kwargs):
        super().__init__(**kwargs)
        self.items = [verse.text for verse in verses]
        self.title = title


@dataclass
class BibleApp:
    __search_mode = False
    search_found = False
    # Min, Max length of words for a phrase search
    MIN_QUERY_WORDS: ClassVar[int] = 3
    MAX_QUERY_WORDS: ClassVar[int] = 5

    def __post_init__(self):
        self.language_selected = "EN"
        languages = list(LANGUAGE_TO_VERSIONS.keys())
        self.language_selector = v.Select(
            v_model=self.language_selected, items=languages, prepend_icon="translate"
        )
        self.language_selector.on_event("change", self.__on_language_changed)
        self.bible_version_selected = get_default_bible_version(self.language_selected)
        versions: List[str] = list(LANGUAGE_TO_VERSIONS[self.language_selected])
        self.version_selector = v.Select(
            v_model=self.bible_version_selected, items=versions, prepend_icon="bookmark"
        )
        self.version_selector.on_event("change", self.__on_version_changed)

        self.bible = Bible(
            version=self.bible_version_selected, language=self.language_selected
        )

        self.search_mode_switcher = v.Switch(v_model=False, label="Search Mode")
        self.search_text = v.TextField(label="Phrase search", v_model="")
        self.search_submit = v.Btn(color="primary", children=["Submit"])
        self.search_form = v.Html(tag="div", children=[self.search_mode_switcher])

        self.search_mode_switcher.on_event("change", self.__on_search_mode_switched)
        self.search_submit.on_event("click", self.search_phrase)

        yes_remove_btn = v.Btn(children=["Yes"], color="green darken-1", flat=True)
        no_remove_btn = v.Btn(children=["No"], color="green darken-1", flat=True)

        yes_remove_btn.on_event("click", self.__continue_remove_search)
        no_remove_btn.on_event("click", self.__cancel_remove_search)
        self.search_remove_dialog = v.Dialog(
            v_model=False,
            width="500",
            persistent=True,
            children=[
                v.Card(
                    children=[
                        v.CardTitle(
                            primary_title=True,
                            class_="headline",
                            children=["Remove search"],
                        ),
                        v.CardText(children=["Are you sure?"]),
                        v.CardActions(
                            children=[
                                v.Spacer(children=[]),
                                no_remove_btn,
                                yes_remove_btn,
                            ]
                        ),
                    ]
                )
            ],
        )
        book_names = [book.name for book in self.bible.books]
        self.book_selector = v.Select(
            v_model=book_names[0], items=book_names, prepend_icon="book"
        )
        self.book_selector.on_event("change", self.__on_book_selected)
        self.book_selected = self.book_selector.v_model
        self.total_chapter: int = self.bible.book(self.book_selected).num_chapter
        self.chapter_selected = 1
        self.chapter_selector = self.create_chapter_selector(
            num_chapter=self.total_chapter,
            idx_chapter_selected=self.chapter_selected - 1,
        )
        self.bible_nav_selector = v.Html(
            tag="div",
            children=[
                self.search_form,
                self.language_selector,
                self.version_selector,
                self.book_selector,
                self.chapter_selector,
            ],
        )
        self.nav_content = v.Layout(
            pa_4=True,
            _metadata={"mount_id": "content-nav"},
            column=True,
            children=[self.bible_nav_selector],
        )
        self.bible_loading = v.ProgressLinear(indeterminate=True)
        self.cloud_loading = v.ProgressLinear(indeterminate=True)
        chapter_text = (
            self.bible.book(self.book_selected)
            .chapter(self.chapter_selected)
            .clean_text()
        )
        verse_list = self.display_verse_list()
        self.main_content = v.Layout(
            _metadata={"mount_id": "content-main"},
            row=True,
            wrap=True,
            children=[
                self.bible_loading,
                self.draw_chapter_cloud(chapter_text),
                verse_list,
                self.search_remove_dialog,
            ],
        )

    @property
    def search_mode(self) -> bool:
        return self.__search_mode

    @search_mode.setter
    def search_mode(self, value: bool):
        self.__search_mode = value

    def create(self) -> Tuple[v.Layout, v.Layout]:
        return self.nav_content, self.main_content

    def display_verse_list(self) -> VerseList:
        """
        Display verses' text as a list
        :return:  VerseList, vuetify template object
        """
        num_verse = (
            self.bible.book(self.book_selected).chapter(self.chapter_selected).num_verse
        )
        verse_list = VerseList(
            verses=self.bible.book(self.book_selected)
            .chapter(self.chapter_selected)
            .verses,
            title=f"{self.book_selected.title()} {self.chapter_selected}: 1-{num_verse}",
        )
        return verse_list

    def draw_chapter_cloud(self, chapter_text: str) -> v.Flex:
        """
        Draw frequency of words as clouds
        :param chapter_text: str, chapter text
        :return: Flex layout object
        """
        self.bible_loading.active = True
        self.cloud_loading.active = True if self.search_mode else False
        title_cloud = f"{self.book_selected.title()} {self.chapter_selected}"
        chapter_cloud = generate_cloud(text=chapter_text)
        self.bible_loading.active = False
        self.cloud_loading.active = False
        return v.Flex(
            xs12=True,
            sm12=True,
            md4=True,
            lg4=True,
            xl4=True,
            offset_xs1=True,
            children=[
                v.Html(tag="h2", class_="justify-center", children=[title_cloud]),
                chapter_cloud,
            ],
        )

    def update_main_content(self) -> None:
        """
        Change's the main_content of the app's upon application state changes
        :return: None
        """
        chapter_text = (
            self.bible.book(self.book_selected)
            .chapter(self.chapter_selected)
            .clean_text()
        )
        chapter_cloud = self.draw_chapter_cloud(chapter_text)
        verse_list = self.display_verse_list()
        if self.search_mode and self.search_found:
            self.main_content.children = [
                self.bible_loading,
                # Barplot's of book similarity
                v.Flex(
                    xs12=True,
                    sm12=True,
                    md5=True,
                    lg5=True,
                    xl5=True,
                    offset_xs1=True,
                    children=[
                        v.Html(tag="h2", children=[f"Book Similarity Ratio"]),
                        self.book_to_similarity_barplot,
                    ],
                ),
                # Marketplot's of chapter similarity
                v.Flex(
                    xs12=True,
                    sm12=True,
                    md6=True,
                    lg6=True,
                    xl6=True,
                    children=[
                        v.Html(
                            tag="h2",
                            children=[
                                f"Chapter Similarity Ratio: {self.book_selected.title()}"
                            ],
                        ),
                        self.chapter_to_similarity_marketmap,
                    ],
                ),
                self.cloud_loading,
                chapter_cloud,
                verse_list,
                self.search_remove_dialog,
            ]
        else:
            self.main_content.children = [
                self.bible_loading,
                chapter_cloud,
                verse_list,
                self.search_remove_dialog,
            ]

    def create_chapter_selector(
        self, num_chapter, idx_chapter_selected: int
    ) -> v.BtnToggle:
        """
        Create toggle's button for chapters
        :param num_chapter: number of toggle's buttons
        :param idx_chapter_selected: selected index (the first to be toggled)
        :return: toggle button
        """

        chapter_buttons = []
        for i in range(num_chapter):
            button = v.Btn(flat=True, block=True, children=[str(i + 1)])
            button.on_event("click", self.__on_chapter_clicked)
            chapter_buttons.append(
                v.Flex(xs2=True, sm2=True, md2=True, lg2=True, children=[button])
            )

        selector = v.BtnToggle(
            v_model=idx_chapter_selected,
            children=[v.Layout(row=True, wrap=True, children=chapter_buttons)],
        )

        return selector

    def search_phrase(self, *_):
        """Run the search"""
        self.search_text.loading = True
        self.bible_loading.active = True
        query_text = self.search_text.v_model
        if count_words(query_text) > BibleApp.MAX_QUERY_WORDS:
            err_msg = f"Max words Limit to {BibleApp.MAX_QUERY_WORDS}"
            self.search_text.error_messages = err_msg
            self.search_text.loading = False
            self.bible_loading.active = False
            return
        if count_words(query_text) < BibleApp.MIN_QUERY_WORDS:
            err_msg = f"At least {BibleApp.MIN_QUERY_WORDS} words are required"
            self.search_text.error_messages = err_msg
            self.search_text.loading = False
            self.bible_loading.active = False
            return

        self.search_mode = True
        self.search_text.error_messages = ""
        self.book_to_similarity = self.bible.book_to_similarity(query_text)
        if self.book_to_similarity == {}:
            self.main_content.children = [
                v.Flex(
                    xs12=True,
                    sm12=True,
                    md12=True,
                    lg12=True,
                    xl12=True,
                    children=[
                        v.Html(
                            tag="h2",
                            children=[
                                f"Search phrase not found: '{self.search_text.v_model}'"
                            ],
                        )
                    ],
                ),
                self.search_remove_dialog,
            ]
            self.search_found = False
            self.search_text.loading = False
            self.bible_loading.active = False
            return

        self.search_found = True
        self.book_to_similarity_barplot = self.create_book_to_similarity_barplot(
            self.book_to_similarity
        )
        self.book_selector.items = list(self.book_to_similarity.keys())
        self.book_selected: str = list(self.book_to_similarity.keys())[0]
        self.book_selector.v_model = self.book_selected
        chapter_to_similarity = self.bible.book(
            self.book_selected
        ).chapter_to_similarity(query_text)

        self.chapter_to_similarity_marketmap = self.create_chapter_market_map(
            chapter_to_similarity
        )
        self.similarity_plots = v.Layout(
            row=True,
            wrap=True,
            children=[
                self.book_to_similarity_barplot,
                self.chapter_to_similarity_marketmap,
            ],
        )
        # Trigger updates from book -> chapter -> verses to be displayed
        self.__on_book_selected()
        self.search_text.loading = False
        self.bible_loading.active = False

    def create_book_to_similarity_barplot(
        self, book_to_similarity: Dict[BookName, SimRatio]
    ) -> bq.Figure:
        x_ord = bq.OrdinalScale(reverse=True)
        y_sc = bq.LinearScale()

        bar = bq.Bars(
            x=list(book_to_similarity.keys()),
            y=list(book_to_similarity.values()),
            scales={"x": x_ord, "y": y_sc},
            selected=[0],
            # selected_stroke="gray",
            selected_style={"fill": "red"},
            orientation="horizontal",
            colors=["gray"],
        )
        bar.interactions = {"click": "select"}

        ax_x = bq.Axis(
            scale=x_ord, orientation="vertical", tick_style={"font-size": "large"}
        )
        ax_y = bq.Axis(scale=y_sc, tick_format=".2f", num_ticks=3)

        margin = dict(top=10, bottom=20, left=80, right=10)
        fig = bq.Figure(
            marks=[bar],
            axes=[ax_x, ax_y],
            padding_x=0.005,
            padding_y=0.01,
            fig_margin=margin,
        )
        # fig.layout.min_width = '300px'
        fig.layout.min_height = "700px"
        fig.layout.width = "auto"
        fig.layout.height = "auto"

        def show_chapter_similarity(_, target):
            self.bible_loading.active = True
            selected_book: str = target["data"]["x"]
            self.book_selector.v_model = selected_book
            self.book_selected = selected_book
            self.__on_book_selected()

        bar.on_element_click(show_chapter_similarity)
        return fig

    def create_chapter_market_map(
        self, chapter_to_similarity: Dict[int, float]
    ) -> MarketMap:

        col = bq.ColorScale()
        ax_c = bq.ColorAxis(scale=col, label="ratio", visible=True, num_ticks=3)
        data = pd.DataFrame.from_dict(
            chapter_to_similarity, orient="index", columns=["sim"]
        )

        market_map = MarketMap(
            names=list(chapter_to_similarity.keys()),
            cols=5,
            color=list(chapter_to_similarity.values()),
            scales={"color": col},
            axes=[ax_c],
            ref_data=data,
            freeze_tooltip_location=True,
            # colors=["#ccc"],
            colors=["#ccc"],
            enable_select=True,
            selected_stroke="red",
            selected=[self.chapter_selected],
            stroke="gray",
            group_stroke="gray",
            hovered_stroke="black",
            font_style={"font-size": "large", "fill": "white"},
        )
        # market_map.layout.min_width = "100%"
        market_map.layout.min_height = "700px"
        market_map.layout.width = "auto"
        market_map.layout.height = "auto"

        def selected_index_changed(change):
            try:
                self.chapter_selected = change["new"][-1]
                market_map.selected = [self.chapter_selected]
                # Note: v_model from chapter selector is an index starting from 0
                self.chapter_selector.v_model = self.chapter_selected - 1
                self.update_main_content()
            except KeyError:
                pass

        market_map.observe(selected_index_changed, "selected")
        return market_map

    def __on_search_mode_switched(self, *_) -> None:
        """Callback as search mode toggled"""
        self.search_mode = self.search_mode_switcher.v_model
        if self.search_mode:
            self.search_form.children = [
                self.search_mode_switcher,
                self.search_text,
                self.search_submit,
            ]
        else:
            if self.search_text.v_model == "":
                self.search_form.children = [self.search_mode_switcher]
                return
            else:
                self.search_remove_dialog.v_model = True

    def __on_language_changed(self, *_) -> None:
        """Callback as language changed"""
        self.language_selector.loading = True
        self.language_selected = self.language_selector.v_model
        # Default to choose the first's bible's version
        self.bible_version_selected = LANGUAGE_TO_VERSIONS[self.language_selected][0]
        self.version_selector.v_model = self.bible_version_selected
        self.version_selector.items = LANGUAGE_TO_VERSIONS[self.language_selected]
        self.__on_version_changed()
        self.language_selector.loading = False

    def __on_version_changed(self, *_) -> None:
        """Callback as version changed"""
        self.version_selector.loading = True
        self.bible_version_selected = self.version_selector.v_model
        try:
            self.bible = Bible(
                version=self.bible_version_selected, language=self.language_selected
            )
        except ValueError:
            self.language_selector.error_messages = (
                f"Bible version {self.bible_version_selected} ERROR"
            )
            self.version_selector.loading = False
        else:
            if self.search_mode:
                self.version_selector.loading = False
                self.search_phrase()
            else:
                book_names: List[str] = [book.name for book in self.bible.books]
                self.book_selector.items = book_names
                self.book_selector.v_model = (
                    self.book_selected if self.book_selected else book_names[0]
                )
                self.__on_book_selected()
        finally:
            self.version_selector.loading = False

    def __on_book_selected(self, *_) -> None:
        self.book_selector.loading = True
        self.book_selected = self.book_selector.v_model
        try:
            self.total_chapter: int = self.bible.book(self.book_selected).num_chapter
        except ValueError:
            self.book_selector.error_messages = "Total number of chapters not found"
            self.book_selector.loading = False
            return

        if self.search_mode and self.search_found:
            chapter_to_similarity = self.bible.book(
                self.book_selected
            ).chapter_to_similarity(self.search_text.v_model)
            # Default to the first chapter,
            # given that chapter_to_similarity is sorted from highest to lowest score
            self.chapter_selected = list(chapter_to_similarity.keys())[0]
            self.chapter_to_similarity_marketmap = self.create_chapter_market_map(
                chapter_to_similarity
            )
            # Update the barplot mark's selected attributes to the selected book
            books = list(self.book_to_similarity.keys())
            selected_book_idx = books.index(self.book_selected)
            self.book_to_similarity_barplot.marks[0].selected = [selected_book_idx]
        else:
            self.chapter_selected = (
                self.chapter_selected
                if (
                    self.chapter_selected
                    and self.chapter_selected <= self.total_chapter
                )
                else 1
            )

        self.chapter_selector = self.create_chapter_selector(
            num_chapter=self.total_chapter,
            idx_chapter_selected=self.chapter_selected - 1,
        )
        self.bible_nav_selector.children = [
            self.search_form,
            self.language_selector,
            self.version_selector,
            self.book_selector,
            self.chapter_selector,
        ]
        self.update_main_content()
        self.book_selector.loading = False

    def __on_chapter_clicked(self, widget, *_):
        """Add click handler for a toggling button to get the chapter"""

        self.chapter_selected = int(widget.children[0])
        if self.search_mode and self.search_found:
            self.chapter_to_similarity_marketmap.selected = [self.chapter_selected]
        self.update_main_content()

    def __continue_remove_search(self, *_):
        """Callback to a proceed response to a dialog to remove search"""
        self.search_mode = False
        self.search_mode_switcher.v_model = False
        self.search_remove_dialog.v_model = False
        self.search_text.v_model = ""
        self.search_form.children = [self.search_mode_switcher]
        self.book_selector.items = [book.name for book in self.bible.books]
        self.update_main_content()

    def __cancel_remove_search(self, *_):
        """Callback to a cancel response to a dialog to remove search"""
        self.search_mode = True
        self.search_mode_switcher.v_model = True
        self.search_remove_dialog.v_model = False
