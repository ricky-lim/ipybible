import click
import json

from pathlib import Path

from ipybible.extraction import IBook
from ipybible.books import BOOKS


@click.group()
def main():
    pass


@main.command()
@click.option(
    "--out", help="output directory path", type=Path, default=Path.cwd, required=False
)
def get_bible(out):
    """
    Get Bible in json format
    :param out:
    :return:
    """
    for book in BOOKS:
        book_chapters = IBook(book).chapter_to_text(version="basicenglish")
        with open(Path(out) / f"{book}.json", "w") as out_json:
            json.dump(book_chapters, out_json)
