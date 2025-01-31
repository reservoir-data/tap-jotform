"""Jotform tap class."""

from __future__ import annotations

from importlib import metadata

from singer_sdk import Stream, Tap
from singer_sdk import typing as th

from tap_jotform import streams


def get_package_version() -> str:
    """Return the version number.

    Returns:
        The package version number.
    """
    try:
        return metadata.version(__package__)
    except metadata.PackageNotFoundError:
        return "<unknown>"


class TapJotform(Tap):
    """Singer Tap for Jotform."""

    name = "tap-jotform"

    config_jsonschema = th.PropertiesList(
        th.Property(
            "api_key",
            th.StringType,
            required=True,
            description=(
                "Authentication key. See https://api.jotform.com/docs/#authentication"
            ),
        ),
        th.Property(
            "api_url",
            th.StringType,
            required=False,
            default="https://api.jotform.com",
            description="API Base URL",
        ),
        th.Property(
            "user_agent",
            th.StringType,
            default=f"{name}/{get_package_version()}",
            description="User-Agent header",
        ),
        th.Property(
            "start_date",
            th.DateTimeType,
            required=False,
            description="Start date for data collection",
        ),
        th.Property(
            "requests_cache",
            th.ObjectType(
                th.Property(
                    "enabled",
                    th.BooleanType,
                    default=False,
                    description="Enable requests cache",
                ),
                th.Property(
                    "config",
                    th.ObjectType(
                        th.Property(
                            "expire_after",
                            th.IntegerType,
                            description="Cache expiration time in seconds",
                        ),
                    ),
                    description="Requests cache configuration",
                    default={},
                ),
            ),
            description="Cache configuration for HTTP requests",
        ),
    ).to_dict()

    def discover_streams(self) -> list[Stream]:
        """Return a list of discovered streams.

        Returns:
            A list of discovered streams.
        """
        return [
            streams.FormsStream(self),
            streams.QuestionsStream(self),
            streams.SubmissionsStream(self),
            streams.ReportsStream(self),
            streams.UserHistory(self),
            streams.FoldersStream(self),
        ]
