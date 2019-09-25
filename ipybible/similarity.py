import numpy as np  # type: ignore
import spacy  # type: ignore

from typing import List
from spacy.tokens.doc import Doc  # type: ignore
from sklearn.feature_extraction.text import CountVectorizer  # type: ignore
from sklearn.metrics.pairwise import cosine_similarity  # type: ignore
from diskcache import Cache, Index  # type: ignore
from dataclasses import dataclass
from hashlib import sha256

from ipybible import BIBLE_DATA_DIR

SIM_CACHE: Cache = Cache()
BIBLE_INDEX = Index(str(BIBLE_DATA_DIR))


@dataclass
class SpacyLangModel:
    nlp: spacy
    stop_words: List[str]


def normalize_text(
        text: str, spacy_model: SpacyLangModel, index_name: Index = BIBLE_INDEX
):
    index_key = sha256(text.encode("utf-8")).hexdigest()
    if index_key in index_name:
        return BIBLE_INDEX[index_key]
    else:
        doc: Doc = spacy_model.nlp(text.lower())
        lemma_words: List[str] = []
        for token in doc:
            if token.is_punct or token.is_stop:
                continue
            lemma = token.lemma_.strip()
            if "-PRON-" not in lemma:
                lemma_words.append(lemma)
        clean_text = " ".join(lemma_words)
        BIBLE_INDEX[index_key] = clean_text
        return clean_text


def cosine_sim(str_a: str, str_b: str) -> float:
    """
    Compute cosine similarity between two strings
    :param str_a: first string (text)
    :param str_b: second string (text)
    :return: a similarity ratio
    """
    str_a, str_b = str_a.lower(), str_b.lower()
    vectors = [t for t in vectorize(str_a, str_b)]
    return float(cosine_similarity(vectors)[0, 1])


def vectorize(*strs: str) -> np.array:
    """
    Returns an numpy array, given string arguments
    :param strs: string arguments
    :return: numpy array of strings
    """
    text: List[str] = [t for t in strs]
    vectorizer = CountVectorizer(ngram_range=(2, 3))
    return vectorizer.fit_transform(text).toarray()
