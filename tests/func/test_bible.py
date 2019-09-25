import pytest

from ipybible.bible import Bible, BibleNotFound


@pytest.fixture
def bible_basic_english():
    yield Bible(version='basicenglish', language='EN')


def test_bible_basic_english(bible_basic_english):
    assert bible_basic_english.version == 'basicenglish'
    assert bible_basic_english.language == 'EN'


def test_bible_unknown():
    with pytest.raises(BibleNotFound):
        Bible(version='unknown', language='EN')


def test_bible_psalm(bible_basic_english):
    psalm = bible_basic_english.book('psalms')
    assert psalm.num_chapter == 150
    assert psalm.chapter(1).num_verse == 6


def test_bible_books(bible_basic_english):
    from ipybible.books import BOOKS
    for book in BOOKS:
        assert book in bible_basic_english._books.keys()


def test_bible_num_chapter(bible_basic_english):
    from ipybible.books import BOOK_TO_TOTAL_CHAPTER
    for book_name, expected_num_chapter in BOOK_TO_TOTAL_CHAPTER.items():
        assert bible_basic_english.book(book_name).num_chapter == expected_num_chapter
