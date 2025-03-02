"""Stream type classes for tap-jotform."""

from __future__ import annotations

import json
import typing as t

from singer_sdk import typing as th  # JSON Schema typing helpers
from singer_sdk.helpers._typing import TypeConformanceLevel

from tap_jotform.client import JotformPaginatedStream, JotformStream

if t.TYPE_CHECKING:
    import requests
    from singer_sdk.helpers.types import Context, Record

CREATED_AT = th.Property("created_at", th.DateTimeType)
UPDATED_AT = th.Property("updated_at", th.DateTimeType)


class FormsStream(JotformPaginatedStream):
    """Forms stream."""

    name = "forms"
    path = "/user/forms"

    INTEGER_FIELDS = (
        "height",
        "new",
        "count",
        "favorite",
        "archived",
    )

    schema = th.PropertiesList(
        th.Property("id", th.StringType, description="The Form ID"),
        th.Property("username", th.StringType),
        th.Property("title", th.StringType),
        th.Property("height", th.IntegerType),
        th.Property("url", th.StringType),
        th.Property(
            "status",
            th.StringType,
            allowed_values=["ENABLED", "DISABLED", "DELETED"],
        ),
        CREATED_AT,
        UPDATED_AT,
        th.Property("last_submission", th.DateTimeType),
        th.Property(
            "new",
            th.IntegerType,
            description="Total number of unread submissions",
        ),
        th.Property(
            "count",
            th.IntegerType,
            description="Total number of submissions",
        ),
        th.Property("type", th.StringType, allowed_values=["LEGACY", "CARD"]),
        th.Property("favorite", th.IntegerType),
        th.Property("archived", th.IntegerType),
    ).to_dict()

    def get_child_context(
        self,
        record: Record,
        context: Context | None,  # noqa: ARG002
    ) -> dict:
        """Return a context dictionary for child streams.

        Args:
            record: The record being processed.
            context: The context dictionary for the parent stream.

        Returns:
            A context dictionary for child streams.
        """
        return {"form_id": record["id"]}


class QuestionsStream(JotformStream):
    """Questions stream."""

    INTEGER_FIELDS = ("order",)

    name = "questions"
    path = "/form/{form_id}/questions"
    primary_keys = ("form_id", "qid")
    replication_key = None
    parent_stream_type = FormsStream

    schema = th.PropertiesList(
        th.Property("qid", th.StringType, required=True, description="Question ID"),
        th.Property("form_id", th.StringType, required=True, description="Form ID"),
        th.Property(
            "type",
            th.StringType,
            required=True,
            description="Question type such as textbox or dropdown",
        ),
        th.Property(
            "order",
            th.IntegerType,
            required=True,
            description="Question order in the form",
        ),
        th.Property(
            "question",
            th.ObjectType(),
            required=True,
            description="Question data",
        ),
    ).to_dict()

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
        for qid, question in response.json()["content"].items():
            yield {
                "qid": qid,
                "type": question["type"],
                "order": question["order"],
                "question": question,
            }


class SubmissionsStream(JotformPaginatedStream):
    """Submissions stream."""

    name = "submissions"
    path = "/user/submissions"

    INTEGER_FIELDS = (
        "flag",
        "new",
    )

    schema = th.PropertiesList(
        th.Property("id", th.StringType, description="The Submission ID"),
        th.Property("form_id", th.StringType),
        th.Property("ip", th.StringType),
        th.Property("flag", th.IntegerType),
        th.Property("notes", th.StringType),
        CREATED_AT,
        UPDATED_AT,
        th.Property(
            "status",
            th.StringType,
            allowed_values=["ACTIVE", "OVERQUOTA", "DELETED", "ARCHIVED", "CUSTOM"],
        ),
        th.Property(
            "new",
            th.IntegerType,
            description="Total number of unread submissions",
        ),
        th.Property(
            "answers",
            th.ArrayType(
                th.ObjectType(
                    th.Property("qid", th.StringType, required=True),
                    th.Property("answer", th.StringType, deprecated=True),
                    th.Property(
                        "answer_object",
                        th.CustomType(
                            {
                                "type": [
                                    "object",
                                    "array",
                                    "integer",
                                    "number",
                                    "boolean",
                                    "string",
                                    "null",
                                ]
                            },
                        ),
                        description="The answer object",
                    ),
                ),
            ),
        ),
    ).to_dict()

    def post_process(self, row: Record, context: Context | None = None) -> Record:
        """Post-process a row.

        Args:
            row: The row of data.
            context: The context object.

        Returns:
            The processed row of data.
        """
        row = super().post_process(row, context)

        answers_list = []
        answers: dict[str, dict[str, str | None]] = row.pop("answers", {})
        for qid, entry in answers.items():
            answer = entry.get("answer")
            entry["answer"] = json.dumps(answer) if answer is not None else None
            entry["answer_object"] = answer
            value: dict[str, str | None] = {"qid": qid, **entry}
            answers_list.append(value)
        row["answers"] = answers_list

        return row


