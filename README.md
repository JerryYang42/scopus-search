# Scopus Search

## Installation 

### How to install locally

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

### secrets

For secrets sharing, we naively use a file `ProjectSecrets.py` to hold all the secrets. Please never force push it to the git repo. If you want it, reach to us.

### additional models

Run this to install pre-trained language model `en_core_web_md` for word convertion

```zsh
python -m spacy download en_core_web_md
```

If you encountered `CERTIFICATE_VERIFY_FAILED` ERROR, dont' panic. Walk around by following two steps.

```zsh
wget https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-2.2.5/en_core_web_sm-2.2.5.tar.gz
wget https://github.com/explosion/spacy-models/releases/download/en_core_web_md-3.7.0/en_core_web_md-3.7.0-py3-none-any.whl

python -m pip install ./en_core_web_md-3.7.0-py3-none-any.whl
```

### additional csv files

Please put `examples_for_hackathon.xlsx` under the project's `resource/` folder to retrive the sample data to conversation with ChatGPT.

### Mongo DB

Read [Get Started with Atlas](https://www.mongodb.com/docs/atlas/getting-started/) for more information.

Local Deployments
[Create a local deployment](https://www.mongodb.com/docs/atlas/cli/stable/atlas-cli-deploy-local/)
 to try Atlas features on a single-node replica set hosted on your local computer.

```
brew install mongodb-atlas-cli
brew install mongosh
brew install mongodb-compass
brew install mongodb-database-tools
```

```
mongodb-atlas-cli 1.13.0 is already installed and up-to-date
mongosh 2.0.2 is already installed and up-to-date
podman 4.7.2 is already installed and up-to-date
Not upgrading mongodb-compass, the latest version is already installed
```

## About Boolean Search 
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