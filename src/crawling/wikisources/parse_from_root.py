from src.crawling.wikisources.parser import WsParser
from src.crawling.crawler import crawl

if __name__ == '__main__':
    crawl('ws_content', WsParser('ws_state.json'), 2000)


