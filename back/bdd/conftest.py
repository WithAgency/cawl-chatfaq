"""Fixtures shared by every browser scenario."""

from pathlib import Path

import pytest
from playwright.sync_api import expect

from bdd.fixtures.front import *  # noqa: F403
from bdd.fixtures.visual_regression import *  # noqa: F403


def pytest_addoption(parser):
    parser.addoption(
        "--update-snapshots",
        action="store_true",
        default=False,
        help="Rewrite the Playwright screenshots under bdd/__snapshots__.",
    )


@pytest.fixture(scope="session")
def browser_type_launch_args(browser_type_launch_args):
    """Chromium's sandbox is blocked by Docker's default seccomp profile."""
    args = list(browser_type_launch_args.get("args", []))
    if Path("/.dockerenv").exists() and "--no-sandbox" not in args:
        args.append("--no-sandbox")
    return {**browser_type_launch_args, "args": args}


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    """Desktop viewport used by the functional scenarios and the snapshots."""
    return {
        **browser_context_args,
        "viewport": {"width": 1280, "height": 720},
    }


@pytest.fixture(autouse=True)
def expect_timeout():
    expect.set_options(timeout=15_000)


@pytest.fixture
def seeded():
    """Objects created by the scenario, shared with later steps."""
    return {}
