#!/bin/bash

############################################################
# Help                                                     #
############################################################
# Help()
# {
#    # Display Help
#    echo "Add description of the script functions here."
#    echo
#    echo "Syntax: scriptTemplate [-g|h|v|V]"
#    echo "options:"
#    echo "g     Print the GPL license notification."
#    echo "h     Print this Help."
#    echo "v     Verbose mode."
#    echo "V     Print software version and exit."
#    echo
# }

# take 1 input - landing page url
set landing_page_url=$1
# fix the seed of hash function so that every hash of a string is reproducible between runs
export PYTHONHASHSEED=0
# get into local python virtual env
source venv/bin/activate
# run the app with input
# python cli.py -u "https://www.sciencedirect.com/journal/journal-of-taibah-university-medical-sciences/about/forthcoming-special-issues#health-sector-transformation-in-saudi-arabia" -s boolean

deactivate
