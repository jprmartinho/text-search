from __future__ import annotations

import json

from elasticsearch import Elasticsearch
from loguru import logger
from sentence_transformers import SentenceTransformer


class Search:
    def __init__(self):
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.es = Elasticsearch('http://es:9200')

    @logger.catch
    def create_index(self):
        self.es.indices.delete(index='page_contents', ignore_unavailable=True)
        self.es.indices.create(
            index='page_contents',
            mappings={
                'properties': {
                    'embedding': {
                        'type': 'dense_vector',
                    },
                },
            },
        )

    @logger.catch
    def get_embedding(self, text):
        return self.model.encode(text)

    @logger.catch
    def insert_documents(self, documents):
        operations = []
        for document in documents:
            paragraphs = document['content'].split('\n')
            for paragraph in paragraphs:
                if not paragraph.strip():
                    continue
                operations.append({'index': {'_index': 'page_contents'}})
                operations.append(
                    {
                        'title': document['title'],
                        'content': paragraph,
                        'embedding': self.get_embedding(paragraph),
                    },
                )
            self.es.index(
                index='page_summaries',
                id=document['title'],
                body={'summary': document['summary']},
            )
        return self.es.bulk(operations=operations)

    @logger.catch
    def retrieve_document(self, id):
        document = self.es.get(index='page_contents', id=id)
        summary = self.es.get(
            index='page_summaries',
            id=document['_source']['title'],
        )
        document['_source']['summary'] = summary['_source']['summary']
        return document

    @logger.catch
    def reindex(self):
        self.create_index()
        with open('wiki_pages.json') as f:
            documents = json.loads(f.read())
        return self.insert_documents(documents)

    @logger.catch
    def get_mapping(self):
        return self.es.indices.get_mapping(index='page_contents')

    @logger.catch
    def search(self, **query_args):
        return self.es.search(index='page_contents', **query_args)
