# Elasticsearch as

## Installation

- [Downloading Elasticsearch and Kibana(macOS/Linux and Windows)](https://dev.to/elastic/downloading-elasticsearch-and-kibana-macos-linux-and-windows-1mmo)

## Start of the search engine

- `elasticsearch-7.15.1/bin/elasticsearch`


## Brief overview of basic functionality

- Create index:

`curl -X PUT "localhost:9200/index_name?pretty"`

- Delete index:

`curl -X DELETE "http://localhost:9200/index_name"`

- Delete all indices:

`curl -X DELETE "http://localhost:9200/*"`

- Show all indices names:

`curl "http://localhost:9200/_aliases?pretty=true"`

- Typical query:

```
curl -X GET "localhost:9200/_search?pretty" -H 'Content-Type: application/json' -d'
{
  "query": {
    "match_phrase": {
      "source": "some phrase"
    }
  }
}'
```

