from __future__ import annotations

import json
import sys

import wikipedia as wiki
from loguru import logger

from constants import DEFAULT_SEARCH_TERM
from constants import WIKI_PAGES_FILENAME


def get_wiki_pages(term: str, limit: int = 5) -> list[wiki.page]:
    suggestion = wiki.suggest(term)
    if suggestion:
        term = suggestion
        logger.info(f'Suggested term: {suggestion}')

    wiki_page_titles: list[str] = wiki.search(term, results=limit)

    if not wiki_page_titles:
        logger.warning(f'No pages found for the term: {term}')
        return []

    logger.info(f'Found {len(wiki_page_titles)} pages for the term: {term}')

    wiki_pages: list[wiki.page] = []
    for page_title in wiki_page_titles:
        try:
            page = wiki.page(page_title)
            wiki_pages.append(page)
        except wiki.exceptions.PageError:
            logger.warning(f"Page '{page_title}' does not exist.")
        except wiki.exceptions.DisambiguationError as e:
            logger.warning(
                f"Page '{page_title}' refers to a disambiguation page. "
                f'Options are: {e.options}',
            )
            if e.options:
                try:
                    page = wiki.page(e.options[0])
                    wiki_pages.append(page)
                except wiki.exceptions.PageError:
                    logger.warning(f"Page '{e.options[0]}' does not exist.")
        except wiki.exceptions.HTTPTimeoutError:
            logger.error(f"Request to Wikipedia for '{page_title}' timed out.")
        except wiki.exceptions.RedirectError:
            logger.error(
                f"Page '{page_title}' resulted in an unexpected redirect.",
            )
        except wiki.exceptions.WikipediaException as e:
            logger.error(f'An unexpected error occurred: {e}')

    return wiki_pages


def download_wiki_pages(pages: list[wiki.page]):
    wiki_pages = []
    for page in pages:
        try:
            page_dict = {
                'title': page.title,
                'summary': page.summary,
                'content': page.content,
            }
            wiki_pages.append(page_dict)
            logger.info(f'Processed page: {page.title}')
        except Exception as e:
            logger.error(f'Failed to process page: {page.title}. Error: {e}')

    try:
        with open(WIKI_PAGES_FILENAME, 'w') as f:
            json.dump(wiki_pages, f, indent=4)
        logger.info(f'All pages downloaded to: {WIKI_PAGES_FILENAME}')
    except OSError as e:
        logger.error(
            f'OS error when writing to {WIKI_PAGES_FILENAME}: {str(e)}',
        )


if __name__ == '__main__':
    logger.remove()
    logger.add(
        sys.stderr,
        level='INFO',
    )
    term = input(f'Enter a term to search: [{DEFAULT_SEARCH_TERM}]').strip() \
        or DEFAULT_SEARCH_TERM
    pages = get_wiki_pages(term)
    download_wiki_pages(pages)
