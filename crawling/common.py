import logging
import time
from typing import Optional
from urllib.parse import urlparse

import chardet
import requests
from bs4 import BeautifulSoup

LOGGER = logging.getLogger(__name__)


def is_redirected(url1, url2):
    return urlparse(url1).netloc != urlparse(url2).netloc


class NetworkHandler:
    def __init__(self, interval: float = 0):
        self.interval = interval
        self.last_checkpoint = time.time() - interval

    def download_text_from_url(self, url: str):
        data = self.get_data(url)
        if data.status_code != 200:
            LOGGER.warning(f'url {url} returned code {data.status_code}. skipping...')
            return None
        if is_redirected(url, data.url):
            return None
        enc = chardet.detect(data.content)['encoding']
        return data.content.decode(enc)

    def get_bs4_from_url(self, url: str) -> Optional[BeautifulSoup]:
        data = self.get_data(url)
        if data.status_code != 200:
            LOGGER.warning(f'url {url} returned code {data.status_code}. skipping...')
            return None
        if is_redirected(url, data.url):
            LOGGER.warning(f'url {url} redirected to {data.url}. skipping...')
            return None
        enc = chardet.detect(data.content)['encoding']
        return BeautifulSoup(data.content.decode(enc), features='html.parser')

    def get_data(self, url: str):
        """play fine to not get blocked"""
        w8time = self.interval - (time.time() - self.last_checkpoint)
        if w8time > 0:
            LOGGER.info(f'sleep for {w8time:.2f} seconds...')
            time.sleep(w8time)
        data = requests.get(url)
        self.last_checkpoint = time.time()
        return data
