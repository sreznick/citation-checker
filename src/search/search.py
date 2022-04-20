import nltk
from elasticsearch import Elasticsearch
from src.search.parse import Preprocessor
from spellchecker import SpellChecker


class BookSearch:

    def __init__(self, host='localhost', port=9200, index='test', make_new=True):
        self._preprocessor = Preprocessor()
        self._search = Elasticsearch(
            "https://{}:{}".format(host, port),
            ca_certs="/home/alex/Загрузки/elasticsearch-8.1.2/config/certs/http_ca.crt",
            basic_auth=("elastic", "h*xbMjOi64URRDCi4_Ls")
        )
        self._index = index
        if make_new:
            self._search.indices.delete(index=index, ignore=[400, 404])
            self._search.indices.create(index=index, ignore=400)
        nltk.download('all', quiet=True)
        self._spell = SpellChecker(language="ru")
        #  self._last_id = 0

    def add_book(self, book_path, book_id):  # we should decide on book format here
        for i, line in enumerate(self._preprocessor.parse_book(book_path)):
            doc = {
                "book_id": book_id,
                "line_number": i,
                "text": line
            }
            self._search.index(index=self._index, document=doc)

    def __full_text_search(self, query):
        results = self._search.search(
            index=self._index,
            query={
                'match': {
                    'text': query,
                }
            }
        )
        return results['hits']['hits']

    def get_search_results(self, query):
        corrected = ' '.join(self.__correct_query(query))
        print("Searching for \"{}\"{}:".format(corrected,
                                               ("" if corrected == query else " instead of \"{}\"".format(query))))
        results = self.__full_text_search(corrected)
        if not len(results):
            print("Nothing was found :(")
            return
        print("Here's what we found:")
        for entry in results:
            res = entry['_source']
            print('Book #{}, *book_name*, line #{}:'.format(res['book_id'], res['line_number']))
            print(res['text'])

    def __correct_query(self, query: str):
        for word in self._preprocessor.preprocess_line(query).split(" "):
            yield self._spell.correction(word)
