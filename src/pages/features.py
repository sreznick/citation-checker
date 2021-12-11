import bs4.element
from bs4 import BeautifulSoup
import requests
from collections import Counter
import numpy as np
import pandas as pd

all_percentiles = [60, 70, 80, 90, 100]

elements = [ bs4.element.Comment,
             bs4.element.Doctype,
             bs4.element.NavigableString,
             bs4.element.ProcessingInstruction,
             bs4.element.Script,
             bs4.element.Stylesheet,
             bs4.element.Tag ]

percentile_names = [f'p{q}' for q in all_percentiles]
element_names = [str(el).split('.')[-1][:-2] for el in elements]


def get_features(url):
    try:
        data = requests.get(url)
        if data.status_code == 200:
            soup = BeautifulSoup(data.text, 'html.parser')
            lens = []
            types = []
            for child in soup.recursiveChildGenerator():
                types.append(type(child))
                if type(child) != bs4.element.Tag:
                    lens.append(len(child))

            percentiles = [np.percentile(lens, q) for q in all_percentiles]
            elements_counter = Counter(types)
            elements_arr = [elements_counter[el] if el in elements_counter else 0 for el in elements]
            return percentiles + elements_arr + [len(soup.text)]
        else:
            return None
    except BaseException:
        return None


if __name__ == '__main__':
    filename = 'links.txt'
    with open(filename, 'r') as f:
        links = f.read().split()

    X = []
    for url in links:
        features = get_features(url)
        if features is not None:
            X.append(features)
            
    df = pd.DataFrame(X, columns=percentile_names + element_names + ['length'])
    df['is_text'] = [1 if url.endswith('.txt') else 0 for url in links]
    df.to_csv('texts.csv', index=False)
