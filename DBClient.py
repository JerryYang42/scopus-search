import sqlite3 as sl
from enum import Enum


class QueryStatus(str, Enum):
    accepted = 'accepted'
    rejected = 'rejected'
    improved = 'improved'

class QuerySource(str, Enum):
    chatGPT = 'chatGPT'
    booleanSearch = 'booleanSearch'
    vectorSearch = 'vectorSearch'


class DBClient():
    """
    https://www.digitalocean.com/community/tutorials/how-to-use-the-sqlite3-module-in-python-3
    SOMEHOW the singleton doesnot work. try only use one client and pass it around everywhere :(
    """
    def __init__(self, db_path="boolean-search-history.db"):
        self.conn = None
        try:
            self.conn = sl.connect(db_path)
        except Exception as e:
            print(e)
        
        self._create_tables()
    
    def add_boolean_string(self, query: str, source: QuerySource, status: QueryStatus=QueryStatus.rejected) -> None:
        cursor = self.conn.cursor()
        QUERY = f"""
        INSERT INTO boolean_query (query, source, status)
        VALUES ('{query}', '{source}', '{status}');
        """
        cursor.execute(QUERY)
        self.conn.commit()

    # def show_boolean_string(self) -> None:
    #     cursor = self.conn.cursor()
    #     QUERY = """
    #     SELECT * FROM boolean_query;
    #     """
    #     cursor.execute(QUERY)
    #     self.conn.commit()

    def _create_tables(self):
        cursor = self.conn.cursor()
        QUERY_CREATE_TABLES = [
            """
            CREATE TABLE IF NOT EXISTS boolean_query (
                qid INTEGER PRIMARY KEY AUTOINCREMENT,
                query TEXT,
                source TEXT,
                status TEXT,
                n_results INTEGER,
                n_authors INTEGER,
                start_year YEAR,
                end_year YEAR,
                timestamp TIMESTAMP
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS improvement (
                old_query INTEGER NOT NULL,
                new_query INTEGER NOT NULL,
                improved_by TEXT NOT NULL,
                note TEXT NOT NULL,
                FOREIGN KEY (old_query) REFERENCES boolean_query(qid),
                FOREIGN KEY (new_query) REFERENCES boolean_query(qid)
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS paper (
                eid TEXT PRIMARY KEY,
                issn TEXT,
                citation INTEGER NOT NULL,
                cover_date DATE NOT NULL,
                title TEXT,
                keywords TEXT,
                abstract TEXT,
                citedby_count INTEGER,
                author_count INTEGER
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS paper_query (
                eid TEXT NOT NULL,
                qid INTEGER NOT NULL,
                FOREIGN KEY (eid) REFERENCES papers(eid),
                FOREIGN KEY (qid) REFERENCES boolean_query(qid)
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS author (
                auid TEXT PRIMARY KEY,
                firstname TEXT NOT NULL,
                surname TEXT NOT NULL
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS author_query (
                auid TEXT PRIMARY KEY,
                qid INT NOT NULL,
                FOREIGN KEY (auid) REFERENCES authors(auid),
                FOREIGN KEY (qid) REFERENCES boolean_query(qid)
            );
            """
        ]
        for query in QUERY_CREATE_TABLES:
            cursor.execute(query)


##################################################
# TEST
##################################################
dbClient = DBClient()
dbClient.add_boolean_string("test Boolean string", QuerySource.chatGPT, QueryStatus.rejected)
dbClient.show_boolean_string()
