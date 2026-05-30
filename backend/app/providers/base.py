from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable


@dataclass
class SearchResult:
    title: str
    url: str
    snippet: str


@runtime_checkable
class LLMProvider(Protocol):
    name: str

    async def complete_json(
        self,
        *,
        system: str,
        user: str,
        temperature: float,
        max_tokens: int,
        model: str | None = None,
    ) -> dict[str, Any]: ...

    async def complete_text(
        self,
        *,
        system: str,
        user: str,
        temperature: float,
        max_tokens: int,
        model: str | None = None,
    ) -> str: ...


@runtime_checkable
class OCRProvider(Protocol):
    name: str

    async def extract_text(self, image_bytes: bytes) -> str: ...


@runtime_checkable
class SearchProvider(Protocol):
    name: str

    async def search(
        self, query: str, *, domains: list[str], max_results: int
    ) -> list[SearchResult]: ...


@runtime_checkable
class BarcodeProvider(Protocol):
    name: str

    async def lookup(self, barcode: str) -> dict[str, Any] | None: ...


@runtime_checkable
class StorageProvider(Protocol):
    name: str

    async def upload(self, *, user_id: str, scan_id: str, data: bytes, content_type: str) -> str: ...

    async def download(self, path: str) -> bytes: ...
