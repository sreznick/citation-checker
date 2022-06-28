import itertools
import logging
import re
from typing import Iterator, Tuple, TypeVar, Optional
from urllib.parse import urlsplit
import json
from os import path
import attr
from bs4 import BeautifulSoup

from src.crawling.crawler import Crawler, Filter, TextContent, crawl

LOGGER = logging.getLogger(__name__)


class LibRuParser(Crawler):

    def __init__(self, state_file: Optional[str] = None, wait_time: float = .5):
        super().__init__(
            start_page='http://lib.ru',
            home_page='http://lib.ru',
            filt=Filter(
                blacklist=[
                    'What-s-new',
                    'Forum',
                    '..',
                    'lat',
                    'win',
                    'koi',
                    'HITPARAD',
                    '.dir',
                    '_Piece',
                    'Mirrors',
                    '.zip'
                ]
            ),
            state_file=state_file,
            wait_time=wait_time,
            force_encoding='koi8-r',
            random_crawl=True
        )

    def try_parse_text(self, url: str, soup: BeautifulSoup) -> Optional[TextContent]:
        if not url.endswith('.txt') or not url.startswith(self.home_page):
            return None

        author, name = self.get_author_name_for_url(url)
        if author is None:
            return None
        text = self.network_handler.download_text_from_url(f'{url}?format=_Ascii.txt', 'koi8-r')
        return TextContent(
            text=text,
            path=urlsplit(url).path,
            author=author,
            name=name
        )

    def get_author_name_for_url(self, url: str) -> Tuple[Optional[str], Optional[str]]:
        soup, author_url = self.network_handler.get_bs4_url_from_url(url.rpartition('/')[0])
        root_link = soup.find('a')
        if not (root_link.attrs['href'] == '/' and root_link.text == 'Lib.Ru'):
            LOGGER.warning(f"Can't parse {author_url} author")
            author = None
        else:
            author = root_link.parent.next_sibling
        name = None
        for link in soup.find_all('a'):
            if 'href' in link.attrs and self.normalize_href(author_url, link.attrs['href']) == url:
                name = link.text
                break
        return author, name


if __name__ == '__main__':
    crawl('libru_content', LibRuParser('libru_state.json'), 2000)