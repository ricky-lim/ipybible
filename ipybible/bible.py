import requests
import json
import spacy  # type: ignore

from dataclasses import dataclass
from typing import Optional, ClassVar, Dict, List, Callable
from diskcache import Index, Cache  # type: ignore
from multiprocessing import Pool
from functools import partial
from collections import ChainMap

from ipybible import BIBLE_DATA_DIR, SEARCH_DATA_DIR
from ipybible.books import BOOKS
from ipybible.similarity import cosine_sim, SpacyLangModel, normalize_text
from ipybible.misc import sort_dict, normalize

BIBLE_INDEX = Index(str(BIBLE_DATA_DIR))
SEARCH_CACHE = Cache(str(SEARCH_DATA_DIR))
# Path(BIBLE_DATA_DIR).chmod(0o755)
# Path(BIBLE_DATA_DIR / "cache.db").chmod(0o755)
# Path(SEARCH_DATA_DIR).chmod(0o755)
# Path(SEARCH_DATA_DIR / "cache.db").chmod(0o755)


BookName = str
ChapterNum = int
SimRatio = float

LANGUAGE_TO_MODEL = {
    "EN": SpacyLangModel(
        nlp=spacy.load("en_core_web_sm"), stop_words=spacy.lang.en.stop_words.STOP_WORDS
    ),
    "NL": SpacyLangModel(
        nlp=spacy.load("nl_core_news_sm"),
        stop_words=spacy.lang.nl.stop_words.STOP_WORDS,
    ),
}


class BibleNotFound(Exception):
    pass


@dataclass
class Verse:
    number: int
    text: str
    language: str

    def clean_text(self) -> str:
        return normalize_text(
            index_name=BIBLE_INDEX,
            text=self.text,
            spacy_model=LANGUAGE_TO_MODEL[self.language],
        )


@dataclass
class Chapter:
    number: int
    language: str

    def __post_init__(self):
        self._verses = {}

    def add_verse(self, verse: Verse):
        if verse.number not in self._verses:
            self._verses[verse.number] = Verse(
                number=verse.number, text=verse.text, language=self.language
            )

    def verse(self, verse_number: int) -> Optional[Verse]:
        try:
            return self._verses.get(verse_number)
        except KeyError:
            return None

    @property
    def text(self) -> str:
        """Concatenate all verses for a given chapter number"""
        return " ".join([verse.text.strip() for verse in self._verses.values()])

    @property
    def num_verse(self) -> int:
        return len(self._verses.keys())

    @property
    def verses(self) -> List[Verse]:
        return list(self._verses.values())

    def clean_text(self) -> str:
        return normalize_text(
            text=self.text,
            spacy_model=LANGUAGE_TO_MODEL[self.language],
            index_name=BIBLE_INDEX,
        )

    def compute_sim(
        self, text: str, func: Callable[[str, str], float] = cosine_sim
    ) -> float:
        query_clean_text = normalize_text(
            text=text,
            spacy_model=LANGUAGE_TO_MODEL[self.language],
            index_name=BIBLE_INDEX,
        )
        return func(query_clean_text, self.clean_text())
        # return func(text, self.clean_text())


@dataclass
class Book:
    name: str
    language: str

    def __post_init__(self):
        self._chapters = {}

    def chapter(self, chapter_number: int) -> Chapter:
        if chapter_number not in self._chapters:
            chapter = Chapter(number=chapter_number, language=self.language)
            self._chapters[chapter_number] = chapter
        return self._chapters[chapter_number]

    @property
    def num_chapter(self):
        return len(self._chapters.keys())

    @property
    def chapters(self) -> List[Chapter]:
        return list(self._chapters.values())

    @property
    def text(self) -> str:
        """Returns all the text given its book's name"""
        return " ".join([chapter.text.strip() for chapter in self._chapters.values()])

    def clean_text(self) -> str:
        return normalize_text(
            text=self.text,
            spacy_model=LANGUAGE_TO_MODEL[self.language],
            index_name=BIBLE_INDEX,
        )

    def compute_sim(
        self, text: str, func: Callable[[str, str], float] = cosine_sim
    ) -> float:
        query_clean_text = normalize_text(
            text=text,
            spacy_model=LANGUAGE_TO_MODEL[self.language],
            index_name=BIBLE_INDEX,
        )
        return func(query_clean_text, self.clean_text())

    @staticmethod
    def compute_chapter_to_similarity(
        chapter: Chapter, text: str
    ) -> Dict[ChapterNum, SimRatio]:
        return {chapter.number: chapter.compute_sim(text)}

    @SEARCH_CACHE.memoize()
    def chapter_to_similarity(self, text: str) -> Dict[int, float]:
        """Sorted chapter to similarity from highest to lowest score"""
        chapter_to_similarity = {
            chapter.number: chapter.compute_sim(text) for chapter in self.chapters
        }
        return sort_dict(chapter_to_similarity, by="value")


