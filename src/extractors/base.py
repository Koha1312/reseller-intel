"""Abstract base for marketplace extractors.

Every platform-specific extractor (eBay, Poshmark, Mercari, ...) implements this
interface so the rest of the pipeline (parser, storage, analytics) stays
platform-agnostic.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterator

from src.parser.schemas import RawListing


class MarketplaceExtractor(ABC):
    """Interface for pulling listings from a marketplace."""

    @property
    @abstractmethod
    def platform(self) -> str:
        """Short platform identifier, e.g. 'ebay', 'poshmark'."""

    @abstractmethod
    def search(
        self,
        query: str,
        *,
        limit: int = 50,
        offset: int = 0,
        category_id: str | None = None,
    ) -> list[RawListing]:
        """Search listings matching `query`. Returns a single page of results."""

    @abstractmethod
    def get_item(self, listing_id: str) -> RawListing:
        """Fetch a single listing's full detail by platform-native ID."""

    def iter_search(
        self,
        query: str,
        *,
        page_size: int = 50,
        max_results: int = 200,
        category_id: str | None = None,
    ) -> Iterator[RawListing]:
        """Paginated iterator yielding up to `max_results` listings.

        Default implementation calls `search` repeatedly with increasing offset.
        Subclasses can override if the platform offers cursor-based pagination.
        """
        fetched = 0
        offset = 0
        while fetched < max_results:
            page = self.search(
                query,
                limit=min(page_size, max_results - fetched),
                offset=offset,
                category_id=category_id,
            )
            if not page:
                return
            for listing in page:
                yield listing
                fetched += 1
                if fetched >= max_results:
                    return
            offset += len(page)
