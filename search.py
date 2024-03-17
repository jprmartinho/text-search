from __future__ import annotations

import json
from typing import Any

from elastic_transport import ObjectApiResponse
from elasticsearch import Elasticsearch
from sentence_transformers import SentenceTransformer

from constants import CHAR_NEWLINE
from constants import CONTENT_FLD
from constants import EMBEDDING_FLD
from constants import PAGE_CONTENTS_IDX
from constants import PAGE_SUMMARIES_IDX
from constants import SUMMARY_FLD
from constants import TITLE_FLD
from constants import WIKI_PAGES_FILENAME


class Search:
    def __init__(self) -> None:
        # https://www.sbert.net/docs/pretrained_models.html#model-overview
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.es = Elasticsearch('http://es:9200')

    def create_index(self) -> None:
        self.es.indices.delete(
            index=PAGE_CONTENTS_IDX,
            ignore_unavailable=True,
        )
        self.es.indices.delete(
            index=PAGE_SUMMARIES_IDX,
            ignore_unavailable=True,
        )
        self.es.indices.create(
            index=PAGE_CONTENTS_IDX,
            mappings={
                'properties': {
                    'embedding': {
                        'type': 'dense_vector',
                    },
                },
            },
        )
        self.es.indices.create(index=PAGE_SUMMARIES_IDX)

    def get_embedding(self, text: str) -> list[float]:
        return self.model.encode(text)

    def insert_page_docs(self, page_docs: list[dict[str, str]]) -> ObjectApiResponse[Any]:
        operations: list[dict[str, Any]] = []
        for page_doc in page_docs:
            paragraphs: list[str] = page_doc[CONTENT_FLD].split(CHAR_NEWLINE)
            for paragraph in paragraphs:
                if not paragraph.strip():
                    continue
                operations.append({'index': {'_index': PAGE_CONTENTS_IDX}})
                operations.append(
                    {
                        TITLE_FLD: page_doc[TITLE_FLD],
                        CONTENT_FLD: paragraph,
                        EMBEDDING_FLD: self.get_embedding(paragraph),
                    },
                )
            self.es.index(
                index=PAGE_SUMMARIES_IDX,
                id=page_doc[TITLE_FLD],
                body={SUMMARY_FLD: page_doc[SUMMARY_FLD]},
            )
        return self.es.bulk(operations=operations)

    def get_page_doc(self, id: str) -> ObjectApiResponse[Any]:
        page_doc = self.es.get(index=PAGE_CONTENTS_IDX, id=id)
        summary = self.es.get(
            index=PAGE_SUMMARIES_IDX,
            id=page_doc['_source'][TITLE_FLD],
        )
        page_doc['_source'][SUMMARY_FLD] = summary['_source'][SUMMARY_FLD]
        return page_doc

    @staticmethod
    def get_page_doc_title_summary(page_doc: ObjectApiResponse[Any]) -> tuple[str, list[str]]:
        return page_doc['_source'][TITLE_FLD], page_doc['_source'][SUMMARY_FLD].split(CHAR_NEWLINE)

    @staticmethod
    def get_page_docs_data() -> list[dict[str, str]]:
        with open(WIKI_PAGES_FILENAME) as f:
            page_docs_data = json.loads(f.read())
        return page_docs_data

    def regenerate_index(self) -> ObjectApiResponse[Any]:
        self.create_index()
        return self.insert_page_docs(self.get_page_docs_data())

    def get_mapping(self):
        return self.es.indices.get_mapping(index=[PAGE_CONTENTS_IDX, PAGE_SUMMARIES_IDX])

    def search(self, query: str, size: int, from_: int) -> ObjectApiResponse[Any]:

        hybrid_search_query = {
            'script_score': {
                'query': {
                    'multi_match': {
                        'query': query,
                        'fields': [TITLE_FLD, SUMMARY_FLD, CONTENT_FLD],
                    },
                },
                'script': {
                    'params': {'query_vector': self.get_embedding(query)},
                    'source': f"_score + Math.max(0, cosineSimilarity(params.query_vector, '{EMBEDDING_FLD}'))",
                },
            },
        }

        return self.es.search(
            index=PAGE_CONTENTS_IDX,
            query=hybrid_search_query,
            size=size,
            from_=from_,
        )
