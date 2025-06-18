# pharia-data-sdk

Formerly the `intelligence_layer/connectors/data`, `intelligence_layer/connectors/document_index` and `intelligence_layer/connectors/retrievers` modules.

## Overview

This module provides connectors for interacting with the Pharia Data Platform and Document Index, you users to semantically search, access and manage data, documents, and their associated metadata. 

## Installation

```bash
pip install pharia-data-sdk
```

## Usage

### Data Platform Connector

```python
from pharia_data_sdk.connectors.data import DataClient

client = DataClient(token="your_token", base_data_platform_url="<base_data_platform_url>")

client.list_repositories()
```

### Document Index Connector
```python
from pharia_data_sdk.connectors.document_index import DocumentIndexClient

client = DocumentIndexClient(token="your_token", base_document_index_url="<base_document_index_url>")

client.list_namespaces()
```

### Retrievers
```python
from pharia_data_sdk.connectors.retrievers.document_index_retriever import DocumentIndexRetriever
from pharia_data_sdk.connectors.document_index import DocumentIndexClient

retriever = DocumentIndexRetriever(
    document_index=DocumentIndexClient(token="your_token", base_document_index_url="<base_document_index_url>"),
    index_name="<index_name>",
    namespace="<namespace>",
    collection="<collection>",
)

retriever.get_relevant_documents_with_scores("What is the capital of France?")
```

## Contributing

We welcome contributions! Please see our [Contributing Guide](https://github.com/Aleph-Alpha/pharia-data-sdk/blob/main/CONTRIBUTING.md) for details on how to set up the development environment and submit changes.
