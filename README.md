# ipybible

Interactive Python to explore bible. Please Check it out @https://ipybible.herokuapp.com/

Bible source API: https://getbible.net/api

## Installation

```bash
git clone https://github.com/ricky-lim/ipybible.git
cd ipybible
# create virtualenv
python -m venv ipybible-env
source ipybible-env/bin/activate
pip install -r requirements.txt
```

## Bible API
```python
from ipybible.bible import Bible  

# Bible instance, kjv is default to be loaded during installation
kjv_bible = Bible(version='kjv', language='EN')

# Explore text
kjv_bible.book('1 timothy').chapter(6).text 

# Download another bible version 
# Language is required for spacy model to clean the text
asv_bible = Bible(version='asv', language='EN')   
```

## Heroku deployment
```bash
git add 
git commit
git push heroku master
heroku open
```
 More details, please check out on [voila-heroku-deployment](https://voila.readthedocs.io/en/latest/deploy.html).

## Development
```bash

# activate virtualenv
source ipybible-env/bin/activate

# exploration
jupyter-notebook

# local-server
voila --template vuetify-default --enable_nbextensions=True notebooks/bible.ipynb 
```
