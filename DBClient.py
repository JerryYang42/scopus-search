import sqlite3 as sl
from enum import Enum

class DBClient():
    """
    A singleton that keep records of each boolean string search.
    reference:
    https://www.digitalocean.com/community/tutorials/how-to-use-the-sqlite3-module-in-python-3

    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DBClient, cls).__new__(cls)
            # Put any initialization here.
        return cls._instance
    
    def __init__(self, db_path="boolean-search-history.db"):
        self.conn = sl.connect(db_path)
        
        self._create_tables()
    
    def _create_tables(self):
        cursor = self.conn.cursor()
        QUERY_CREATE_TABLES = [
            """
            CREATE TABLE IF NOT EXISTS boolean_query (
                qid INTEGER AUTO_INCREMENT,
                query TEXT PRIMARY KEY,
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

    
class QueryStatus(str, Enum):
    accepted = 'accepted'
    rejected = 'rejected'
    improved = 'improved'

class QuerySource(str, Enum):
    chatGPT = 'chatGPT'
    booleanSearch = 'booleanSearch'
    vectorSearch = 'vectorSearch'
