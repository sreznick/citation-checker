import logging
import sys
from pathlib import Path


def setup_logging(level=logging.INFO, log_dir: Path = None):
    logging.basicConfig(format='%(asctime)s%(levelname)s%(name)s|%(process)d|%(message)s', level=level,
                        stream=sys.stderr)#, filename=str(log_dir / 'citation.log') if log_dir else None)
    logging.getLogger("requests").setLevel(logging.ERROR)
