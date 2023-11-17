import sqlite3 as sl
from enum import Enum
from dataclasses import dataclass
from typing import Iterable, List, Dict, Any, Tuple
from datetime import datetime
import pandas as pd
from sqlalchemy import Integer, String, Date, DateTime

class QueryStatus(str, Enum):
    accepted = 'accepted'
    rejected = 'rejected'
    improved = 'improved'

class QuerySource(str, Enum):
    chatGPT = 'chatGPT'
    booleanSearch = 'booleanSearch'
    vectorSearch = 'vectorSearch'

@dataclass
class Author:
    auid: str
    firstname: str
    lastname: str

@dataclass
class AuthorQuery:
    auid: str
    qid: int

@dataclass
class BooleanQuery:
    qid: int
    query: str
    source: QuerySource
    status: QueryStatus
    n_results: int
    n_authors: List[Author]
    start_year: int
    end_year: int
    timestamp: datetime

class DBClient:
    """
    sqlite tutorial:  https://www.tutorialspoint.com/sqlite/sqlite_using_autoincrement.htm#:~:text=SQLite%20AUTOINCREMENT%20is%20a%20keyword,used%20with%20INTEGER%20field%20only.
    Dataframe.to_sql: https://pandas.pydata.org/pandas-docs/stable/user_guide/io.html#io-sql
    SOMEHOW the singleton doesnot work. try only use one client and pass it around everywhere :(
    """
    def __init__(self, db_path="boolean-search-history.db"):
        self.conn = None
        try:
            self.conn = sl.connect(db_path)
        except Exception as e:
            print(e)
        
        self._create_tables()
    
    def add_boolean_string(self, query: str, source: QuerySource, status: QueryStatus=QueryStatus.rejected) -> int:
        """
        append boolean string to the table and return its qid
        """
        cursor = self.conn.cursor()
        QUERY = f"""
            INSERT INTO boolean_query (query, source, status, timestamp)
            VALUES ('{query}', '{source}', '{status}', datetime('now'));
        """
        cursor.execute(QUERY)
        self.conn.commit()
    
    def get_latest_qid(self, query: str) -> int:
        """
        if many, return the latest one
        """
        cursor = self.conn.cursor()
        QUERY = f"""
            SELECT qid
            FROM boolean_query
            WHERE query = '{query}'
            ORDER BY qid DESC;
        """
        cursor.execute(QUERY)
        row = cursor.fetchone()
        if (row is None) or (len(row) == 0):
            return 0
        qid = row[0]
        return qid
    
    def get_accepted_qid(self, query: str) -> int:
        """
        if many, return the latest one
        """
        cursor = self.conn.cursor()
        QUERY = f"""
            SELECT qid
            FROM boolean_query
            WHERE query = '{query}' AND status = '{QueryStatus.accepted}'
            ORDER BY qid DESC;
        """
        cursor.execute(QUERY)
        row = cursor.fetchone()
        if (row is None) or (len(row) == 0):
            raise ValueError('there should be at least one accepted query in the db')
        qid = row[0]
        return qid
    
    def exists_query(self, query: str) -> int:
        return self.get_latest_qid(query) > 0

    def update_query_status(self, query: str, to_status: QueryStatus) -> bool:
        qid = self.get_latest_qid(query)
        cursor = self.conn.cursor()
        QUERY = f"""
            UPDATE boolean_query
            SET status = '{to_status}'
            WHERE qid = {qid};
        """
        cursor.execute(QUERY)
        return True

    def update_verdict_of_boolean_string(self, query: str, status: QueryStatus) -> None:
        cursor = self.conn.cursor()
        QUERY = f"""
        UPDATE boolean_query SET status = '{status}' 
        WHERE query = '{query}';
        """
        cursor.execute(QUERY)
        self.conn.commit()

    def display_table(self, table_name: str):
        cursor = self.conn.cursor()
        QUERY = f"""
        SELECT * FROM {table_name};
        """
        cursor.execute(QUERY)
        records = cursor.fetchall()
        return records

    def _add_author(self, author: Author) -> bool:
        """
        add author to author table. Return True if done
        """
        if self._author_exists(author.auid):
            return True
        
        cursor = self.conn.cursor()
        QUERY = f"""
        INSERT INTO author (auid, firstname, surname)
        VALUES ('{author.auid}', '{author.firstname}', '{author.lastname}');
        """
        cursor.execute(QUERY)
        self.conn.commit()
        return True

    def _author_exists(self, auid: str) -> bool:
        cursor = self.conn.cursor()
        QUERY = f"""
            SELECT COUNT(*) FROM author WHERE auid = '{auid}';
        """
        cursor.execute(QUERY)
        row = cursor.fetchone()
        cnt = row[0]
        return cnt == 1

    def read_authors(self, query: str) -> pd.DataFrame: 
        qid = self.get_latest_qid(query)
        QUERY = f"""
            SELECT a.auid, a.firstname, a.surname
            FROM boolean_query AS q
            LEFT OUTER JOIN queries_papers AS qp ON q.qid = qp.qid
            LEFT OUTER JOIN papers_authors AS pa ON qp.eid = pa.eid
            LEFT OUTER JOIN author AS a ON pa.auid = a.auid
            WHERE q.query='{query}'
        """
        df_authors = pd.read_sql_query(QUERY, con=self.conn)
        return df_authors

    # def get_authors_given_query(self, query: str | BooleanQuery) -> List[Author]:
    #     query_text = query.query if isinstance(query, BooleanQuery) else query
    #     qid = self.get_qid(query_text)
        
    #     cursor = self.conn.cursor()
    #     QUERY = f"""
    #     SELECT aq.auid, a.firstname, a.surname
    #     FROM author_query AS aq
    #     LEFT OUTER JOIN author AS a
    #     ON aq.auid = a.auid
    #     WHERE aq.qid = {qid};
    #     """
    #     cursor.execute(QUERY)
    #     authors = cursor.fetchall()
    #     return authors

    def add_entries(self, qid: int, entries: List[Dict[Any, Any]]) -> bool:
        # papers table
        df_papers = self._entries_2_papers(entries)
        df_papers.to_sql(name="paper", con=self.conn, if_exists='replace', index=False, dtype={
            'eid': 'String',
            'citedby_count': 'Integer',
            'cover_date': 'Date',
            'title': 'String',
            'abstract': 'String'
        })
        # queries_papers table
        df_queries_papers = df_papers[['eid']].copy()
        df_queries_papers['qid'] = qid
        df_queries_papers.to_sql(name="queries_papers", con=self.conn, if_exists='replace', index=False, dtype={
                'eid': 'String',
                'qid': 'Integer'
            })

        for entry in entries:
            # authors table
            df_authors = self._entry_2_authors(entry)
            df_authors.to_sql(name="author", con=self.conn, if_exists='replace', index=False, dtype={
                'auid': 'String',
                'firstname': 'String',
                'surname': 'String'
            })

            # papers_authors table
            eid = entry['eid']
            df_papers_authors = df_authors[['auid']].copy()
            df_papers_authors['eid'] = eid
            df_papers_authors.to_sql(name="papers_authors", con=self.conn, if_exists='replace', index=False, dtype={
                'eid': 'String',
                'auid': 'String'
            })

    def _entries_2_papers(self, entries: List[Dict[Any, Any]]) -> pd.DataFrame:
        # ALL_COLUMNS = [ 'dc:title', 'prism:volume','prism:issueIdentifier','article-number', 
        #                 'citedby-count', 'prism:doi', 'subtypeDescription', 'eid', 
        #                 'prism:pageRange', 'prism:coverDate', 'prism:publicationName', 'dc:description', 
        #                 'freetoreadLabel', 'link'] ]

        df = pd.DataFrame(entries)
        df_papers = df[[
            'eid',
            'citedby-count', 
            'prism:coverDate', 
            'dc:title', 
            'dc:description']]
        
        df_papers.rename(columns={
            'citedby-count':'citedby_count', 
            'prism:coverDate': 'cover_date', 
            'dc:title': 'title',
            'dc:description':'abstract'
            }, inplace=True)

        df_papers['cover_date'] = pd.to_datetime(df_papers['cover_date'])
        
        return df_papers

    # demo of how to insert df rows iteratively
    # def _insert_df_row_by_row(self, table_name: str, columns: Iterable[str], df: pd.DataFrame) -> bool:
    #     for row in df.itertuples():
    #         insert_sql = f"""
    #             INSERT INTO {table_name} ({ ", ".join(columns)})
    #             VALUES ({row[0]}, '{row[1]}')
    #         """
    #     return True

    def _entry_2_authors(self, entry: Dict[Any, Any]) -> pd.DataFrame:
        # COLUMNS = ['@_fa', '@seq', 'author-url', 'auid', 'authname', 'surname', 'firstname', 'initials', 'afid']
        
        authors = entry.get('author', [])

        df_authors = pd.DataFrame(authors)
        
        df_authors = df_authors[['authid', 'given-name', 'surname']]
        df_authors.rename(columns={ 
            'given-name': 'firstname', 
            'authid': 'auid'
            }, inplace=True)
        
        return df_authors



    def _create_tables(self):
        cursor = self.conn.cursor()
        QUERY_CREATE_TABLES = [
            """
            CREATE TABLE IF NOT EXISTS boolean_query (
                qid INTEGER PRIMARY KEY AUTOINCREMENT,
                query TEXT UNIQUE,
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
                citedby_count INTEGER NOT NULL,
                cover_date DATE NOT NULL,
                title TEXT,
                abstract TEXT
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS queries_papers (
                qid INTEGER NOT NULL,
                eid TEXT NOT NULL,
                FOREIGN KEY (qid) REFERENCES boolean_query(qid),
                FOREIGN KEY (eid) REFERENCES papers(eid),
                PRIMARY KEY (qid, eid)
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
            CREATE TABLE IF NOT EXISTS papers_authors (
                eid TEXT NOT NULL,
                auid TEXT NOT NULL,
                FOREIGN KEY (eid) REFERENCES papers(eid),
                FOREIGN KEY (auid) REFERENCES authors(auid),
                PRIMARY KEY (eid, auid)
            );
            """
        ]
        for query in QUERY_CREATE_TABLES:
            cursor.execute(query)


##################################################
# TEST
##################################################

if __name__ == "__main__":
    dbClient = DBClient()
    # dbClient.add_boolean_string("test Boolean string3", QuerySource.chatGPT, QueryStatus.rejected)
    # records = dbClient.display_table('boolean_query')
    # print(records)
    # qid = dbClient.get_qid("test Boolean string")
    # print(qid)
    # qid = dbClient.get_qid("this string does not exsit in db")
    # assert qid == 0

    # should report error - query text should be unique
    # dbClient.add_boolean_string("test Boolean string", QuerySource.chatGPT, QueryStatus.rejected)
    # dbClient.update_verdict_of_boolean_string("test Boolean string", QueryStatus.accepted)

    # should add author
    # author = Author(auid="1234567", firstname="firstname", lastname="lastname")
    # success = dbClient.add_author_query(author, "test Boolean string")
    # assert success

    records = dbClient.display_table('author')
    print(records)
    # auhtor2 = Author("6787656787", firstname="firstname2", lastname="lastname2")
    # dbClient.add_author_query(auhtor2, "test Boolean string")
    all_authors = dbClient.get_authors_given_query("test Boolean string")
    print(all_authors)

