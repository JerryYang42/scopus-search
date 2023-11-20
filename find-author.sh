#!/bin/bash

# get into local python virtual env
source venv/bin/activate

# run the app with list of urls as input
# python cli.py -u "https://www.sciencedirect.com/journal/journal-of-taibah-university-medical-sciences/about/forthcoming-special-issues#health-sector-transformation-in-saudi-arabia" -s boolean

# run the app with 20 top entries, ask before retrieval under single run mode
# python cli.py -u "https://www.sciencedirect.com/journal/journal-of-taibah-university-medical-sciences/about/forthcoming-special-issues#health-sector-transformation-in-saudi-arabia" -s boolean -n 20 -a -q

# run this in vector search
# python cli.py -u "https://www.sciencedirect.com/journal/journal-of-taibah-university-medical-sciences/about/forthcoming-special-issues#health-sector-transformation-in-saudi-arabia" -s vector -n 20 -a

# run app in batch
python cli.py -c "input/test_urls.csv" -s boolean -n 20

deactivate
