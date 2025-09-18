"""Tests standard tap features using the built-in SDK tests library."""

from __future__ import annotations

from typing import Any

from singer_sdk.testing import get_tap_test_class

from tap_jotform.tap import TapJotform

SAMPLE_CONFIG: dict[str, Any] = {
    "requests_cache": {
        "enabled": True,
        "config": {
            "expire_after": 3600,
        },
    },
    "start_date": "2021-01-01T00:00:00Z",
    "include_deprecated_streams": False,
}


TestTapJotform = get_tap_test_class(TapJotform, config=SAMPLE_CONFIG)
