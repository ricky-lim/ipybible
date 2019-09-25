import ipywidgets as widgets  # type: ignore
import numpy as np  # type: ignore
import matplotlib.pyplot as plt  # type: ignore
import hashlib  # type: ignore

from pathlib import Path
from PIL import Image  # type: ignore
from wordcloud import ImageColorGenerator, WordCloud  # type: ignore
from diskcache import Index  # type: ignore

from ipybible import IMG_DATA_DIR

LOVE_MASK_IMG = IMG_DATA_DIR / "love.png"
CLOUD_INDEX = Index()


def hash_txt(text: str) -> str:
    hash_object = hashlib.sha256(text.encode("utf-8"))
    hex_dig = hash_object.hexdigest()
    return hex_dig


def generate_cloud(text: str, mask_img: Path = LOVE_MASK_IMG):
    hashed_text = hash_txt(text)
    out = widgets.Output()
    mask = np.array(Image.open(mask_img))
    with out:
        if hashed_text in CLOUD_INDEX:
            wordcloud_bible = CLOUD_INDEX[hashed_text]
        else:
            wordcloud_bible = WordCloud(
                # stopwords=set(STOPWORDS),
                background_color=None,
                mode="RGBA",
                max_words=1000,
                mask=mask,
            ).generate(text)
            CLOUD_INDEX[hashed_text] = wordcloud_bible
        image_colors = ImageColorGenerator(mask)
        plt.figure(figsize=[15, 15])
        plt.imshow(
            wordcloud_bible.recolor(color_func=image_colors), interpolation="bilinear"
        )
        plt.axis("off")
        plt.show()
        return out
