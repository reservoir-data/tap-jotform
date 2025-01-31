"""REST client handling, including JotformStream base class."""

from __future__ import annotations

import typing as t

import requests
import requests_cache
from singer_sdk.authenticators import APIKeyAuthenticator
from singer_sdk.pagination import BaseOffsetPaginator
from singer_sdk.streams import RESTStream

if t.TYPE_CHECKING:
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

    def __init__(self, *args: t.Any, **kwargs: t.Any) -> None:
        """Initialize the stream object."""
        super().__init__(*args, **kwargs)
        self._requests_session = None

    @property
    def url_base(self) -> str:
        """Return the API URL root, configurable via tap settings.

        Returns:
            The API URL root.
        """
        return self.config["api_url"]

    @property
    def authenticator(self) -> APIKeyAuthenticator:
        """Return a new authenticator object.

        Returns:
            An authenticator instance.
        """
        return APIKeyAuthenticator.create_for_stream(
            self,
            key="APIKEY",
            value=self.config["api_key"],
            location="header",
        )

    @property
    def http_headers(self) -> dict:
        """Return the http headers needed.

        Returns:
            A dictionary of headers.
        """
        headers = {}
        if "user_agent" in self.config:
            headers["User-Agent"] = self.config.get("user_agent")
        return headers

    def post_process(
        self,
        row: Record,
        context: Context | None = None,  # noqa: ARG002
    ) -> dict:
        """Post-process a record.

        Args:
            row: The record to post-process.
            context: The context object.

        Returns:
            The post-processed record.
        """
        for field in self.INTEGER_FIELDS:
            value = row.get(field)
            row[field] = int(value) if value else None
        return row

    def parse_response(
        self,
        response: requests.Response,
    ) -> t.Generator[dict, None, None]:
        """Parse the response and return an iterator of result rows.

        Args:
            response: The response object.

        Yields:
            An iterator of parsed records.
        """
        self.logger.info(
            "Received response",
            extra={"limit_left": response.json()["limit-left"]},
        )
        yield from super().parse_response(response)

    @property
    def requests_session(self) -> requests_cache.CachedSession | requests.Session:
        """Return a new requests session object.

        Returns:
            A new requests session object.
        """
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

    def get_new_paginator(self) -> JotformPaginator:
        """Return a new instance of a paginator.

        Returns:
            A new instance of a paginator.
        """
        return JotformPaginator(0, self.page_size)

    def get_url_params(
        self,
        context: Context | None,
        next_page_token: int | None,
    ) -> dict[str, t.Any]:
        """Return a dictionary of values to be used in URL parameterization.

        Args:
            context: The context object.
            next_page_token: The next page token.

        Returns:
            A dictionary of values to be used in URL parameterization.
        """
        params: dict[str, t.Any] = {"limit": self.page_size}

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

    def post_process(self, row: Record, context: Context | None = None) -> Record:
        """Post-process a record.

        Args:
            row: The record to post-process.
            context: The context object.

        Returns:
            The post-processed record.
        """
        row = super().post_process(row, context)
        row["updated_at"] = row["updated_at"] or row["created_at"]
        return row
