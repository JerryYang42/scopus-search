import json
from typing import Dict, Any, List
import os
import hashlib

from UserInputClient import UserResponse
from Config import Config


class BooleanStringJsonIO:

    def __init__(self) -> None:
        self.folder = Config.BOOLEAN_STRING_OUTPUT_FOLDER
        if not os.path.exists(self.folder):
            os.makedirs(self.folder)

    def write(self, boolean_string: str) -> None:
        data = {
            'query': boolean_string
        }
        filepath = self._filepath_from(boolean_string)
        with open(filepath, 'w') as fp:
            json.dump(data, fp)

    def set_is_invalid(self, boolean_string: str, is_invlid: bool) -> None:
        filepath = self._filepath_from(boolean_string)
        # if not os.path.exists(filepath):
        #     self.write(boolean_string)
        data = self.read(boolean_string)
        data['is_invalid'] = is_invlid
        with open(filepath, 'w') as fp:
            json.dump(data, fp)
    
    def set_user_response(self, boolean_string: str, user_response: UserResponse) -> None:
        filepath = self._filepath_from(boolean_string)
        # if not os.path.exists(filepath):
        #     self.write(boolean_string)
        data = self.read(boolean_string)
        data['user_response'] = {
            'accepted': user_response.accepted
        }
        with open(filepath, 'w') as fp:
            json.dump(data, fp)

    def set_total_results(self, boolean_string: str, total_results: int) -> None:
        filepath = self._filepath_from(boolean_string)
        # if not os.path.exists(filepath):
        #     self.write(boolean_string)
        data = self.read(boolean_string)
        data['total_results'] = total_results
        with open(filepath, 'w') as fp:
            json.dump(data, fp)

    def set_entries(self, boolean_string: str, entries: List[Any]) -> None:
        filepath = self._filepath_from(boolean_string)
        # if not os.path.exists(filepath):
        #     self.write(boolean_string)
        data = self.read(boolean_string)
        for entry in entries:
            if '_fa' in entry: del entry['@_fa']
            if 'link' in entry: del entry['link']
            if 'prism:url' in entry:
                entry['url'] = entry['prism:url']; del entry['prism:url']
            if 'dc:identifier' in entry: del entry['dc:identifier']
            if 'title' in entry:
                entry['title'] = entry['dc:title']; del entry['dc:title']
            if 'prism:publicationName' in entry: 
                del entry['prism:publicationName']
            if 'prism:eIssn' in entry: del entry['prism:eIssn']
            if 'prism:volume' in entry:
                del entry['prism:volume']
            if 'prism:issueIdentifier' in entry: del entry['prism:issueIdentifier']
            if 'prism:pageRange' in entry:
                del entry['prism:pageRange']
            if 'prism:coverDate' in entry:
                entry['cover_date'] = entry['prism:coverDate']; del entry['prism:coverDate']
            if 'prism:coverDisplayDate' in entry: del entry['prism:coverDisplayDate']
            if 'prism:doi' in entry: del entry['prism:doi']
            if 'dc:description' in entry:
                entry['abstract'] = entry['dc:description']; del entry['dc:description']
            if 'citedby-count' in entry: entry['citedby_count'] = entry['citedby-count']
            if 'affiliation' in entry: del entry['affiliation']
            if 'author' in entry:
                entry['authors'] = entry['author']; del entry['author']
                
                for author in entry['authors']:
                    if '@_fa' in author: del author['@_fa']
                    if '@seq' in author: del author['@seq']
                    if 'author-url' in author: author['author_url'] = author['author-url']; del author['author-url']
                    if 'authid' in author: author['auid'] = author['authid']; del author['authid']
                    if 'authname' in author: del author['authname']
                    if 'surname' in author: author['surname']
                    if 'given-name' in author:
                        author['firstname'] = author['given-name']; del author['given-name']
                    if 'initials' in author: del author['initials']
                    if 'afid' in author: del author['afid']
        data['entries'] = entries
        with open(filepath, 'w') as fp:
            json.dump(data, fp)

    def read(self, boolean_string: str, ) -> Dict[str, Any]:
        filepath = self._filepath_from(boolean_string)
        with open(filepath, 'r') as fp:
            data = json.load(fp)
            return data
        
    def get_is_invalid(self, boolean_string: str, is_invlid: bool) -> bool:
        data = self.read(boolean_string)
        if 'is_invalid' in data: 
            return data['is_invalid']
        if 'entries' in data:
            return False
        return False

    def get_user_response(self, boolean_string: str) -> UserResponse:
        data = self.read(boolean_string)
        return UserResponse(accepted=data['user_response'])

    def get_total_results(self, boolean_string: str) -> int:
        data = self.read(boolean_string)
        if 'total_results' in data:
            return data['total_results']
        if 'entries' in data:
            return len(data['entries'])
        return 0
    
    def get_entries(self, boolean_string: str) -> List[Any]:
        data = self.read(boolean_string)
        entries = data['entries']
        return entries
    
    def get_eids(self, boolean_string: str) -> List[str]:
        data = self.read(boolean_string)
        if 'entries' not in data: 
            return []
        entries = data['entries']
        eids = [entry.get('eid', None) for entry in entries]
        eids = [eid for eid in eids if eid is not None]
        return eids
    
    def get_auids(self, boolean_string: str) -> List[str]:
        data = self.read(boolean_string)
        if 'entries' not in data: 
            return []
        entries = data['entries']
        auids = []
        for entry in entries:
            if 'authors' not in entry:
                continue
            authors = entry['authors']
            auids.extend([author.get('auid', None) for author in authors])
        auids = [auid for auid in auids if auid is not None]
        return auids
    
    def _filepath_from(self, boolean_string: str) -> str:
        filename = self._filename_from(boolean_string)
        filepath = f"{self.folder}/{filename}"
        return filepath
    
    def _filename_from(self, boolean_string: str) -> str:
        # return f"{hash(boolean_string)}.json"
        m = hashlib.md5()
        m.update(boolean_string.encode('utf-8'))
        return str(m.hexdigest())[:12]

