# -*- coding: utf-8 -*-
from pathlib import Path

"""Top-level package for kilana_admin."""

__author__ = """Ricky Lim"""
__email__ = "rlim.email@gmail.com"
__version__ = "0.1.0"
BIBLE_DATA_DIR = Path(__file__).parent / "data" / "bible"
IMG_DATA_DIR = Path(__file__).parent / "data" / "img"
SEARCH_DATA_DIR = Path(__file__).parent / "data" / "search"
Path(BIBLE_DATA_DIR).mkdir(parents=True, exist_ok=True)
Path(IMG_DATA_DIR).mkdir(parents=True, exist_ok=True)
Path(SEARCH_DATA_DIR).mkdir(parents=True, exist_ok=True)
