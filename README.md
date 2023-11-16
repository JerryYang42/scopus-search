# Scopus Search

## Python scripts

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