#!/usr/bin/bash

echo "delete template..."
curl -XDELETE "ap:9200/_index_template/job_postings_template"

echo -e "\nCreateing new template..."
curl -XPUT "ap:9200/_index_template/job_postings_template" \
-H "Content-Type: application/json" -d '
{
  "index_patterns": ["job_posting*"],
  "priority": 1,
  "template": {
    "settings": {
      "number_of_replicas": 2,
      "analysis": {
        "tokenizer": {
          "two_gram_tokenizer": {
            "type": "ngram",
            "min_gram": 2,
            "max_gram": 2
          }
        },
        "analyzer": {
          "two_gram_analyzer": {
            "type": "custom",
            "tokenizer": "two_gram_tokenizer",
            "filter": ["lowercase"]
          }
        }
      }
    },
    "mappings": {
      "properties": {
        "domain":    { "type": "keyword" },
        "href":      { "type": "keyword" },
        "company":   { "type": "text", "analyzer": "two_gram_analyzer" },
        "title":     { "type": "text", "analyzer": "two_gram_analyzer" },
        "msgid":     { "type": "keyword" },
        "pay":       { "type": "keyword" },
        "location":  { "type": "keyword" },
        "career":    { "type": "keyword" },
        "education": { "type": "keyword" },
        "deadline":  { "type": "keyword" }, 
        "body_text": { "type": "text", "analyzer": "two_gram_analyzer" },
        "type":      { "type": "keyword" },
        "morph":     { "type": "keyword" }
      }
    }
  }
}'
