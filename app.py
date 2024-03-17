from __future__ import annotations

from flask import Flask
from flask import render_template
from flask import request
from loguru import logger
from werkzeug.exceptions import HTTPException
from werkzeug.exceptions import InternalServerError

from search import Search


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
        query=query,
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


@app.get('/page_doc/<id>')
def get_page_doc(id):
    title, paragraphs = es.get_page_doc_title_summary(
        es.get_page_doc(id),
    )
    return render_template(
        'page_doc.html',
        title=title,
        paragraphs=paragraphs,
    )


@app.cli.command()
def regenerateindex():
    """Regenerate the Elasticsearch index."""
    response = es.regenerate_index()
    logger.info(
        f'Index with {len(response["items"])} page documents created '
        f'in {response["took"]} milliseconds.',
    )


@app.cli.command()
def getmapping():
    """Get mappings for both page content and summary indices."""
    response = es.get_mapping()
    logger.info(
        f'Mappings for both page content and summary indices:\n{response}',
    )
