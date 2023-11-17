import pandas as pd


class VectorSearchClient():

    ENDPOINT = ""

    def num_results_from(self, keywords: str) -> int:
        pass

    def retrieve_all_authors(self, keywords: str) -> pd.DataFrame:
        pass

    def try_limit_to_recent(self):
        pass

    def try_loosen_time_limit(self):
        pass



##############################################################
# TEST
##############################################################

if __name__ == "__main__":
    vectorSearchClient = VectorSearchClient()