@dataclass
class Bible:
    version: str
    language: str
    BASE_URL: ClassVar[str] = "https://getbible.net/json"

    def __post_init__(self):
        self._books: Dict[str, Book] = {}
        index_name = self.version
        if self.version in BIBLE_INDEX:
            self._books = BIBLE_INDEX[self.version]
            return
        # Retrieving from BASE_URL and populate books
        # BOOKS = ['genesis', 'psalms']
        print(f"Downloading bible version: {self.version}...")
        for book in BOOKS:
            chapter_to_verse: Dict = Bible.retrieve_chapter_to_verse(
                book, version=self.version
            )
            self.populate_book(book, chapter_to_verse)
            BIBLE_INDEX[index_name] = self._books
        print(f"Cleaning text....")
        self.clean_text()

    def book(self, name: str) -> Book:
        if name not in self._books:
            book = Book(name=name, language=self.language)
            self._books[name] = book
        return self._books[name]

    @property
    def books(self) -> List[Book]:
        return list(self._books.values())

    def total_chapter(self) -> int:
        return sum(book.num_chapter for book in self._books.values())

    @staticmethod
    def retrieve_chapter_to_verse(book, **kwargs) -> Dict:
        """
        Retrieve book from API url (BASE_URL)
        :param book: name of the book, e.g psalms
        :param kwargs: parameters passed to the URL
        :return: a dictionary of chapter to verses
        """

        params = dict(p=book, **kwargs)
        resp = requests.get(url=Bible.BASE_URL, params=params)
        # The first character to skip is '(' and the last two characters ');'
        clean_text = resp.text[1:-2]
        # NULL parsed as a single 'U'
        if clean_text == "U":
            raise BibleNotFound(f"NULL result. PARAMS={params}.")
        try:
            book_to_chapter: Dict = json.loads(clean_text)["book"]
        except KeyError:
            raise BibleNotFound(f"Error Book loaded. PARAMS={params}")
        else:
            return book_to_chapter

    def populate_book(self, book: str, chapter_to_verse: Dict) -> None:
        """
        Given a book's name, e.g psalms it fills the chapter
        :param book: name of the book, e.g psalms
        :param chapter_to_verse: dictionary, chapter as its key and verse as it values
        :return: None
        """
        for chapter_num, chapter_to_verse in chapter_to_verse.items():
            verse_to_text = chapter_to_verse["chapter"]
            for verse_num, verse_to_text in verse_to_text.items():
                verse_text = verse_to_text["verse"].strip()
                verse = Verse(int(verse_num), verse_text, self.language)
                self.book(book).chapter(int(chapter_num)).add_verse(verse)

    # @staticmethod
    # def clean_textbook(book: Book):
    #     book.clean_text()
    #     for chapter in book.chapters:
    #         chapter.clean_text()
    #         for verse in chapter.verses:
    #             verse.clean_text()

    def clean_text(self):
        for book in self.books:
            book.clean_text()
            for chapter in book.chapters:
                chapter.clean_text()
                for verse in chapter.verses:
                    verse.clean_text()

        # pool = Pool()
        # pool.map(Bible.clean_textbook, self.books)
        # pool.close()
        # pool.join()

    @staticmethod
    def compute_book_to_similarity(book: Book, text: str) -> Dict[BookName, SimRatio]:
        chapter_to_similarity = book.chapter_to_similarity(text)
        chapter_ratios = list(chapter_to_similarity.values())
        top_chapter_ratio = chapter_ratios[0]
        # Every book is represented by the highest chapter ratio's
        return {book.name: top_chapter_ratio}

    @SEARCH_CACHE.memoize()
    def book_to_similarity(self, text: str) -> Dict[BookName, SimRatio]:

        # book_to_similarity = {}
        # for book in self.books:
        #     chapter_to_similarity = book.chapter_to_similarity(text)
        #     stats_chapter_similarity = list(chapter_to_similarity.values())[0]
        #     book_to_similarity[book.name] = stats_chapter_similarity

        compute_text = partial(Bible.compute_book_to_similarity, text=text)
        with Pool() as pool:
            res: List[Dict[BookName, SimRatio]] = pool.map(compute_text, self.books)

        book_to_similarity = dict(ChainMap(*res))
        normalized_book_to_similarity = normalize(
            sort_dict(book_to_similarity, by="value")
        )
        # Filtered book with similarity score greater than 0.0
        filtered_book_to_similarity = {
            b: r for b, r in normalized_book_to_similarity.items() if r > 0.0
        }
        return filtered_book_to_similarity
