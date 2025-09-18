"""Jotform tap class."""

from __future__ import annotations

from typing import override

from singer_sdk import Stream, Tap
from singer_sdk import typing as th

from tap_jotform import streams


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
        th.Property(
            "include_deprecated_streams",
            th.BooleanType,
            default=True,
            description="Whether to include deprecated streams",
        ),
    ).to_dict()

    @override
    def discover_streams(self) -> list[Stream]:
        all_streams: list[Stream] = [
            streams.FormsStream(self),
            streams.QuestionsStream(self),
            streams.SubmissionsStream(self),
            streams.ReportsStream(self),
            streams.UserHistory(self),
            streams.LabelsStream(self),
        ]
        if self.config.get("include_deprecated_streams"):
            all_streams.extend(
                [
                    streams.FoldersStream(self),
                ]
            )
        return all_streams
