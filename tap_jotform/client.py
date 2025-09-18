"""REST client handling, including JotformStream base class."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

import requests
import requests_cache
from singer_sdk.authenticators import APIKeyAuthenticator
from singer_sdk.pagination import BaseOffsetPaginator
from singer_sdk.streams import RESTStream

if TYPE_CHECKING:
    from collections.abc import Generator

    from singer_sdk.helpers.types import Context, Record


class JotformPaginator(BaseOffsetPaginator):
    """Jotform pagination class."""


class JotformStream(RESTStream):
    """Jotform stream class."""

    page_size = 100
    primary_keys: tuple[str, ...] = ("id",)  # type: ignore[assignment]
    records_jsonpath = "$.content[*]"

    INTEGER_FIELDS: tuple[str, ...] = ()

    _requests_session: requests.Session | None

    @override
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the stream object."""
        super().__init__(*args, **kwargs)
        self._requests_session = None

    @override
    @property
    def url_base(self) -> str:
        return self.config["api_url"]

    @override
    @property
    def authenticator(self) -> APIKeyAuthenticator:
        return APIKeyAuthenticator(key="APIKEY", value=self.config["api_key"])

    @override
    def post_process(
        self,
        row: Record,
        context: Context | None = None,
    ) -> dict:
        for field in self.INTEGER_FIELDS:
            value = row.get(field)
            row[field] = int(value) if value else None
        return row

    @override
    def parse_response(
        self,
        response: requests.Response,
    ) -> Generator[dict, None, None]:
        self.logger.info(
            "Received response",
            extra={"limit_left": response.json()["limit-left"]},
        )
        yield from super().parse_response(response)

    @override
    @property
    def requests_session(self) -> requests_cache.CachedSession | requests.Session:
        if self._requests_session is None:  # type: ignore[has-type]
            if (
                self.config.get("requests_cache")
                and self.config["requests_cache"]["enabled"]
            ):
                self._requests_session = requests_cache.CachedSession(
                    **self.config["requests_cache"]["config"],
                )
            else:
                self._requests_session = requests.Session()
        return self._requests_session


class JotformPaginatedStream(JotformStream):
    """A Jotform stream with pagination."""

    @override
    def get_new_paginator(self) -> JotformPaginator:
        return JotformPaginator(0, self.page_size)

    @override
    def get_url_params(
        self,
        context: Context | None,
        next_page_token: int | None,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {"limit": self.page_size}

        starting_value = self.get_starting_timestamp(context)
        if starting_value and self.replication_key:
            self.logger.info(
                "Bookmark found %(bookmark)s",
                extra={"bookmark": starting_value},
            )
            params["filter"] = f'{{"{self.replication_key}:gt": "{starting_value}"}}'

        if next_page_token:
            params["offset"] = next_page_token

        return params

    @override
    def post_process(self, row: Record, context: Context | None = None) -> Record:
        """Post-process a record."""
        row = super().post_process(row, context)
        row["updated_at"] = row["updated_at"] or row["created_at"]
        return row
