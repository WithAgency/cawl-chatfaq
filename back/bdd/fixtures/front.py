"""Start Django and the Nuxt apps under test."""

import json
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
ADMIN_DIR = REPO_ROOT / "admin"
WIDGET_DIR = REPO_ROOT / "widget"


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def _install_front(directory: Path, env: dict) -> None:
    # An empty node_modules still counts as existing. Install until the
    # Nuxt binary the build script runs is actually there.
    if (directory / "node_modules" / ".bin" / "nuxt").exists():
        return
    # Admin's postinstall runs `nuxt prepare`, which reads these variables.
    install_env = {**os.environ, **env}
    if (directory / "pnpm-lock.yaml").exists():
        # pnpm 12 exits when a dependency build is not on the allow list.
        # esbuild and @parcel/watcher need those scripts for the Nuxt build.
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
        subprocess.run(["npm", "install"], cwd=directory, check=True, env=install_env)


def _build_front(directory: Path, env: dict) -> None:
    if os.environ.get("SKIPBUILD", "0") == "1":
        logger.info("Skipping the front build for %s", directory)
        return
    _install_front(directory, env)
    logger.info("Building %s", directory)
    subprocess.run(
        ["npm", "run", "build"],
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


def _proxy_major(directory: Path) -> int | None:
    """Version actually imported by the built server, not another copy nearby."""
    package = (
        directory
        / ".output"
        / "server"
        / "node_modules"
        / "http-proxy-middleware"
        / "package.json"
    )
    if not package.is_file():
        return None
    version = json.loads(package.read_text()).get("version", "")
    try:
        return int(str(version).split(".", 1)[0])
    except ValueError:
        return None


def _adapt_proxy_call(directory: Path) -> None:
    """@model-w/proxy calls createProxyMiddleware(filter, options). That is the
    v2 signature. v3 accepts only an options object and exits on the v2 call.
    The admin tree contains both versions; rewrite the call only when the
    built server resolved v3. Applying it to v2 makes the context "/" and
    proxies every page, including /login.
    """
    if _proxy_major(directory) != 3:
        return
    bundle = directory / ".output" / "server" / "chunks" / "nitro" / "nitro.mjs"
    if not bundle.is_file():
        return
    old = (
        "const proxy = createProxyMiddleware(\n"
        "  // @ts-ignore\n"
        "  (pathname, req) => shouldUseProxy(req.headers, req.method, pathname),\n"
        "  proxyOptions\n"
        ");"
    )
    new = (
        "const proxy = createProxyMiddleware({\n"
        "  ...proxyOptions,\n"
        "  pathFilter: (pathname, req) => shouldUseProxy(req.headers, req.method, pathname),\n"
        "});"
    )
    text = bundle.read_text()
    if old not in text:
        return
    bundle.write_text(text.replace(old, new, 1))


def _serve(directory: Path, env: dict, ready_path: str) -> Generator[str, None, None]:
    _adapt_proxy_call(directory)
    port = _free_port()
    server_env = {
        **os.environ,
        **env,
        "PORT": str(port),
        "NITRO_PORT": str(port),
        "NITRO_HOST": "127.0.0.1",
        "HOST": "127.0.0.1",
    }
    process = subprocess.Popen(
        ["node", ".output/server/index.mjs"],
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
        yield url.rstrip("/")
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
        "NUXT_API_URL": live_server.url,
        "NUXT_PROXY_OPTIONS_TARGET": live_server.url,
        "API_URL": live_server.url,
        "NUXT_PUBLIC_CHATFAQ_API": live_server.url,
        "NUXT_PUBLIC_CHATFAQ_WS": "ws://127.0.0.1:9",
    }


@pytest.fixture(scope="session")
def front_server(api_env) -> Generator[str, None, None]:
    """Built admin. Set FRONTURL to point at an already running admin."""
    if address := os.environ.get("FRONTURL"):
        yield address.rstrip("/")
        return
    _build_front(ADMIN_DIR, api_env)
    yield from _serve(ADMIN_DIR, api_env, "/login")


@pytest.fixture(scope="session")
def widget_server(api_env) -> Generator[str, None, None]:
    """Built widget demo. Set WIDGETURL to point at an already running widget."""
    if address := os.environ.get("WIDGETURL"):
        yield address.rstrip("/")
        return
    _build_front(WIDGET_DIR, api_env)
    yield from _serve(WIDGET_DIR, api_env, "/demo/")


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
