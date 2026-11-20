"""Start the SvelteKit server under test, or reuse one that is already running.

docker-local launches that server itself and sets FRONTURL. Other checkouts
run pytest without that variable: this fixture then builds adapter-node and
serves it. WIDGETURL overrides the demo origin; otherwise the demo is /demo
on the same server.
"""

import os
import socket
import subprocess
import threading
import time
from collections.abc import Generator
from logging import getLogger
from pathlib import Path

import httpx
import pytest
from playwright.sync_api import ConsoleMessage, Page

logger = getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parents[3]
FRONT_DIR = REPO_ROOT / "front"


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def _install_front(directory: Path, env: dict) -> None:
    if (directory / "node_modules" / ".bin" / "vite").exists():
        return
    install_env = {**os.environ, **env}
    if (directory / "pnpm-lock.yaml").exists():
        subprocess.run(
            [
                "pnpm",
                "install",
                "--frozen-lockfile",
                "--config.dangerouslyAllowAllBuilds=true",
            ],
            cwd=directory,
            check=True,
            env=install_env,
        )
    else:
        subprocess.run(
            ["pnpm", "install", "--config.dangerouslyAllowAllBuilds=true"],
            cwd=directory,
            check=True,
            env=install_env,
        )


def _build_front(directory: Path, env: dict) -> None:
    if os.environ.get("SKIPBUILD", "0") == "1":
        logger.info("Skipping the front build for %s", directory)
        return
    _install_front(directory, env)
    logger.info("Building %s", directory)
    subprocess.run(
        ["pnpm", "run", "build"],
        cwd=directory,
        check=True,
        env={**os.environ, **env},
    )


def _wait_until_up(url: str, process: subprocess.Popen, output: list[str]) -> None:
    deadline = time.time() + 90
    while time.time() < deadline:
        if process.poll() is not None:
            raise RuntimeError(
                f"Front server exited before {url} answered.\n{''.join(output)}"
            )
        try:
            httpx.get(url, timeout=1)
            return
        except httpx.HTTPError:
            time.sleep(0.4)
    raise TimeoutError(f"{url} did not answer.\n{''.join(output)}")


def _capture(process: subprocess.Popen, output: list[str]) -> None:
    if process.stdout is None:
        return
    for line in process.stdout:
        output.append(line)


def _serve(directory: Path, env: dict, ready_path: str) -> Generator[str, None, None]:
    port = _free_port()
    server_env = {
        **os.environ,
        **env,
        "PORT": str(port),
        "HOST": "127.0.0.1",
    }
    process = subprocess.Popen(
        ["node", "build/index.js"],
        cwd=directory,
        env=server_env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    output: list[str] = []
    reader = threading.Thread(target=_capture, args=(process, output), daemon=True)
    reader.start()
    url = f"http://127.0.0.1:{port}{ready_path}"
    try:
        _wait_until_up(url, process, output)
        yield f"http://127.0.0.1:{port}"
    finally:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
        reader.join(timeout=2)
        if output:
            logger.info("Front server logs:\n%s", "".join(output))


@pytest.fixture(scope="session")
def api_env(live_server) -> dict:
    return {
        "API_URL": live_server.url,
        "PUBLIC_API_URL": live_server.url,
        "VITE_API_URL": live_server.url,
    }


@pytest.fixture(scope="session")
def front_server(api_env) -> Generator[str, None, None]:
    """Built SvelteKit server. Set FRONTURL to point at one that is already up."""
    if address := os.environ.get("FRONTURL"):
        yield address.rstrip("/")
        return
    _build_front(FRONT_DIR, api_env)
    yield from _serve(FRONT_DIR, api_env, "/login")


@pytest.fixture(scope="session")
def widget_server(api_env) -> Generator[str, None, None]:
    """Demo origin. Served on 127.0.0.1 so the widget domain check matches.

    The admin UI can use FRONTURL (the docker-local Vite server). The demo
    cannot: the seeded widget allows http://127.0.0.1:* only, and the browser
    sends that host as Referer.
    """
    if address := os.environ.get("WIDGETURL"):
        yield address.rstrip("/")
        return
    if not (FRONT_DIR / "build" / "index.js").exists():
        saved = os.environ.get("SKIPBUILD")
        os.environ["SKIPBUILD"] = "0"
        try:
            _build_front(FRONT_DIR, api_env)
        finally:
            if saved is None:
                os.environ.pop("SKIPBUILD", None)
            else:
                os.environ["SKIPBUILD"] = saved
    yield from _serve(FRONT_DIR, api_env, "/demo/")


@pytest.fixture(autouse=True)
def relaxed_hosts(settings):
    settings.ALLOWED_HOSTS = ["*"]
    settings.USE_RAY = False


@pytest.fixture(autouse=True)
def browser_console(page: Page) -> list[ConsoleMessage]:
    logs: list[ConsoleMessage] = []

    def record(message: ConsoleMessage) -> None:
        logs.append(message)

    # list.append is a builtin. Playwright 1.54 stores its wrapper on the
    # handler, and Python 3.14 refuses that on builtins.
    page.on("console", record)
    return logs
