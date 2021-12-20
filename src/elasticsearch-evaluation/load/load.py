from elasticsearch import Elasticsearch, helpers
import os
import sys


def paragraph_parser(text):
    # Split text into paragraphs
    split_text = text.split('\n')

    # Replace " with \" and delete spaces
    for paragraph_ind, paragraph in enumerate(split_text):
        split_text[paragraph_ind] = paragraph.strip().replace('"', '\\"')

    return split_text


def doc_parser(path, index_name='texts'):
    """
    path - relative path to the directory with texts
    index_name - name of the index to load texts
    """

    elasticsearch = Elasticsearch("http://localhost:9200")

    # The "title" has additional field, which contains raw string. This field is not tokenized, allowing us
    # to check for exact match during loading. At the same we are able to use title for ordinary search as well.
    # The "author" also is made a "keyword", thus only the exact search can be done on it.
    mappings = {
        "properties": {
            "author": {
                "type": "keyword"
            },
            "title": {
                "type": "text",
                "fields": {
                    "keyword": {
                        "type":  "keyword"
                    }
                }
            }
        }
    }

    if not elasticsearch.indices.exists(index=index_name):
        elasticsearch.indices.create(index=index_name, mappings=mappings)

    texts_dir = os.path.join(os.path.dirname(os.path.realpath(sys.argv[0])), path)

    for root, _, files in os.walk(texts_dir):
        author = os.path.basename(root)

        for file_name in files:
            file_path = os.path.join(root, file_name)

            # Check if this file is not in index already
            search_query = {
                "bool": {
                    "must": [
                        {
                            'match_phrase': {
                                'author': author
                            }
                        },
                        {
                            'match_phrase': {
                                'title.keyword': file_name
                            }
                        }
                    ]
                }
            }

            response = elasticsearch.search(index=index_name, query=search_query)

            if response['hits']['total']['value'] == 0:
                with open(file_path, 'r') as file:
                    file_text = file.read()

                    paragraphs = []

                    # Split on paragraphs and load each of them into elasticsearch
                    for paragraph in paragraph_parser(file_text):
                        if paragraph:
                            document = {
                                "author": author,
                                "title": file_name,
                                "text": paragraph
                            }
                            paragraphs.append(document)

                    # Bulk API is used to perform several operations in a single API call
                    helpers.bulk(elasticsearch, paragraphs, index=index_name)
                    print(f"{file_name}: was uploaded successfully")
            else:
                print(f"{file_name}: was already in database")


if __name__ == '__main__':
    doc_parser("texts")
