"""Nox configuration."""

from __future__ import annotations

import os
import sys
from textwrap import dedent

import nox

try:
    from nox_poetry import Session, session
except ImportError:
    message = f"""\
    Nox failed to import the 'nox-poetry' package.
    Please install it using the following command:
    {sys.executable} -m pip install nox-poetry"""
    raise SystemExit(dedent(message)) from None

package = "tap-jotform"
src_dir = "tap_jotform"
tests_dir = "tests"

python_versions = [
    "3.14",
    "3.13",
    "3.12",
    "3.11",
    "3.10",
    "3.9",
]
main_python_version = "3.12"
locations = src_dir, tests_dir, "noxfile.py"
nox.options.sessions = (
    "mypy",
    "tests",
)


@session(python=main_python_version)
def run(session: Session) -> None:
    """Run the tap with request caching enabled."""
    session.install(".")
    session.run(
        "tap-jotform",
        "--config",
        "requests_cache.config.json",
        "--config",
        "ENV",
    )


@session(python=python_versions)
def mypy(session: Session) -> None:
    """Check types with mypy."""
    args = session.posargs or [src_dir, tests_dir]
    session.install(".")
    session.install(
        "mypy",
        "types-requests",
    )
    session.run("mypy", *args)
    if not session.posargs:
        session.run("mypy", f"--python-executable={sys.executable}", "noxfile.py")


@session(python=python_versions)
def tests(session: Session) -> None:
    """Execute pytest tests and compute coverage."""
    deps = ["pytest"]
    if "GITHUB_ACTIONS" in os.environ:
        deps.append("pytest-github-actions-annotate-failures")

    session.install(".")
    session.install(*deps)
    session.run("pytest", *session.posargs)
