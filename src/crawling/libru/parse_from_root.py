import json
from pathlib import Path

import attr

from src.crawling.libru.parser import LibRuParser
from src.util.log import setup_logging


def main():
    storage_path = Path.cwd() / 'libru_content_3'
    setup_logging()
    state_file = 'libru_state.json'
    parser = LibRuParser(state_file)
    for content in parser.crawl_from_root(max_count=2000, save_to=state_file):
        filepath = storage_path / content.path.lstrip('/')
        filepath = filepath.with_suffix('') / filepath.name
        filepath.parent.mkdir(parents=True, exist_ok=True)
        filepath.write_text(content.text)
        metainf = attr.asdict(content)
        del metainf['text']
        (filepath.parent / 'metainf.json').write_text(json.dumps(metainf, ensure_ascii=False))


if __name__ == '__main__':
    main()


