import itertools
import logging
import re
from typing import Iterator, Tuple, TypeVar, Optional
from urllib.parse import urlsplit, unquote_plus
import json
from os import path
import attr
from bs4 import BeautifulSoup

from src.crawling.common import NetworkHandler
from src.crawling.crawler import Crawler, Filter, TextContent

LOGGER = logging.getLogger(__name__)

wsFilter = Filter(
    whitelist=[
        'Категория:Все_авторы'
    ],
    blacklist=[
        ('..', 100),
        ('pagefrom=', 10),
        ('pageuntil=', 10),
        ('action=', 10),
        ('oldid=', 10),
        ('printable=', 10),
        'Служебная:',
        'Категория:',
        'Обсуждение_категории:',
        'Викитека:',
        'Участник:',
        'Участница:',
        'Страница:',
        'Обсуждение_индекса:',
        '.djvu',
        'Обсуждение_участника',
        'Обсуждение_участницы:',
        'Файл:',
        'Справка:',
        'Шаблон:',
        'Категория:Шаблоны',
        'Категория:User',
        'javascript:',
        'Обсуждение_Викитеки:',
        'ЭСБЕ',
        'МЭСБЕ',
        'НЭС',
        'БСЭ',
        'БЭЮ',
        'МСЭ',
        'РБС',
        'МСР',
        'ЕЭБЕ',
        'ЭСГ',
        'БЭАН',
        'ЭЛ',
        'РСКД',
        'ПБЭ',
        'ББСРП',
        'ВТ',
        'Словник',
    ]
)


class WsParser(Crawler):

    def __init__(self, state_file: Optional[str] = None, wait_time: float = .5):
        super().__init__(
            start_page='https://ru.wikisource.org/wiki/Категория:Все_авторы',
            home_page='https://ru.wikisource.org',
            filt=wsFilter,
            state_file=state_file,
            wait_time=wait_time
        )

    def try_parse_text(self, url: str, soup: BeautifulSoup) -> Optional[TextContent]:
        author = self.get_author(soup)
        if author is None:
            return None
        name = self.get_title(soup)
        text_elem = soup.find(attrs={'id': 'mw-content-text'})
        if text_elem is None:
            return None
        text = text_elem.text
        return TextContent(
            text=text,
            path=unquote_plus(urlsplit(url).path),
            author=author,
            name=name
        )

    @staticmethod
    def get_author(soup: BeautifulSoup) -> Optional[str]:
        author_elem = soup.find(attrs={'id': 'ws-author'})
        if author_elem is None:
            return None
        author = author_elem.text
        if (translator := soup.find('#ws-translator')) is not None:
            author += f', пер {translator.text}'
        return author

    @staticmethod
    def get_title(soup: BeautifulSoup) -> Optional[str]:
        name_elem = soup.find(attrs={'id': 'ws-title'})
        if name_elem is None:
            return None
        return name_elem.text

    def normalize_href(self, cur_url, href):
        href = super(WsParser, self).normalize_href(cur_url, href)
        href = re.sub(r'https://ru\.wikisource\.org/w/index\.php\?title=([^&]+)&?',
                      r'https://ru.wikisource.org/wiki/\1?', href)
        return href
