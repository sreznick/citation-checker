import json
from pathlib import Path
from search import BookSearch
from tqdm import tqdm


def fix_path(path: str):
    path = path[1:]
    ar = path.split('/')
    name = ar[-1][:-4]
    ar[-1] = name
    ar.append(name + ".txt")
    return Path('/'.join(ar))


if __name__ == '__main__':
    book_search = BookSearch()
    dir_path = Path("/home/alex/Proga/proj/data")
    for i, json_path in tqdm(enumerate(dir_path.rglob("*.json"), start=1)):
        json_data = json.load(open(json_path))
        book_search.add_book(dir_path.joinpath(fix_path(json_data["path"])), i,
                             json_data["author"], json_data["name"])
    print("*** LOADING COMPLETE ***")
