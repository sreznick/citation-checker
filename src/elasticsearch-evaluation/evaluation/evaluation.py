from elasticsearch import Elasticsearch
import re
import random


def generate_spoiled_phrase(text, number_mistakes):
    words = text.split()
    number_words_phrase = random.randint(min(len(words), 5), min(len(words), 7))
    # Index of the first word in phrase
    start_index = random.randint(0, len(words) - number_words_phrase)

    phrase_words = words[start_index:(start_index + number_words_phrase)]

    number_deleted_symbols = 0
    number_symbols_phrase = sum(len(word) for word in phrase_words)

    for _ in range(number_mistakes):
        # Word with mistakes
        while True:
            index_spoiled_word = random.randint(0, len(phrase_words) - 1)
            spoiled_word = phrase_words[index_spoiled_word]
            if len(spoiled_word) > 0:
                break

        # Choose mistake
        if len(phrase_words[index_spoiled_word]) > 1:
            mistake = random.randint(0, 2)
        elif number_deleted_symbols + 1 == number_symbols_phrase:
            mistake = 0
        else:
            mistake = random.randint(0, 1)

        # Perform mistake
        if mistake == 2:
            spoiled_symbol_index = random.randint(0, len(spoiled_word) - 2)
            spoiled_word = spoiled_word[:spoiled_symbol_index] + spoiled_word[spoiled_symbol_index + 1] + \
                           spoiled_word[spoiled_symbol_index] + spoiled_word[spoiled_symbol_index + 2:]

        else:
            spoiled_symbol_index = random.randint(0, len(spoiled_word) - 1)
            if mistake == 1:
                spoiled_word = spoiled_word[:spoiled_symbol_index] + "" + spoiled_word[spoiled_symbol_index + 1:]
            else:
                spoiled_word = spoiled_word[:spoiled_symbol_index] + "&" + spoiled_word[spoiled_symbol_index + 1:]

        phrase_words[index_spoiled_word] = spoiled_word

    return " ".join(phrase_words)


def count_mistakes(number_iterations, index_name='texts', min_number_mistakes=0, max_number_mistakes=5):
    """
    number_iterations - number of iterations
    index_name - index name
    """

    elasticsearch = Elasticsearch("http://localhost:9200")

    if not elasticsearch.indices.exists(index=index_name):
        print(f"There is no index with name '{index_name}'")
        return
    elif int(re.split("[ \n]", elasticsearch.cat.count(index='texts', params=None, headers=None))[2]) == 0:
        print(f"Index with name '{index_name}' is empty")
        return

    for number_mistakes in range(min_number_mistakes, max_number_mistakes):
        number_fails = 0

        for _ in range(number_iterations):
            random_query = {
                "function_score": {
                    "query": {
                        "match_all": {}
                    },
                    "random_score": {}
                }
            }

            initial_response = elasticsearch.search(index=index_name,
                                                    query=random_query, size=1)['hits']['hits'][0]['_source']
            initial_author = initial_response['author']
            initial_title = initial_response['title']
            initial_text = initial_response['text']

            # Introducing spelling mistakes by random
            spoiled_phrase = generate_spoiled_phrase(initial_text, number_mistakes)

            # Query
            phrase_query = {
                "match": {
                    "text": {
                        "query": spoiled_phrase,
                        "fuzziness": "AUTO"
                    }
                }
            }

            # Search for the best response on the query
            predicted_response = elasticsearch.search(index=index_name, query=phrase_query)
            if predicted_response['hits']['total']['value'] == 0:
                number_fails += 1
            else:
                predicted_author = predicted_response['hits']['hits'][0]['_source']['author']
                predicted_title = predicted_response['hits']['hits'][0]['_source']['title']
                if (predicted_author != initial_author) or (predicted_title != initial_title):
                    number_fails += 1

        print(f"With number of mistakes={number_mistakes}: number of fails={number_fails}, "
              f"number of iterations={number_iterations}")
    return


if __name__ == '__main__':
    count_mistakes(50, index_name="texts", min_number_mistakes=0, max_number_mistakes=10)
