import string
from pathlib import Path

import nltk
from elasticsearch import Elasticsearch, helpers
from spellchecker import SpellChecker
from hunspell import HunSpell
from Levenshtein import distance
from tqdm import tqdm
from wiki_ru_wordnet import WikiWordnet

from src.search.parse import Preprocessor

from src.search.synonyms import SynonymSet


class SearchResult:
    def __init__(self, entry, query, modifier: float = 1):
        self._score = float(entry['_score']) * modifier
        self._query = query
        self._mod = modifier
        self.title = entry['_source']['title']
        self.author = entry['_source']['author']
        self._link = None
        self.line_num = entry['_source']['line_number']
        self._text = entry['_source']['full_text']
        
    def __eq__(self, other):
        return self.author == other.author and self.title == other.title and self.line_num == other.line_num

    def __lt__(self, other):
        return self._score < other.score()

    def print(self):
        print('"{}"\n{}\nparagraph #{} (score = {}):'.format(self.title, self.author,
                                                             self.line_num, self._score))
        print(self._query, self._mod)
        print(self._text)
        print("-------------------------------------------")

    def score(self):
        return self._score

    def __hash__(self):
        return hash(self.title) * 1000000 + hash(self.author) * 1000 + int(self.line_num)


class BookSearch:
    def __init__(self, host: str = 'localhost', port: int = 9200, index: str = 'test', make_new: bool = True):
        self._preprocessor = Preprocessor()
        self._es = Elasticsearch(
            "https://{}:{}".format(host, port),
            ca_certs="/home/alex/Загрузки/elasticsearch-8.1.2/config/certs/http_ca.crt",
            basic_auth=("elastic", "h*xbMjOi64URRDCi4_Ls")
        )
        self._index = index
        if make_new:
            mappings = {
                "properties": {
                    "author": {
                        "type": "keyword"
                    },
                    "title": {
                        "type": "text"
                    },
                    "full_text": {
                        "type": "text"
                    },
                    "search_text1": {
                        "type": "text",
                        "analyzer": "icu_snowball_folder",
                        "search_analyzer": "icu_snowball_folder"
                    },
                    "search_text2": {
                        "type": "text",
                        "analyzer": "icu_hunspell_folder",
                        "search_analyzer": "icu_hunspell_folder"
                    },
                    "stop_words_text": {
                        "type": "text",
                        "analyzer": "stop_words_folder",
                        "search_analyzer": "stop_words_folder"
                    }
                }
            }

            settings = {
                "index": {
                    "analysis": {
                        "analyzer": {
                            "icu_snowball_folder": {
                                "tokenizer": "icu_tokenizer",
                                "filter": ["icu_normalizer", "snowball"]
                            },
                            "icu_hunspell_folder": {
                                "tokenizer": "icu_tokenizer",
                                "filter": ["icu_normalizer", "ru_RU"]
                            },
                            "stop_words_folder": {
                                "tokenizer": "icu_tokenizer",
                                "filter": ["icu_normalizer", "russian_stop", "ru_RU"]
                            }
                        },
                        "filter": {
                            "ru_RU": {
                                "type": "hunspell",
                                "locale": "ru_RU"
                            },
                            "russian_stop": {
                                "type":       "stop",
                                "stopwords":  "_russian_"
                            },
                            "snowball": {
                                "type": "snowball",
                                "language": "Russian"
                            }
                        }
                    }
                }
            }

            if self._es.indices.exists(index=index):
                self._es.indices.delete(index=index, ignore=[400, 404])
            self._es.indices.create(index=index, mappings=mappings, settings=settings)
        nltk.download('all', quiet=True)
        self._hunspell = HunSpell("/home/alex/Proga/proj/hunspell/ru_RU/ru_RU.dic",
                                  "/home/alex/Proga/proj/hunspell/ru_RU/ru_RU.aff")
        self._spell = SpellChecker(language="ru")
        self._search_eps = 0.7
        self._wikiwordnet = WikiWordnet()

    def __already_indexed_book(self, author, title):
        title_author_query = {
            "bool": {
                "must": [
                    {
                        'match_phrase': {
                            'author': author
                        }
                    },
                    {
                        'match_phrase': {
                            'title.keyword': title
                        }
                    }
                ]
            }
        }
        return self._es.search(index=self._index, query=title_author_query)['hits']['total']['value'] != 0

    def add_book(self, book_path: Path, book_id, author, title):
        if self.__already_indexed_book(author, title):
            print(f"{book_path.name}: was already in database according to author and title")
            return

        paragraphs = []
        for i, lines in enumerate(self._preprocessor.parse_book(book_path)):
            line, preprocessed_line = lines
            doc = {
                "book_id": book_id,
                "author": author,
                "title": title,
                "line_number": i,
                "full_text": line.strip(),
                "search_text1": preprocessed_line,
                "search_text2": preprocessed_line
            }
            paragraphs.append(doc)
        helpers.bulk(self._es, paragraphs, index=self._index)

    def __full_text_search(self, query):
        results = self._es.search(
            index=self._index,
            query={
                "multi_match": {
                    "query": query,
                    "minimum_should_match": "90%",
                    "type": "most_fields",
                    "fields": ["stop_words_text^5", "search_text1^3", "search_text2^4", "full_text"]
                }
            }
        )
        return results['hits']['hits']

    def __get_search_results(self, query, modifier=1):
        results = self.__full_text_search(query)
        for entry in results:
            yield SearchResult(entry, query, modifier)

    def search(self, query):
        corrected = ' '.join(self.__correct_query(query))
        synsets = [SynonymSet(w, self._wikiwordnet, self._search_eps) for w in corrected.split(" ")]
        queries = get_all_synonyms(synsets, 0, list())
        results: set[SearchResult] = set()
        for syn_query, mod in tqdm(queries):
            results.update(self.__get_search_results(" ".join(syn_query), mod))
        print("Searching for \"{}\"{}. ".format(corrected, "" if corrected == query else " instead of \"{}\""
                                                .format(query)), end="")
        if not len(results):
            print("Nothing was found :(")
            return
        print("Here's what we found:")
        result_list = list(results)
        result_list.sort(reverse=True)
        for res in result_list[:10]:
            res.print()

    def __correct_query(self, query: str):
        for word in query.split(" "):
            h_word = ""
            if not self._hunspell.spell(word):
                h_word = self._hunspell.suggest(word)
                h_word = h_word[0] if h_word != list() else ""
            c_word = self._spell.correction(word)
            if distance(word, h_word) < len(word) / 2 and h_word != "":
                yield h_word
            elif distance(word, c_word) < len(word) / 2:
                yield c_word
            else:
                yield word


def get_all_synonyms(synsets: list[SynonymSet], pos: int, cur: list[str], cur_modifier=1):
    if pos == len(synsets):
        yield cur, cur_modifier
        return
    for synonym, modifier in synsets[pos].get_items():
        yield from get_all_synonyms(synsets, pos + 1, cur + [synonym], cur_modifier * modifier)
