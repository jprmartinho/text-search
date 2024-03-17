from __future__ import annotations

import json
from unittest.mock import MagicMock
from unittest.mock import mock_open
from unittest.mock import patch

import pytest

import search
from constants import CONTENT_FLD
from constants import EMBEDDING_FLD
from constants import PAGE_CONTENTS_IDX
from constants import PAGE_SUMMARIES_IDX
from constants import SUMMARY_FLD
from constants import TITLE_FLD
from constants import WIKI_PAGES_FILENAME


@pytest.fixture
def mock_page_docs():
    # Arrange
    return [
        {
            TITLE_FLD: 'title of page doc 1',
            CONTENT_FLD: 'page doc content paragraph 1\npage doc content paragraph 2',
            SUMMARY_FLD: 'summary of page doc 1',
        },
        {
            TITLE_FLD: 'title of page doc 2',
            CONTENT_FLD: 'page doc content paragraph 3\npage doc content paragraph 4',
            SUMMARY_FLD: 'summary of page doc 2',
        },
    ]


@pytest.fixture
@patch.object(search, 'SentenceTransformer')
@patch.object(search, 'Elasticsearch')
def mock_search_instance(mock_es, mock_model):
    # Arrange
    magic_mock = MagicMock()
    mock_es.return_value = magic_mock
    mock_model.return_value = magic_mock
    return search.Search()


def test_search_init(mock_search_instance):
    # Assert
    assert isinstance(mock_search_instance.model, MagicMock)
    assert isinstance(mock_search_instance.es, MagicMock)


def test_create_index(mock_search_instance):
    # Act
    mock_search_instance.create_index()

    # Assert
    assert mock_search_instance.es.indices.delete.call_count == 2
    assert mock_search_instance.es.indices.create.call_count == 2


def test_get_embedding(mock_search_instance):
    # Arrange
    mock_search_instance.model.encode.return_value = [0.123, 0.456]

    # Act
    embedding = mock_search_instance.get_embedding('query')

    # Assert
    assert embedding == [0.123, 0.456]
    mock_search_instance.model.encode.assert_called_once_with('query')


@patch('builtins.open', new_callable=mock_open, read_data=json.dumps({'key': 'value'}))
def test_get_page_docs_data(mock_open_file, mock_search_instance):
    # Act
    page_docs_data = mock_search_instance.get_page_docs_data()

    # Assert
    mock_open_file.assert_called_once_with(WIKI_PAGES_FILENAME)
    assert page_docs_data == {'key': 'value'}


def test_insert_page_docs(mock_search_instance, mock_page_docs):
    # Act
    mock_search_instance.insert_page_docs(mock_page_docs)

    # Assert
    assert mock_search_instance.es.bulk.called
    assert mock_search_instance.model.encode.call_count == 4


def test_get_page_doc(mock_search_instance):
    # Arrange
    mock_search_instance.es.get.side_effect = [
        {'_source': {TITLE_FLD: 'title of page doc', CONTENT_FLD: 'page doc content'}},
        {'_source': {SUMMARY_FLD: 'summary of page doc'}},
    ]
    # Act
    page_doc = mock_search_instance.get_page_doc('page_doc_id')

    # Assert
    assert page_doc['_source'][TITLE_FLD] == 'title of page doc'
    assert page_doc['_source'][CONTENT_FLD] == 'page doc content'
    assert page_doc['_source'][SUMMARY_FLD] == 'summary of page doc'
    assert mock_search_instance.es.get.call_count == 2


def test_get_page_doc_title_summary(mock_search_instance):
    # Arrange
    mock_page_doc = {
        '_source': {
            TITLE_FLD: 'title of page doc',
            SUMMARY_FLD: 'summary of page doc, paragraph 1\nsummary of page doc, paragraph 2',
        },
    }

    # Act
    title, paragraphs = mock_search_instance.get_page_doc_title_summary(
        mock_page_doc,
    )

    # Assert
    assert title == 'title of page doc'
    assert paragraphs == [
        'summary of page doc, paragraph 1', 'summary of page doc, paragraph 2',
    ]


def test_get_mapping(mock_search_instance):
    # Arrange
    mock_search_instance.es.indices.get_mapping.return_value = 'mapping'

    # Act
    response = mock_search_instance.get_mapping()

    # Assert
    assert response == 'mapping'
    mock_search_instance.es.indices.get_mapping.assert_called_once_with(
        index=[PAGE_CONTENTS_IDX, PAGE_SUMMARIES_IDX],
    )


@pytest.mark.parametrize(
    'query_args, expected_call',
    [
        (
            {'query': 'query text', 'size': 5, 'from_': 0},
            {
                'index': 'page_contents', 'query': {
                    'script_score': {
                        'query': {
                            'multi_match': {
                                'query': 'query text',
                                'fields': [TITLE_FLD, SUMMARY_FLD, CONTENT_FLD],
                            },
                        },
                        'script': {
                            'params': {'query_vector': [0.123, 0.456]},
                            'source': '_score + '
                            f"Math.max(0, cosineSimilarity(params.query_vector, '{EMBEDDING_FLD}'))",
                        },
                    },
                }, 'size': 5, 'from_': 0,
            },
        ),
    ],
    ids=['hybrid_search'],
)
def test_search(query_args, expected_call, mock_search_instance):
    # Arrange
    mock_search_instance.model.encode.return_value = [0.123, 0.456]

    # Act
    mock_search_instance.search(**query_args)

    # Assert
    mock_search_instance.es.search.assert_called_with(**expected_call)
