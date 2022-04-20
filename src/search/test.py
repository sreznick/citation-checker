from pathlib import Path
from search import BookSearch


if __name__ == '__main__':
    book_search = BookSearch()
    book_path = Path("/home/alex/Proga/proj/citation-checker/src/search/test.txt")
    book_search.add_book(book_path, 1)
    book_search.get_search_results("алиса")