class ReportsStream(JotformStream):
    """Reports stream."""

    name = "reports"
    path = "/user/reports"

    schema = th.PropertiesList(
        th.Property("id", th.StringType, description="The Report ID"),
        th.Property("form_id", th.StringType),
        th.Property("title", th.StringType),
        CREATED_AT,
        UPDATED_AT,
        th.Property("fields", th.ArrayType(th.StringType)),
        th.Property(
            "list_type",
            th.StringType,
            allowed_values=[
                "excel",
                "csv",
                "grid",
                "table",
                "calendar",
                "rss",
                "visual",
            ],
        ),
        th.Property("status", th.StringType, allowed_values=["ENABLED", "DELETED"]),
        th.Property("url", th.StringType),
        th.Property("isProtected", th.BooleanType),
        th.Property("type", th.StringType),
        th.Property("form_title", th.StringType),
        th.Property("form_count", th.IntegerType),
        th.Property("form_url", th.StringType),
        th.Property("last_submission", th.DateTimeType),
    ).to_dict()

    def post_process(self, row: Record, context: Context | None = None) -> Record:
        """Post-process a row of data.

        Args:
            row: The row of data.
            context: The context object.

        Returns:
            The processed row of data.
        """
        row = super().post_process(row, context)
        fields = row.get("fields") or ""
        row["fields"] = fields.split(",")
        return row


class UserHistory(JotformStream):
    """User History stream."""

    name = "user_history"
    path = "/user/history"
    primary_keys = ("username", "timestamp", "type")

    schema = th.PropertiesList(
        th.Property(
            "type",
            th.StringType,
            allowed_values=[
                "userCreation",
                "userLogin",
                "userLogout",
                "formCreation",
                "formUpdate",
                "formDelete",
                "formPurge",
                "lastUpdate",
                "passwordChanged",
                "portalCreated",
                "portalUpdated",
                "reportCreated",
                "reportUpdated",
                "submissionDeleteAll",
            ],
        ),
        th.Property("username", th.StringType),
        th.Property("ip", th.StringType),
        th.Property("server", th.StringType),
        th.Property("timestamp", th.IntegerType),
        th.Property("email", th.StringType),
        th.Property("parent", th.StringType),
        th.Property("subuser", th.StringType),
    ).to_dict()

    def get_url_params(
        self,
        context: Context | None,  # noqa: ARG002
        next_page_token: t.Any | None,  # noqa: ANN401, ARG002
    ) -> dict[str, t.Any] | str:
        """Get the URL parameters.

        Args:
            context: The context object.
            next_page_token: The next page token.

        Returns:
            The URL parameters.
        """
        return {
            "action": "all",
            "date": "lastWeek",
            "sortBy": "ASC",
        }


class FoldersStream(JotformStream):
    """Folders stream."""

    name = "folders"
    path = "/user/folders"
    primary_keys = ("id",)

    INTEGER_FIELDS = (
        "new",
        "count",
        "favorite",
        "archived",
        "height",
    )
    TYPE_CONFORMANCE_LEVEL = TypeConformanceLevel.ROOT_ONLY

    schema = th.PropertiesList(
        th.Property("id", th.StringType),
        th.Property("path", th.StringType),
        th.Property("owner", th.StringType),
        th.Property("name", th.StringType),
        th.Property("parent", th.StringType),
        th.Property("color", th.StringType),
        th.Property(
            "forms",
            th.ObjectType(
                additional_properties=th.ObjectType(
                    th.Property("id", th.StringType),
                    th.Property("username", th.StringType),
                    th.Property("title", th.StringType),
                    th.Property("height", th.IntegerType),
                    th.Property("status", th.StringType),
                    CREATED_AT,
                    UPDATED_AT,
                    th.Property("last_submission", th.DateTimeType),
                    th.Property("new", th.IntegerType),
                    th.Property("count", th.IntegerType),
                    th.Property("type", th.StringType),
                    th.Property("favorite", th.IntegerType),
                    th.Property("archived", th.IntegerType),
                    th.Property("url", th.StringType),
                ),
            ),
        ),
        th.Property("subfolders", th.ArrayType(th.ObjectType())),
    ).to_dict()

    def post_process(self, row: Record, context: Context | None = None) -> Record:
        """Post-process a row of data."""
        forms = {
            form_id: JotformStream.post_process(self, form, context)
            for form_id, form in row.pop("forms", {}).items()
        }
        row["forms"] = forms
        return row
