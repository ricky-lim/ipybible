from typing import Dict, List, Tuple
from collections import OrderedDict
from math import fsum


def count_words(phrase: str) -> int:
    return len([word for word in phrase.split()])


def normalize(d: Dict[str, float]) -> Dict[str, float]:
    """
    Normalize dictionary values to 1
    :param d: dictionary with values of floats
    :return: a dictionary with normalized values
    """

    # Just to avoid exhaustive iterator
    if iter(d.values()) is iter(d.values()):
        raise TypeError("Values of input dictionary must be a container")

    ratios = list(d.values())
    total = fsum(ratios)
    if total == 0 or len(ratios) < 10:
        return d
    return {k: float("{0:.3f}".format(v / fsum(d.values()))) for k, v in d.items()}


def sort_dict(d: Dict, by: str, reverse=True) -> Dict:
    """
    Sort dictionary by either key (0) or value(1)
    :param d: input dictionary
    :param by: either key or value
    :param reverse: from high to low, default to True
    :return: sorted dictionary, default from high to low
    """
    by_to_pos = {"key": 0, "value": 1}
    by_pos = by_to_pos[by]

    sorted_res: List[Tuple[str, float]] = sorted(
        d.items(), key=lambda kv: kv[by_pos], reverse=reverse
    )
    return OrderedDict(sorted_res)
