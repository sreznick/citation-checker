from pathlib import Path
import nltk
from nltk.stem import WordNetLemmatizer
import string


class Preprocessor:

    def __init__(self):
        self._lemmatizer = WordNetLemmatizer()

    def parse_book(self, book_path):
        book = open(Path(book_path))
        for line in book.readlines():
            yield self.preprocess_line(line)

    def preprocess_line(self, line):
        words = [word for word in  # self._lemmatizer.lemmatize(word)
                 nltk.tokenize.word_tokenize(line.lower(), language='russian')]
        return " ".join([word for word in words if word not in string.punctuation])
