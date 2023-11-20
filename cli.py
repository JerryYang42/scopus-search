import argparse
from concurrent.futures import ThreadPoolExecutor

from DBClient import SearchEngine
from AuthorFinderApp import AuthorFinderApp
import csv
from typing import List

def run_cli():
    parser = argparse.ArgumentParser(
        prog='Find Authors for Special Issue',
        description='This app will try to generate '\
            'a qualified boolean string or keywords '\
            'based on the info list on the landing '\
            'page given. Use -u, --url to run once. '\
            'Use -c, --csv to run in batch.')

    parser.add_argument(
        '-u', '--url', type=str, 
        help='landing page url')

    parser.add_argument(
        '-s', '--search-engine', dest='search_engine', type=str, 
        choices=['boolean', 'vector'], 
        default='boolean', 
        help='specify which scopus search api you would like to use: '\
            '[1] "boolean" for sending Boolean String Query to '\
            'Boolean Search Engine. '\
            '[2] "vector" for sending keywords as in natural '\
            'language to Vector Embeddings Search Engine')
    
    parser.add_argument(
        '-c', '--csv', dest='csv_filepath', type=str,
        help='if you want to process multiple urls, '\
            'input a csv filepath that contains only one column, '\
            'which are urls. No column title needed.')
    
    parser.add_argument(
        '-n', '--n-top-entries', dest='n_top_entries', type=int, default=20_000,
        help='specify how many entries you want to retrieve. '\
            "It's only available under Boolean Search. "\
            'If larger than the total results, will return all results. '\
            'Under Vector Search, this argument will be ignored. '\
            'Default 500 for each search engine')
    
    parser.add_argument(
        '-a', '--ask-before-retrieval', 
        action="store_true", 
        help='only available when url argument is given, i.e. when run once, '\
            'and when using Boolean Search. '\
            'It will ask the user if they want to proceed with the generated query.'\
            'Default false')
    
    parser.add_argument(
        '-q', '--quiet', action="store_true", 
        help='mute info'
    )

    args = None
    try:
        args = parser.parse_args()
    except argparse.ArgumentTypeError as e:
        raise ValueError(f"Invalid argument: {e}")
    
    if (args.csv_filepath is None) and (args.url is None):
        raise ValueError(f"Missing argument url or csv filepath.")
    
    if (args.csv_filepath is not  None) and (args.url is not None):
        raise ValueError(f"Specified both url and csv filepath. '\
                         'Please only use one option.")

    search_engine: SearchEngine = None
    if args.search_engine == 'boolean':
        search_engine = SearchEngine.BooleanSearch
    elif args.search_engine == 'vector':
        search_engine = SearchEngine.VectorSearch
    else:
        print(f"Invalid search engine: {args.search_engine}. '\
               'It should be 'boolean' or 'vector'")
        exit(1)

    
    if args.csv_filepath is not None:
        urls = _get_urls_from_csv(filepath=args.csv_filepath)
        app = AuthorFinderApp()

        def _run_app(url, search_engine, n_top_entries, ask_before_retrieval, quiet):
            try: 
                app.start(landing_page_url=url, 
                        use=search_engine, 
                        n_top_entries=n_top_entries, 
                        ask_before_retrieval=ask_before_retrieval,
                        quiet=quiet )
            except Exception as e:
                print(e)

        with ThreadPoolExecutor(max_workers=6) as executor:
            futures = [executor.submit(_run_app, url, search_engine, args.n_top_entries, args.ask_before_retrieval, args.quiet) for url in urls]
            processed_queries = []
            for future in futures:
                result = future.result()
                if result:
                    processed_queries.append(result)
                    print(f"processed: {len(processed_queries)}/{len(urls)}")
        

    if args.url is not None:
        app = AuthorFinderApp()
        try: 
            app.start(landing_page_url=args.url, 
                    use=search_engine, 
                    n_top_entries=args.n_top_entries, 
                    ask_before_retrieval=args.ask_before_retrieval,
                    quiet=args.quiet)
        except Exception as e:
            print(e)


def _get_urls_from_csv(filepath: str) -> List[str]:
    with open(filepath, newline='') as csvfile:
        reader = csv.reader(csvfile)
        try:
            reader.line_num > 0
        except Exception as e:
            print(f"error loading csv file {filepath}")
        
        urls = [row[0] for row in reader]
        return urls


if __name__ == '__main__':
    # print(_get_urls_from_csv("input/test_urls.csv"))
    run_cli()

