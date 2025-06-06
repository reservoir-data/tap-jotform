"""Nox configuration."""

from __future__ import annotations

import sys

import nox

cli = "tap-jotform"
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
locations = src_dir, tests_dir, "noxfile.py"
nox.needs_version = ">=2025.2.9"
nox.options.default_venv_backend = "uv"
nox.options.sessions = (
    "mypy",
    "tests",
)

UV_SYNC_COMMAND = (
    "uv",
    "sync",
    "--locked",
    "--no-dev",
)


@nox.session
def run(session: nox.Session) -> None:
    """Run the tap with request caching enabled."""
    env = {
        "UV_PROJECT_ENVIRONMENT": session.virtualenv.location,
    }
    if isinstance(session.python, str):
        env["UV_PYTHON"] = session.python

    session.run_install(
        *UV_SYNC_COMMAND,
        env=env,
    )
    session.run(
        cli,
        "--config",
        "requests_cache.config.json",
        "--config",
        "ENV",
    )


@nox.session
def mypy(session: nox.Session) -> None:
    """Check types with mypy."""
    env = {
        "UV_PROJECT_ENVIRONMENT": session.virtualenv.location,
    }
    if isinstance(session.python, str):
        env["UV_PYTHON"] = session.python

    session.run_install(
        *UV_SYNC_COMMAND,
        "--group=testing",
        "--group=typing",
        env=env,
    )
    args = session.posargs or [src_dir, tests_dir]
    session.run("mypy", *args)
    if not session.posargs:
        session.run("mypy", f"--python-executable={sys.executable}", "noxfile.py")


@nox.session(python=python_versions)
def tests(session: nox.Session) -> None:
    """Execute pytest tests and compute coverage."""
    env = {
        "UV_PROJECT_ENVIRONMENT": session.virtualenv.location,
    }
    if isinstance(session.python, str):
        env["UV_PYTHON"] = session.python

    session.run_install(
        *UV_SYNC_COMMAND,
        "--group=ci",
        "--group=testing",
        env=env,
    )
    session.run("pytest", *session.posargs)
