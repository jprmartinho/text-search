from __future__ import annotations

import sys

from flask import Flask
from flask import render_template
from flask import request
from loguru import logger
from werkzeug.exceptions import HTTPException
from werkzeug.exceptions import InternalServerError

from search import Search

logger.remove()
logger.add(
    sys.stderr,
    level='INFO',
)

app = Flask(__name__)

es = Search()


@app.errorhandler(Exception)
def handle_exception(e):
    logger.error(f'An error occurred: {e}')

    # pass through HTTP errors
    if isinstance(e, HTTPException):
        return e
    # handle non-HTTP exceptions
    return InternalServerError()


@app.get('/')
def index():
    return render_template('index.html')


@app.post('/')
def handle_search():
    query = request.form.get('query', '')
    from_ = request.form.get('from_', type=int, default=0)
    topk = request.form.get('topk', type=int, default=5)

    results = es.search(
        query={
            'script_score': {
                'query': {
                    'multi_match': {
                        'query': query,
                        'fields': ['title', 'summary', 'content'],
                    },
                },
                'script': {
                    'source': '_score + '
                    'Math.max('
                    "0, cosineSimilarity(params.query_vector, 'embedding'))",
                    'params': {'query_vector': es.get_embedding(query)},
                },
            },
        },
        size=topk,
        from_=from_,
    )

    return render_template(
        'index.html',
        results=results['hits']['hits'],
        query=query,
        topk=topk,
        from_=from_,
        total=results['hits']['total']['value'],
    )


@app.get('/document/<id>')
def get_document(id):
    document = es.retrieve_document(id)
    title = document['_source']['title']
    paragraphs = document['_source']['summary'].split('\n')
    return render_template('document.html', title=title, paragraphs=paragraphs)


@app.cli.command()
def reindex():
    """Regenerate the Elasticsearch index."""
    response = es.reindex()
    logger.info(
        f'Index with {len(response["items"])} documents created '
        f'in {response["took"]} milliseconds.',
    )
