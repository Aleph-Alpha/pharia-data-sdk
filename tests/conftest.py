import os
from collections.abc import Sequence
from os import getenv

from aleph_alpha_client import Client
from dotenv import load_dotenv
from pharia_inference_sdk.connectors import (
    AlephAlphaClientProtocol,
    LimitedConcurrencyClient,
)
from pytest import fixture

from pharia_data_sdk.connectors.retrievers.base_retriever import Document
from pharia_data_sdk.connectors.retrievers.qdrant_in_memory_retriever import (
    QdrantInMemoryRetriever,
    RetrieverType,
)
from tests.conftest_document_index import *  # noqa: F403 - we import everything here to get the file to be "appended" to this file and thus making all fixtures available

load_dotenv()


@fixture(scope="session")
def token() -> str:
    token = getenv("AA_TOKEN")
    assert isinstance(token, str)
    return token


@fixture(scope="session")
def inference_url() -> str:
    return os.environ["CLIENT_URL"]


@fixture(scope="session")
def client(token: str, inference_url: str) -> AlephAlphaClientProtocol:
    return LimitedConcurrencyClient(
        Client(token, host=inference_url),
        max_concurrency=10,
        max_retry_time=10,
    )


@fixture
def asymmetric_in_memory_retriever(
    client: AlephAlphaClientProtocol,
    in_memory_retriever_documents: Sequence[Document],
) -> QdrantInMemoryRetriever:
    return QdrantInMemoryRetriever(
        in_memory_retriever_documents,
        client=client,
        k=2,
        retriever_type=RetrieverType.ASYMMETRIC,
    )


@fixture
def symmetric_in_memory_retriever(
    client: AlephAlphaClientProtocol,
    in_memory_retriever_documents: Sequence[Document],
) -> QdrantInMemoryRetriever:
    return QdrantInMemoryRetriever(
        in_memory_retriever_documents,
        client=client,
        k=2,
        retriever_type=RetrieverType.SYMMETRIC,
    )
