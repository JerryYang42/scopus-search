# Scopus Search

## How to install locally

You need python 3.10

Use venv to create a local environment call `venv` (the second `venv`)

```zsh
python -m venv venv
```

Acticate the virtual env by 

```zsh
source venv/bin/activate
```

After this, you will expected to see `(venv)` showing up in your command prompt.

With it activated, pip install libraries from `requirements.txt`

```zsh
pip install -r requirements.txt --trusted-host files.pythonhosted.org --trusted-host pypi.org --trusted-host pypi.python.org --default-timeout=1000
```

Congratulations. You're all set!

Well, if you want to exit the virtual env. Type

```zsh
deactivate
```


### About Boolean Search 
Example of api call

```bash
curl --location --request POST 'https://shared-search-service-api.cert.scopussearch.net/sharedsearch/document/result' \
--header 'X-ELS-product: Hackathon' \
--header 'X-ELS-diagnostics: true' \
--header 'Content-Type: application/json' \
--header 'X-ELS-dataset: abstract' \
--data-raw '{"query": { "queryString": "allsmall:(water on mars)"},
    "returnFields": ["eid", "authkeywords", "abs", "itemtitle","aucite"],  
    "resultSet": { "skip": 0, "amount": 30},
    "rankingModel": { "modelName": "abstract_default"},
    "filters": [ {"fieldName": "db", "terms": ["scopus","medl"],"operator": "IS ONE OF"}],
    "sortBy": [ {"fieldName": "relevance","order": "desc"}]
}'
```