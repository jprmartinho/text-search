from __future__ import annotations

from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

import search

# Sample data for testing
SAMPLE_DOCUMENTS = [
    {
        'title': 'Test Doc 1',
        'content': 'Content 1\nContent 2',
        'summary': 'Summary 1',
    },
    {
        'title': 'Test Doc 2',
        'content': 'Content 3\nContent 4',
        'summary': 'Summary 2',
    },
]


@pytest.fixture
@patch.object(search, 'SentenceTransformer')
@patch.object(search, 'Elasticsearch')
def mock_search_instance(mock_es, mock_model):
    magic_mock = MagicMock()
    mock_es.return_value = magic_mock
    mock_model.return_value = magic_mock
    return search.Search()


def test_search_init(mock_search_instance):
    assert isinstance(mock_search_instance.model, MagicMock)
    assert isinstance(mock_search_instance.es, MagicMock)


def test_create_index(mock_search_instance):
    mock_search_instance.create_index()
    mock_search_instance.es.indices.delete.assert_called_once_with(
        index='page_contents',
        ignore_unavailable=True,
    )
    mock_search_instance.es.indices.create.assert_called_once()


# Test getting embeddings
def test_get_embedding(mock_search_instance):
    mock_search_instance.model.encode.return_value = [0.123, 0.456]
    embedding = mock_search_instance.get_embedding('test text')
    assert embedding == [0.123, 0.456]
    mock_search_instance.model.encode.assert_called_once_with('test text')


# Test inserting documents
def test_insert_documents(mock_search_instance):
    mock_search_instance.insert_documents(SAMPLE_DOCUMENTS)
    assert mock_search_instance.es.bulk.called
    assert (
        mock_search_instance.model.encode.call_count == 4
    )  # Two paragraphs per document


# Test retrieving a document
def test_retrieve_document(mock_search_instance):
    mock_search_instance.es.get.side_effect = [
        {'_source': {'title': 'Test Doc', 'content': 'Content'}},
        {'_source': {'summary': 'Summary'}},
    ]
    document = mock_search_instance.retrieve_document('doc_id')
    assert document['_source']['summary'] == 'Summary'
    assert mock_search_instance.es.get.call_count == 2


# Test searching
@pytest.mark.parametrize(
    'query_args, expected_call',
    [
        (
            {'query': {'match': {'title': 'Test'}}},
            {'index': 'page_contents', 'query': {'match': {'title': 'Test'}}},
        ),
        (
            {'query': {'match_all': {}}},
            {'index': 'page_contents', 'query': {'match_all': {}}},
        ),
    ],
    ids=['match', 'match_all'],
)
def test_search(query_args, expected_call, mock_search_instance):
    mock_search_instance.search(**query_args)
    mock_search_instance.es.search.assert_called_with(**expected_call)
