import asyncio
import os
import random
import re
import string
from collections.abc import AsyncIterator, Awaitable, Callable, Iterable, Iterator
from contextlib import asynccontextmanager, contextmanager
from datetime import datetime, timedelta, timezone
from functools import wraps
from time import sleep
from typing import ParamSpec, TypeVar, get_args, overload

import pytest_asyncio
from dotenv import load_dotenv
from pytest import fixture

from pharia_data_sdk.connectors.base.json_serializable import JsonSerializable
from pharia_data_sdk.connectors.document_index.document_index import (
    AsyncDocumentIndexClient,
    CollectionPath,
    DocumentContents,
    DocumentIndexClient,
    DocumentPath,
    EmbeddingConfig,
    HybridIndex,
    IndexConfiguration,
    IndexPath,
    InstructableEmbed,
    Representation,
    SearchQuery,
    SemanticEmbed,
)
from pharia_data_sdk.connectors.retrievers.base_retriever import (
    Document,
    DocumentChunk,
)
from pharia_data_sdk.connectors.retrievers.document_index_retriever import (
    AsyncDocumentIndexRetriever,
    DocumentIndexRetriever,
)

load_dotenv()
P = ParamSpec("P")
R = TypeVar("R")


@fixture(scope="session")
def document_index(token: str) -> DocumentIndexClient:
    return DocumentIndexClient(
        token, base_document_index_url=os.environ["DOCUMENT_INDEX_URL"]
    )


@pytest_asyncio.fixture()
async def async_document_index(token: str) -> AsyncIterator[AsyncDocumentIndexClient]:
    async with AsyncDocumentIndexClient(
        token, base_document_index_url=os.environ["DOCUMENT_INDEX_URL"]
    ) as client:
        yield client


def to_document(document_chunk: DocumentChunk) -> Document:
    return Document(text=document_chunk.text, metadata=document_chunk.metadata)


@overload
def retry(
    func: None = None, max_retries: int = 3, seconds_delay: float = 0.0
) -> Callable[[Callable[P, R]], Callable[P, R]]: ...


@overload
def retry(
    func: Callable[P, R], max_retries: int = 3, seconds_delay: float = 0.0
) -> Callable[P, R]: ...