class VectorQueryJsonIO:
    def __init__(self) -> None:
        self.folder = Config.VECTOR_QUERY_OUTPUT_FOLDER
        if not os.path.exists(self.folder):
            os.makedirs(self.folder)

    def write(self, vector_query: str, entries: List[Any]) -> None:
        for entry in entries:
            entry['relevance']
            entry['eid']
            entry['abstract'] = entry['abs']; del entry['abs']
            entry['pub_year'] = entry['pubyr']; del entry['pubyr']
            if 'authors' in entry:
                authors = entry['authors']
                for author in authors:
                    if 'authid' in author:
                        author['auid'] = author["authid"]; del author["authid"]
        data = {
            'query': vector_query,
            'entries': entries
        }
        filepath = self._filepath_from(vector_query)
        with open(filepath, 'w') as fp:
            json.dump(data, fp)

    def read(self, vector_query: str, ) -> Dict[str, Any]:
        filepath = self._filepath_from(vector_query)
        with open(filepath, 'r') as fp:
            data = json.load(fp)
            return data

    def get_total_results(self, boolean_string: str) -> int:
        data = self.read(boolean_string)
        return len(data['entries'])

    def get_eids(self, vector_query: str) -> List[str]:
        data = self.read(vector_query)
        if 'entries' not in data: 
            return []
        entries = data['entries']
        eids = [entry.get('eid', None) for entry in entries]
        eids = [eid for eid in eids if eid is not None]
        return eids


    def get_auids(self, vector_query: str) -> List[str]:
        data = self.read(vector_query)
        if 'entries' not in data: 
            return []
        entries = data['entries']
        auids = []
        for entry in entries:
            if 'authors' not in entry:
                continue
            authors = entry['authors']
            auids.extend([author.get('auid', None) for author in authors])
        auids = [auid for auid in auids if auid is not None]
        return auids
    
    def get_abstracts(self, vector_query: str) -> List[str]:
        data = self.read(vector_query)
        if 'entries' not in data: 
            return []
        entries = data['entries']
        abstracts = [entry.get('abstract', None) for entry in entries]
        abstracts = [abstract for abstract in abstracts if abstract is not None]
        return abstracts

    def _filepath_from(self, vector_query: str) -> str:
        filename = self._filename_from(vector_query)
        filepath = f"{self.folder}/{filename}"
        return filepath
    
    def _filename_from(self, vector_query: str) -> str:
        # return f"{hash(boolean_string)}.json"
        m = hashlib.md5()
        m.update(vector_query.encode('utf-8'))
        return str(m.hexdigest())[:12]


##############################################################
# TEST
##############################################################

if __name__ == "__main__":
    boolean_string = '''( TITLE-ABS-KEY ( "plant-based" ) OR TITLE-ABS-KEY ( "animal analogues" ) OR TITLE-ABS-KEY ( "consumer acceptance" ) OR TITLE-ABS-KEY ( "flavour attributes" ) OR TITLE-ABS-KEY ( "health" ) OR TITLE-ABS-KEY ( "market growth" ) OR TITLE-ABS-KEY ( "nutrition" ) OR TITLE-ABS-KEY ( "product development" ) OR TITLE-ABS-KEY ( "product quality" ) OR TITLE-ABS-KEY ( "sensory attributes" ) OR TITLE-ABS-KEY ( "sustainable alternatives" ) OR TITLE-ABS-KEY ( "texture attributes" ) ) AND SUBJTERMS ( 1106 )'''
    boolean_string_json_io = BooleanStringJsonIO()
    boolean_string_json_io.write(boolean_string)
    boolean_string_json_io.set_user_response(boolean_string, user_response=UserResponse(accepted=False))
    boolean_string_json_io.set_total_results(boolean_string, 100)
    print(boolean_string_json_io.read(boolean_string))
    print(boolean_string_json_io.get_user_response(boolean_string))
    print(boolean_string_json_io.get_total_results(boolean_string))
