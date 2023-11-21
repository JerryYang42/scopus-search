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
python cli.py -c "input/test_urls.csv" -s boolean -n 20000
python cli.py -c "input/test_urls.csv" -s vector -n 500
zip -r "20k-boolean-500-vector-batch-1.zip" output
rm -r output
mkdir output

python cli.py -c "input/test_urls.csv" -s boolean -n 20000
python cli.py -c "input/test_urls.csv" -s vector -n 500
zip -r "20k-boolean-500-vector-batch-2.zip" output
rm -r output
mkdir output

python cli.py -c "input/test_urls.csv" -s boolean -n 20000
python cli.py -c "input/test_urls.csv" -s vector -n 500
zip -r "20k-boolean-500-vector-batch-3.zip" output
rm -r output
mkdir output

python cli.py -c "input/test_urls.csv" -s boolean -n 20000
python cli.py -c "input/test_urls.csv" -s vector -n 500
zip -r "20k-boolean-500-vector-batch-4.zip" output
rm -r output
mkdir output

python cli.py -c "input/test_urls.csv" -s boolean -n 20000
python cli.py -c "input/test_urls.csv" -s vector -n 500
zip -r "20k-boolean-500-vector-batch-5.zip" output
rm -r output
mkdir output
deactivate