def retry(
    func: Callable[P, R] | None = None,
    max_retries: int = 60,
    seconds_delay: float = 0.5,
) -> Callable[[Callable[P, R]], Callable[P, R]] | Callable[P, R]:
    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            for _ in range(1 + max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    sleep(seconds_delay)

            raise last_exception

        return wrapper

    if func is None:
        return decorator
    else:
        return decorator(func)


@overload
def async_retry(
    *,
    max_retries: int = 3,
    seconds_delay: float = 0.0,
) -> Callable[[Callable[P, Awaitable[R]]], Callable[P, Awaitable[R]]]: ...


@overload
def async_retry(
    func: Callable[P, Awaitable[R]],
    *,
    max_retries: int = 3,
    seconds_delay: float = 0.0,
) -> Callable[P, Awaitable[R]]: ...


def async_retry(
    func: Callable[P, Awaitable[R]] | None = None,
    *,
    max_retries: int = 60,
    seconds_delay: float = 0.5,
) -> (
    Callable[[Callable[P, Awaitable[R]]], Callable[P, Awaitable[R]]]
    | Callable[P, Awaitable[R]]
):
    def decorator(f: Callable[P, Awaitable[R]]) -> Callable[P, Awaitable[R]]:
        @wraps(f)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            for _ in range(1 + max_retries):
                try:
                    return await f(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    await asyncio.sleep(seconds_delay)
            raise last_exception

        return wrapper

    if func is None:
        return decorator
    else:
        return decorator(func)


def random_alphanumeric_string(length: int = 20) -> str:
    return "".join(random.choices(string.ascii_letters + string.digits, k=length))


def random_identifier() -> str:
    name = random_alphanumeric_string(10)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    return f"intelligence-layer-ci-{name}-{timestamp}"


def is_outdated_identifier(identifier: str, timestamp_threshold: datetime) -> bool:
    # match the format that is defined in random_identifier()
    matched = re.match(
        r"^intelligence-layer-ci-[a-zA-Z0-9]{10}-(?P<timestamp>\d{8}T\d{6})$",
        identifier,
    )
    if matched is None:
        return False

    timestamp = datetime.strptime(matched["timestamp"], "%Y%m%dT%H%M%S").replace(
        tzinfo=timezone.utc
    )
    return not timestamp > timestamp_threshold


def random_semantic_embed() -> EmbeddingConfig:
    return SemanticEmbed(
        representation=random.choice(get_args(Representation)),
        model_name="luminous-base",
    )


def random_instructable_embed() -> EmbeddingConfig:
    return InstructableEmbed(
        model_name="pharia-1-embedding-4608-control",
        query_instruction=random_alphanumeric_string(),
        document_instruction=random_alphanumeric_string(),
    )


def random_embedding_config() -> EmbeddingConfig:
    return random.choice([random_semantic_embed(), random_instructable_embed()])


@fixture
def document_contents() -> DocumentContents:
    text = """John Stith Pemberton, the inventor of the world-renowned beverage Coca-Cola, was a figure whose life was marked by creativity, entrepreneurial spirit, and the turbulent backdrop of 19th-century America. Born on January 8, 1831, in Knoxville, Georgia, Pemberton grew up in an era of profound transformation and change.

Pemberton began his professional journey by studying medicine and pharmacy. After earning a degree in pharmacy, he started his career as a druggist in Columbus, Georgia. He was known for his keen interest in creating medicinal concoctions and was well-respected in his community. His early creations included various medicines and tonics, which were typical of the times when pharmacists often concocted their own remedies.

Pemberton's life took a significant turn during the American Civil War. He served as a lieutenant colonel in the Confederate Army, and it was during this period that he sustained a wound that led him to become dependent on morphine. This personal struggle with addiction likely influenced his later work in seeking out alternatives and remedies for pain relief.

In the post-war years, Pemberton relocated to Atlanta, Georgia, where he continued to experiment with various medicinal syrups and tonics. It was during this time, in the late 19th century, that he developed a beverage he initially called "Pemberton's French Wine Coca." This concoction was inspired by Vin Mariani, a popular French tonic wine that contained coca leaves. Pemberton's beverage was intended to serve not just as a refreshing drink but also as a remedy for various ailments, including morphine addiction, indigestion, and headaches.

However, in 1886, when Atlanta introduced prohibition legislation, Pemberton was compelled to create a non-alcoholic version of his beverage. He experimented with a combination of carbonated water, coca leaf extract, kola nut, and other ingredients, eventually perfecting the formula for what would soon become Coca-Cola. The name was suggested by his bookkeeper, Frank Robinson, who also created the distinctive cursive logo that is still in use today.

Pemberton advertised his new creation as a "brain tonic" and "temperance drink," asserting that it could alleviate headaches and fatigue. However, due to his declining health and financial difficulties, Pemberton was eventually compelled to sell portions of his business to various partners. Shortly before his death in 1888, he sold his remaining stake in Coca-Cola to Asa G. Candler, a fellow pharmacist and businessman.

Under Candler's leadership, Coca-Cola transformed from a pharmacist's concoction into a mass-produced and marketed beverage that became a staple of American culture and a global icon. Despite the changes and the immense growth of the brand, the legacy of John Stith Pemberton as the inventor of Coca-Cola remains an integral part of the beverage's history.

Pemberton's life story is a testament to the spirit of innovation and resilience. His creation, borne out of personal struggles and the context of his times, went on to transcend its origins and become a symbol recognized across the globe. Today, when we think of Coca-Cola, we are reminded of Pemberton's journey from a small-town pharmacist to the creator of one of the world's most enduring and beloved brands."""
    return DocumentContents(contents=[text], metadata={"Some": "Metadata"})


@fixture(scope="session")
def document_contents_with_metadata() -> list[DocumentContents]:
    text_1 = """John Stith Pemberton, the inventor of the world-renowned beverage Coca-Cola, was a figure whose life was marked by creativity, entrepreneurial spirit, and the turbulent backdrop of 19th-century America. Born on January 8, 1831, in Knoxville, Georgia, Pemberton grew up in an era of profound transformation and change."""
    text_2 = """Pemberton began his professional journey by studying medicine and pharmacy. After earning a degree in pharmacy, he started his career as a druggist in Columbus, Georgia. He was known for his keen interest in creating medicinal concoctions and was well-respected in his community. His early creations included various medicines and tonics, which were typical of the times when pharmacists often concocted their own remedies."""
    text_3 = """Pemberton's life took a significant turn during the American Civil War. He served as a lieutenant colonel in the Confederate Army, and it was during this period that he sustained a wound that led him to become dependent on morphine. This personal struggle with addiction likely influenced his later work in seeking out alternatives and remedies for pain relief."""

    metadata_1: JsonSerializable = {
        "string-field": "example_string_1",
        "option-field": None,
        "integer-field": 123,
        "float-field": 123.45,
        "boolean-field": True,
        "date-field": datetime(2022, 1, 1, tzinfo=timezone.utc)
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z"),
    }

    metadata_2: JsonSerializable = {
        "string-field": "example_string_2",
        "option-field": "example_string_2",
        "integer-field": 456,
        "float-field": 678.90,
        "boolean-field": False,
        "date-field": datetime(2023, 1, 1, tzinfo=timezone.utc)
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z"),
    }

    metadata_3: JsonSerializable = {
        "string-field": "example_string_3",
        "option-field": "example_string_3",
        "integer-field": 789,
        "float-field": 101112.13,
        "boolean-field": True,
        "date-field": datetime(2024, 1, 1, tzinfo=timezone.utc)
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z"),
    }

    return [
        DocumentContents(contents=[text_1], metadata=metadata_1),
        DocumentContents(contents=[text_2], metadata=metadata_2),
        DocumentContents(contents=[text_3], metadata=metadata_3),
    ]


@fixture(scope="session")
def document_index_namespace(document_index: DocumentIndexClient) -> Iterable[str]:
    yield "Search"
    _teardown(document_index, "Search")


@pytest_asyncio.fixture()
async def async_document_index_namespace(
    async_document_index: AsyncDocumentIndexClient,
) -> AsyncIterator[str]:
    yield "Search"
    await _async_teardown(async_document_index, "Search")


def _teardown(
    document_index: DocumentIndexClient, document_index_namespace: str
) -> Iterator[None]:
    yield

    # Cleanup leftover resources from previous runs.
    timestamp_threshold = datetime.now(timezone.utc) - timedelta(hours=1)

    collections = document_index.list_collections(document_index_namespace)
    for collection_path in collections:
        if is_outdated_identifier(collection_path.collection, timestamp_threshold):
            document_index.delete_collection(collection_path)

    indexes = document_index.list_indexes(document_index_namespace)
    for index_path in indexes:
        if is_outdated_identifier(index_path.index, timestamp_threshold):
            document_index.delete_index(index_path)

    filter_indexes = document_index.list_filter_indexes_in_namespace(
        document_index_namespace
    )
    for filter_index in filter_indexes:
        if is_outdated_identifier(filter_index, timestamp_threshold):
            document_index.delete_filter_index_from_namespace(
                document_index_namespace, filter_index
            )


async def _async_teardown(
    async_document_index: AsyncDocumentIndexClient, document_index_namespace: str
) -> None:
    # Cleanup leftover resources from previous runs.
    timestamp_threshold = datetime.now(timezone.utc) - timedelta(hours=1)
    async with async_document_index as client:
        collections = await client.list_collections(document_index_namespace)
        for collection_path in collections:
            if is_outdated_identifier(collection_path.collection, timestamp_threshold):
                await client.delete_collection(collection_path)

        indexes = await client.list_indexes(document_index_namespace)
        for index_path in indexes:
            if is_outdated_identifier(index_path.index, timestamp_threshold):
                await client.delete_index(index_path)

        filter_indexes = await client.list_filter_indexes_in_namespace(
            document_index_namespace
        )
        for filter_index in filter_indexes:
            if is_outdated_identifier(filter_index, timestamp_threshold):
                await client.delete_filter_index_from_namespace(
                    document_index_namespace, filter_index
                )


@fixture(scope="session")
def filter_index_configs(
    document_index: DocumentIndexClient,
    document_index_namespace: str,
) -> dict[str, dict[str, str]]:
    configs = {
        random_identifier(): {
            "field-name": "string-field",
            "field-type": "string",
        },
        random_identifier(): {
            "field-name": "option-field",
            "field-type": "string",
        },
        random_identifier(): {
            "field-name": "integer-field",
            "field-type": "integer",
        },
        random_identifier(): {
            "field-name": "float-field",
            "field-type": "float",
        },
        random_identifier(): {
            "field-name": "boolean-field",
            "field-type": "boolean",
        },
        random_identifier(): {
            "field-name": "date-field",
            "field-type": "date_time",
        },
    }

    for name, config in configs.items():
        document_index.create_filter_index_in_namespace(
            namespace=document_index_namespace,
            filter_index_name=name,
            field_name=config["field-name"],
            field_type=config["field-type"],  # type:ignore[arg-type]
        )

    return configs


@pytest_asyncio.fixture()
async def async_filter_index_configs(
    async_document_index: AsyncDocumentIndexClient,
    async_document_index_namespace: str,
) -> dict[str, dict[str, str]]:
    configs = {
        random_identifier(): {
            "field-name": "string-field",
            "field-type": "string",
        },
        random_identifier(): {
            "field-name": "option-field",
            "field-type": "string",
        },
        random_identifier(): {
            "field-name": "integer-field",
            "field-type": "integer",
        },
        random_identifier(): {
            "field-name": "float-field",
            "field-type": "float",
        },
        random_identifier(): {
            "field-name": "boolean-field",
            "field-type": "boolean",
        },
        random_identifier(): {
            "field-name": "date-field",
            "field-type": "date_time",
        },
    }

    for name, config in configs.items():
        await async_document_index.create_filter_index_in_namespace(
            namespace=async_document_index_namespace,
            filter_index_name=name,
            field_name=config["field-name"],
            field_type=config["field-type"],  # type:ignore[arg-type]
        )
    return configs


@contextmanager
def random_index_with_embedding_config(
    document_index: DocumentIndexClient,
    document_index_namespace: str,
    embedding_config: EmbeddingConfig,
) -> Iterator[tuple[IndexPath, IndexConfiguration]]:
    name = random_identifier()

    chunk_size, chunk_overlap = sorted(
        random.sample([0, 32, 64, 128, 256, 512, 1024], 2), reverse=True
    )

    hybrid_index_choices: list[HybridIndex] = ["bm25", None]
    hybrid_index = random.choice(hybrid_index_choices)

    index = IndexPath(namespace=document_index_namespace, index=name)
    index_configuration = IndexConfiguration(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        hybrid_index=hybrid_index,
        embedding=embedding_config,
    )
    try:
        document_index.create_index(index, index_configuration)
        yield index, index_configuration
    finally:
        document_index.delete_index(index)


@asynccontextmanager
async def async_random_index_with_embedding_config(
    async_document_index: AsyncDocumentIndexClient,
    async_document_index_namespace: str,
    embedding_config: EmbeddingConfig,
) -> AsyncIterator[tuple[IndexPath, IndexConfiguration]]:
    name = random_identifier()

    chunk_size, chunk_overlap = sorted(
        random.sample([0, 32, 64, 128, 256, 512, 1024], 2), reverse=True
    )

    hybrid_index_choices: list[HybridIndex] = ["bm25", None]
    hybrid_index = random.choice(hybrid_index_choices)

    index = IndexPath(namespace=async_document_index_namespace, index=name)
    index_configuration = IndexConfiguration(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        hybrid_index=hybrid_index,
        embedding=embedding_config,
    )
    try:
        await async_document_index.create_index(index, index_configuration)
        yield index, index_configuration
    finally:
        await async_document_index.delete_index(index)


@fixture
def random_instructable_index(
    document_index: DocumentIndexClient, document_index_namespace: str
) -> Iterator[tuple[IndexPath, IndexConfiguration]]:
    with random_index_with_embedding_config(
        document_index, document_index_namespace, random_instructable_embed()
    ) as index:
        yield index


@pytest_asyncio.fixture()
async def async_random_instructable_index(
    async_document_index: AsyncDocumentIndexClient, async_document_index_namespace: str
) -> AsyncIterator[tuple[IndexPath, IndexConfiguration]]:
    async with async_random_index_with_embedding_config(
        async_document_index,
        async_document_index_namespace,
        random_instructable_embed(),
    ) as index:
        yield index


@fixture
def random_semantic_index(
    document_index: DocumentIndexClient, document_index_namespace: str
) -> Iterator[tuple[IndexPath, IndexConfiguration]]:
    with random_index_with_embedding_config(
        document_index, document_index_namespace, random_semantic_embed()
    ) as index:
        yield index


@pytest_asyncio.fixture()
async def async_random_semantic_index(
    async_document_index: AsyncDocumentIndexClient, async_document_index_namespace: str
) -> AsyncIterator[tuple[IndexPath, IndexConfiguration]]:
    async with async_random_index_with_embedding_config(
        async_document_index, async_document_index_namespace, random_semantic_embed()
    ) as index:
        yield index


@fixture
def random_index(
    document_index: DocumentIndexClient, document_index_namespace: str
) -> Iterator[tuple[IndexPath, IndexConfiguration]]:
    with random_index_with_embedding_config(
        document_index,
        document_index_namespace,
        random.choice([random_semantic_embed(), random_instructable_embed()]),
    ) as index:
        yield index


@pytest_asyncio.fixture()
async def async_random_index(
    async_document_index: AsyncDocumentIndexClient, async_document_index_namespace: str
) -> AsyncIterator[tuple[IndexPath, IndexConfiguration]]:
    async with async_random_index_with_embedding_config(
        async_document_index,
        async_document_index_namespace,
        random.choice([random_semantic_embed(), random_instructable_embed()]),
    ) as index:
        yield index


@fixture
def random_collection(
    document_index: DocumentIndexClient,
    document_index_namespace: str,
) -> Iterator[CollectionPath]:
    collection_name = random_identifier()
    collection_path = CollectionPath(
        namespace=document_index_namespace, collection=collection_name
    )
    try:
        document_index.create_collection(collection_path)

        yield collection_path
    finally:
        document_index.delete_collection(collection_path)


@pytest_asyncio.fixture()
async def async_random_collection(
    async_document_index: AsyncDocumentIndexClient,
    async_document_index_namespace: str,
) -> AsyncIterator[CollectionPath]:
    collection_name = random_identifier()
    collection_path = CollectionPath(
        namespace=async_document_index_namespace, collection=collection_name
    )
    try:
        await async_document_index.create_collection(collection_path)
        yield collection_path
    finally:
        await async_document_index.delete_collection(collection_path)


def _add_documents_to_document_index(
    document_index: DocumentIndexClient,
    documents: list[DocumentContents],
    index_name: str,
    collection_path: CollectionPath,
):
    # Add all documents
    for i, content in enumerate(documents):
        document_index.add_document(
            DocumentPath(
                collection_path=collection_path,
                document_name=f"document-{i}",
            ),
            content,
        )

    # Ensure documents are searchable; this allows time for indexing
    @retry
    def search() -> None:
        search_result = document_index.search(
            collection_path,
            index_name,
            SearchQuery(
                query="Coca-Cola",
            ),
        )
        assert len(search_result) > 0

    search()


async def _async_add_documents_to_document_index(
    async_document_index: AsyncDocumentIndexClient,
    documents: list[DocumentContents],
    index_name: str,
    collection_path: CollectionPath,
):
    # Add all documents
    for i, content in enumerate(documents):
        await async_document_index.add_document(
            DocumentPath(
                collection_path=collection_path,
                document_name=f"document-{i}",
            ),
            content,
        )

    # Ensure documents are searchable; this allows time for indexing
    @async_retry
    async def search() -> None:
        search_result = await async_document_index.search(
            collection_path,
            index_name,
            SearchQuery(
                query="Coca-Cola",
            ),
        )
        assert len(search_result) > 0

    await search()


@fixture(scope="session")
def read_only_populated_collection(
    document_index: DocumentIndexClient,
    document_index_namespace: str,
    document_contents_with_metadata: list[DocumentContents],
    filter_index_configs: dict[str, dict[str, str]],
) -> Iterator[tuple[CollectionPath, IndexPath]]:
    index_name = random_identifier()
    index_path = IndexPath(namespace=document_index_namespace, index=index_name)
    index_configuration = IndexConfiguration(
        chunk_size=512,
        chunk_overlap=0,
        hybrid_index="bm25",
        embedding=SemanticEmbed(
            representation="asymmetric",
            model_name="luminous-base",
        ),
    )

    collection_name = random_identifier()
    collection_path = CollectionPath(
        namespace=document_index_namespace, collection=collection_name
    )

    try:
        document_index.create_collection(collection_path)
        document_index.create_index(index_path, index_configuration)
        document_index.assign_index_to_collection(collection_path, index_name)

        for name in filter_index_configs:
            document_index.assign_filter_index_to_search_index(
                collection_path=collection_path,
                index_name=index_name,
                filter_index_name=name,
            )
        _add_documents_to_document_index(
            document_index, document_contents_with_metadata, index_name, collection_path
        )

        yield collection_path, index_path
    finally:
        document_index.delete_collection(collection_path)

        @retry
        def clean_up_indexes() -> None:
            document_index.delete_index(index_path)
            for filter_index_name in filter_index_configs:
                document_index.delete_filter_index_from_namespace(
                    document_index_namespace, filter_index_name
                )

        clean_up_indexes()


@pytest_asyncio.fixture()
async def async_read_only_populated_collection(
    async_document_index: AsyncDocumentIndexClient,
    async_document_index_namespace: str,
    document_contents_with_metadata: list[DocumentContents],
    async_filter_index_configs: dict[str, dict[str, str]],
) -> AsyncIterator[tuple[CollectionPath, IndexPath]]:
    async with async_document_index as client:
        collection_name = random_identifier()
        collection_path = CollectionPath(
            namespace=async_document_index_namespace, collection=collection_name
        )
        index_name = random_identifier()
        index_path = IndexPath(
            namespace=async_document_index_namespace, index=index_name
        )
        index_configuration = IndexConfiguration(
            chunk_size=512,
            chunk_overlap=0,
            hybrid_index="bm25",
            embedding=SemanticEmbed(
                representation="asymmetric",
                model_name="luminous-base",
            ),
        )
        try:
            await client.create_collection(collection_path)
            await client.create_index(index_path, index_configuration)
            await client.assign_index_to_collection(collection_path, index_name)

            for name in async_filter_index_configs:
                await client.assign_filter_index_to_search_index(
                    collection_path=collection_path,
                    index_name=index_name,
                    filter_index_name=name,
                )

            await _async_add_documents_to_document_index(
                client, document_contents_with_metadata, index_name, collection_path
            )
            yield collection_path, index_path

        finally:
            await client.delete_collection(collection_path)

            @async_retry
            async def clean_up_indexes() -> None:
                await client.delete_index(index_path)
                for filter_index_name in async_filter_index_configs:
                    await client.delete_filter_index_from_namespace(
                        async_document_index_namespace, filter_index_name
                    )

            await clean_up_indexes()


@fixture
def random_searchable_collection(
    document_index: DocumentIndexClient,
    document_contents_with_metadata: list[DocumentContents],
    random_index: tuple[IndexPath, IndexConfiguration],
    random_collection: CollectionPath,
) -> Iterator[tuple[CollectionPath, IndexPath]]:
    index_path, _ = random_index
    index_name = index_path.index
    collection_path = random_collection

    try:
        # Assign index
        document_index.assign_index_to_collection(collection_path, index_name)

        _add_documents_to_document_index(
            document_index, document_contents_with_metadata, index_name, collection_path
        )

        yield collection_path, index_path
    finally:
        document_index.delete_collection(collection_path)

        @retry
        def clean_up_index() -> None:
            document_index.delete_index(index_path)

        clean_up_index()


@pytest_asyncio.fixture()
async def async_random_searchable_collection(
    async_document_index: AsyncDocumentIndexClient,
    document_contents_with_metadata: list[DocumentContents],
    async_random_index: tuple[IndexPath, IndexConfiguration],
    async_document_index_namespace: str,
) -> AsyncIterator[tuple[CollectionPath, IndexPath]]:
    index_path, _ = async_random_index
    index_name = index_path.index
    collection_name = random_identifier()
    collection_path = CollectionPath(
        namespace=async_document_index_namespace, collection=collection_name
    )

    try:
        await async_document_index.create_collection(collection_path)
        await async_document_index.assign_index_to_collection(
            collection_path, index_name
        )

        await _async_add_documents_to_document_index(
            async_document_index,
            document_contents_with_metadata,
            index_name,
            collection_path,
        )

        yield collection_path, index_path
    finally:
        await async_document_index.delete_collection(collection_path)

        @async_retry
        async def clean_up_index() -> None:
            await async_document_index.delete_index(index_path)

        await clean_up_index()


@fixture
def document_index_retriever(
    read_only_populated_collection: tuple[CollectionPath, IndexPath],
    document_index: DocumentIndexClient,
) -> DocumentIndexRetriever:
    return DocumentIndexRetriever(
        document_index,
        index_name=read_only_populated_collection[1].index,
        namespace=read_only_populated_collection[0].namespace,
        collection=read_only_populated_collection[0].collection,
        k=2,
    )


@fixture
def async_document_index_retriever(
    async_read_only_populated_collection: tuple[CollectionPath, IndexPath],
    async_document_index: AsyncDocumentIndexClient,
) -> AsyncDocumentIndexRetriever:
    return AsyncDocumentIndexRetriever(
        async_document_index,
        index_name=async_read_only_populated_collection[1].index,
        namespace=async_read_only_populated_collection[0].namespace,
        collection=async_read_only_populated_collection[0].collection,
        k=2,
    )
