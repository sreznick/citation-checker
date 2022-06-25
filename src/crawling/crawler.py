import itertools
import logging
import re
from pathlib import Path
from typing import Iterator, Tuple, TypeVar, Optional
from urllib.parse import urlparse, unquote_plus
import json
from os import path
import attr
from bs4 import BeautifulSoup
import random
from src.crawling.common import NetworkHandler
from src.util.log import setup_logging
import urllib.parse


def islice(iterator, max_step: int = None):
    if max_step is None:
        return iterator
    return itertools.islice(iterator, max_step)


LOGGER = logging.getLogger(__name__)


@attr.s()
class TextContent:
    text: str = attr.ib()
    path: str = attr.ib()
    name: str = attr.ib()
    author: str = attr.ib()
    source: str = attr.ib("")


class Filter:

    def __init__(self, blacklist=None, whitelist=None):
        self.blacklist = blacklist if blacklist is not None else []
        self.whitelist = whitelist if whitelist is not None else []

    def rank(self, url, templace):
        if isinstance(templace, tuple):
            (pat, score) = templace
            if pat in url:
                return score
        elif templace in url:
            return 1
        return 0

    def is_allowed(self, url):
        whitelist_rank = max(self.rank(url, x) for x in self.whitelist) if self.whitelist else 0
        blacklist_rank = max(self.rank(url, x) for x in self.blacklist) if self.blacklist else 0
        return whitelist_rank >= blacklist_rank


EMPTY_FILTER = Filter()


class Crawler:

    def __init__(self, start_page, home_page, filt=EMPTY_FILTER, state_file: Optional[str] = None, wait_time=0.5,
                 force_encoding=None, random_crawl=False):
        self.start_page = start_page
        self.home_page = home_page
        self.force_encoding = force_encoding
        self.filt = filt
        self.visited_urls = set()
        self.to_visit = [self.start_page]
        self.random_crawl = random_crawl

        self.network_handler = NetworkHandler(wait_time)

        self.state_file = state_file
        if state_file is not None:
            self.read_state(state_file)

    def is_allowed(self, url):
        return ((not url.startswith('http')) or url.startswith(self.home_page)) \
               and self.filt.is_allowed(url)

    def get_state(self):
        return {
            'visited_urls': list(self.visited_urls),
            'to_visit': self.to_visit
        }

    def load_state(self, state):
        self.visited_urls = set(state['visited_urls'])
        self.to_visit = state['to_visit']
        self.to_visit = [x for x in self.to_visit if self.is_allowed(x)]

    def save_state(self, filename: str):
        with open(filename, 'w') as f:
            json.dump(self.get_state(), f)

    def read_state(self, filename: str):
        if path.exists(filename):
            with open(filename) as f:
                self.load_state(json.load(f))

    def crawl_from_root(self, max_count: Optional[int] = None, save: bool = True):
        yield from islice(self.crawl(save), max_count)

    def crawl(self, save: bool):
        while self.to_visit:
            if self.random_crawl:
                url = self.to_visit.pop(random.randrange(len(self.to_visit)))
            else:
                url = self.to_visit.pop()
            if (text := self.traverse(url)) is not None:
                text.source = url
                yield text
            if save and self.state_file is not None:
                self.save_state(self.state_file)

    def traverse(self, url: str) -> Optional[TextContent]:
        logging.info(url)
        self.visited_urls.add(url)
        soup, url = self.network_handler.get_bs4_url_from_url(url, self.force_encoding)
        if soup is None:
            logging.warning(f"Can't parse {url}")
            return None
        new_urls = []
        for link in soup.find_all('a'):
            if 'href' not in link.attrs:
                continue
            href = link.attrs['href']
            href = self.normalize_href(url, href)
            if not self.is_allowed(href):
                continue
            if href not in self.visited_urls:
                self.visited_urls.add(href)
                new_urls.append(href)
        self.to_visit += reversed(new_urls)
        return self.try_parse_text(url, soup)

    def try_parse_text(self, url: str, soup: BeautifulSoup) -> Optional[TextContent]:
        raise NotImplementedError

    def normalize_href(self, cur_url, href):
        if href.startswith('#') or href == '':
            href = cur_url
        if href.startswith('//'):
            href = f'{self.home_page.partition("//")[0]}{href}'
        if not href.startswith('http'):
            if href.startswith('..'):
                return '..'
            if href.startswith('/'):
                href = f'{self.home_page}{href}'
            else:
                if cur_url.endswith('/'):
                    href = f'{cur_url}{href}'
                else:
                    parent = cur_url.rpartition('/')[0]
                    href = f'{parent}/{href}'
        if '#' in href:
            href = href.rpartition('#')[0]
        href = href.rstrip('/')
        href = unquote_plus(href)
        return href


def crawl(storage_name: str, parser: Crawler, max_count=100, save=True):
    text_extensions = {'.txt'}
    storage_path = Path.cwd() / storage_name
    setup_logging()
    for content in parser.crawl_from_root(max_count, save):
        target_dir = storage_path / content.path.lstrip('/')
        if target_dir.suffix in text_extensions:
            target_dir = target_dir.with_suffix('')
        target_dir.mkdir(parents=True, exist_ok=True)
        (target_dir / (content.name + '.txt')).write_text(content.text)
        metainf = attr.asdict(content)
        del metainf['text']
        (target_dir / 'metainf.json').write_text(json.dumps(metainf, ensure_ascii=False))