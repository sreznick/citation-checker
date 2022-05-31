import nltk
from nltk.stem.snowball import RussianStemmer
import string


class Preprocessor:

    def __init__(self):
        self._stemmer = RussianStemmer()
        self._punctuation = string.punctuation
        self._max_len = 100

    def max_len(self):
        return self._max_len

    def __remove_punctuation(self, word):
        if word in self._punctuation:
            return ""
        word = "".join([ch for ch in word if ch not in self._punctuation])
        return word

    def __punctuation(self, word):
        return self.__remove_punctuation(word) == ""

    def __preprocess_line(self, line):
        words = [word for word in nltk.tokenize.wordpunct_tokenize(line.lower())]
        return " ".join([word for word in words if not self.__punctuation(word)])

    def parse_book(self, book_path):
        book = open(book_path)
        prev_line = ""
        for line in nltk.sent_tokenize(" ".join(book.readlines())):
            prev_line += " " + line
            if len(prev_line) >= self._max_len:
                yield prev_line, self.__preprocess_line(prev_line)
                prev_line = ""
        if prev_line != "":
            yield prev_line, self.__preprocess_line(prev_line)
