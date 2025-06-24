# Quick Start

## Installation

```bash
pip install pharia-data-sdk
```

## Usage

### Data Platform Connector

```python
from pharia_data_sdk.connectors.data import DataClient

client = DataClient(token="<token>", base_data_platform_url="<base_data_platform_url>")

repositories = client.list_repositories()
repository = repositories[0]
datasets = client.list_datasets(repository)
dataset = datasets[0]
```

### Document Index Connector
```python
from pharia_data_sdk.connectors.document_index.document_index import DocumentIndexClient, SearchQuery

client = DocumentIndexClient(token="<token>", base_document_index_url="<base_document_index_url>")

namespaces = client.list_namespaces()
collections = client.list_collections(namespaces[0])
indexes = client.list_indexes(namespaces[0])
client.search(collections[0], indexes[0].index, SearchQuery(query="What fish is most common in swedish lakes?"))
```

### Retrievers
```python
from pharia_data_sdk.connectors.retrievers.document_index_retriever import DocumentIndexRetriever
from pharia_data_sdk.connectors.document_index.document_index import DocumentIndexClient

retriever = DocumentIndexRetriever(
    document_index=DocumentIndexClient(token="<token>", base_document_index_url="<base_document_index_url>"),
    index_name="<index_name>",
    namespace="<namespace>",
    collection="<collection>",
)

retriever.get_relevant_documents_with_scores("What fish is most common in swedish lakes?")
```