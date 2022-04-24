from src.crawling.libru.parser import LibRuParser
from src.crawling.crawler import crawl

if __name__ == '__main__':
    crawl('libru_content', LibRuParser('libru_state.json'), 2000)


