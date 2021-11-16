import itertools
import logging
import re
from typing import Iterator, Tuple, TypeVar, Optional
from urllib.parse import urlparse

import attr
from bs4 import BeautifulSoup

from crawling.common import NetworkHandler

LOGGER = logging.getLogger(__name__)
T = TypeVar('T')


def islice(iterator: Iterator[T], max_step: int = None) -> Iterator[T]:
    if max_step is None:
        return iterator
    return itertools.islice(iterator, max_step)


@attr.s()
class LibRuContent:
    text: str = attr.ib()
    # meta inf
    path: str = attr.ib(default=None)
    name: str = attr.ib(default=None)
    author: str = attr.ib(default=None)
    section: str = attr.ib(default=None)
    section_id: int = attr.ib(default=None)

    def replace(self, **kwargs):
        attrs = attr.asdict(self, recurse=False)
        return LibRuContent(**{**attrs, **kwargs})


class LibRuParser:
    LIBRU_HOME = 'http://lib.ru'
    INTERESTED_SECTIONS = list(range(3)) + list(range(4, 10))
    SEE_ALSO_REGEXP = re.compile('См. также*')

    def __init__(self):
        self.author_parser = AuthorParser(dir=parse_dir)
        self.network_handler = NetworkHandler(1.)

    def crawl_from_root(self, max_count: int = None) -> Iterator[LibRuContent]:
        root_soup = self.network_handler.get_bs4_from_url(self.LIBRU_HOME)
        if root_soup is None:
            yield from ()
            return
        yield from islice(self.traverse_contents(root_soup), max_count)

    def traverse_contents(self, root_soup) -> Iterator[LibRuContent]:
        all_hrefs = [a for a in root_soup.find_all('a')]
        for section_id in self.INTERESTED_SECTIONS:
            cur_section = root_soup.find(attrs={'name': section_id})
            LOGGER.info(f'traversing section {cur_section.next.text}')
            nxt_section_line = root_soup.find(attrs={'name': section_id + 1}).sourceline

            section_hrefs = [(a.attrs['href'], a.next.text) for a in all_hrefs if
                             cur_section.sourceline < a.sourceline < nxt_section_line]

            for href, href_name in section_hrefs:
                LOGGER.info(f'traversing {href_name} subsection in {cur_section.next.text}')
                for librucontent in self.traverse_section(href):
                    yield librucontent.replace(section=cur_section.next.text, section_id=section_id)

    def traverse_section(self, section: str) -> Iterator[LibRuContent]:
        soup = self.network_handler.get_bs4_from_url(f'{self.LIBRU_HOME}/{section}')
        sa_start, sa_end = _detect_see_also_span(soup)
        all_tt = {tt.sourceline: tt for tt in soup.find_all('tt')
                  if not (sa_start < tt.sourceline < sa_end)}
        all_types = {line: tt.next.next.text for line, tt in all_tt.items()}
        all_hrefs = {a.sourceline: a for a in soup.find_all('a') if a.sourceline in all_tt}

        for line, htype in all_types.items():
            for content in self.author_parser.parse(htype,
                                                    f'{self.LIBRU_HOME}/{section}/{all_hrefs[line].attrs["href"]}',
                                                    self.network_handler):
                yield content.replace(author=all_hrefs[line].next.text)


def _detect_see_also_span(section_soup: BeautifulSoup) -> Tuple[int, int]:
    subsections = section_soup.findAll(lambda tag: tag.name == 'a' and 'name' in tag.attrs)
    ssections_lines = sorted(ss.sourceline for ss in subsections)
    found = section_soup.findAll(text=LibRuParser.SEE_ALSO_REGEXP)

    start, end = 0, 0

    if len(found) != 0:
        for candidate in found:
            start = candidate.parent.sourceline
            try:
                startid = ssections_lines.index(start)
                if startid != len(ssections_lines) - 1:
                    end = ssections_lines[startid + 1]
                else:
                    end = str(section_soup).count('/n') + 1
                break
            except ValueError:
                start, end = 0, 0

    return start, end


class AuthorParser:
    def __init__(self, **parsers):
        self.parsers = parsers

    def parse(self, author_type: str, url: str, network_handler: NetworkHandler):
        return self.get_parser(author_type)(url, network_handler)

    def get_parser(self, author_type: str):
        if author_type in self.parsers:
            return self.parsers[author_type]
        LOGGER.warning(f"can't parse {author_type} author type, skipping...")
        return self.dummy_parser

    @staticmethod
    def dummy_parser(url: str, network_handler: NetworkHandler) -> Iterator[LibRuContent]:
        yield from ()


def get_ogl_content(url: str, network_handler: NetworkHandler) -> Optional[LibRuContent]:
    LOGGER.info(f'getting {url}')
    text = network_handler.download_text_from_url(f'{url}?format=_Ascii.txt')
    if text:
        return LibRuContent(text=text, path=urlparse(url).path)


def parse_dir(url: str, network_handler: NetworkHandler) -> Iterator[LibRuContent]:
    soup = network_handler.get_bs4_from_url(url)
    if soup is None:
        yield from ()
        return

    sa_start, sa_end = _detect_see_also_span(soup)
    all_tt = {tt.sourceline: tt for tt in soup.find_all('tt')
              if not (sa_start < tt.sourceline < sa_end)}
    all_types = {line: tt.next.next.text for line, tt in all_tt.items()}
    all_hrefs = {a.sourceline: a for a in soup.find_all('a') if a.sourceline in all_tt}

    for line, htype in all_types.items():
        if htype == 'огл':
            content = get_ogl_content(f'{url}/{all_hrefs[line].attrs["href"]}', network_handler)
            if content:
                yield content.replace(name=all_hrefs[line].next.text)
