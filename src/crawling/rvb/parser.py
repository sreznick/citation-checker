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
import urllib.parse
LOGGER = logging.getLogger(__name__)


class RvbParser(Crawler):

    def __init__(self, state_file: Optional[str] = None, wait_time: float = .5):
        super().__init__(
            start_page='https://rvb.ru',
            home_page='https://rvb.ru',
            filt=Filter(
                blacklist=['..']
            ),
            state_file=state_file,
            wait_time=wait_time
        )

    def try_parse_text(self, url: str, soup: BeautifulSoup) -> Optional[TextContent]:
        if not url.startswith(self.home_page):
            return None
        if not soup.find(attrs={"class": "pager"}):
            return None
        breadcrumbs = soup.find('ol')
        if breadcrumbs is None:
            return None
        author = breadcrumbs.find("li").text
        if author is None:
            return None
        name = self.get_name_for_url(url, soup)
        if name is None:
            return None
        text = RvbParser.collect_text(soup)

        return TextContent(
            text=text,
            path=urlsplit(url).path,
            author=author,
            name=name
        )

    @staticmethod
    def collect_text(soup: BeautifulSoup):
        text = ""
        cur = soup.find("ol")
        while ('attrs' not in cur.__dict__) or (cur.attrs.get('class') != ['text-source']):
            cur = cur.next_sibling
            if cur is None:
                break
            text += cur.text
        return text

    def get_name_for_url(self, url: str, soup: BeautifulSoup) -> Optional[str]:
        toc = soup.find("ol").find_all("a")
        if not toc:
            return None
        toc = toc[-1]
        if toc is not None:
            toc = toc.attrs.get('href')
        if toc is None:
            return None
        toc_soup, toc = self.network_handler.get_bs4_url_from_url(urllib.parse.urljoin(url, toc))
        if toc_soup is None:
            return None
        for link in toc_soup.find_all("a"):
            if 'href' in link.attrs and self.normalize_href(toc, link.attrs['href']) == url:
                return link.text
        return None


if __name__ == '__main__':
    crawl('rvb_content', RvbParser('rvb_state.json'), 2000)