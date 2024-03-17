[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://github.com/pre-commit/pre-commit)
![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=for-the-badge&logo=docker&logoColor=white)
![ElasticSearch](https://img.shields.io/badge/-ElasticSearch-005571?style=for-the-badge&logo=elasticsearch)
![Flask](https://img.shields.io/badge/flask-%23000.svg?style=for-the-badge&logo=flask&logoColor=white)


# Text Vectorization and Search Challenge

## Overview

This challenge focuses on creating a system that can take a set of text, vectorize it, and make it searchable by indexing it in a vector database.

### Requirements

1. **Task**: Vectorize a set of 5-10 articles from Wikipedia (read from a file to reduce complexity).
2. **Text Chunking and Vectorization**:
   - Break down the articles into smaller chunks.
   - Utilize open-source text embedding models to vectorize the text chunks.
3. **Graph Database**:
   - Store the embeddings of the text chunks in an open-source graph database capable of supporting vector search.
4. **Querying**:
   - Implement a querying system where the user input (a text query) is used to search the top K results against the vector database.
5. **Bonus Points**:
   - If your search system can handle both text and embeddings in a single query and re-rank results based on relevance.

## Instructions for Running the Code

- Clone this repository and build.
    ```shell
    git clone https://github.com/jprmartinho/text-search.git

    cd text-search

    # Trigger docker compose build command, and tail the logs
    make build; make tail-logs-api

    # Go to http://127.0.0.1:5001/
    ```


---
