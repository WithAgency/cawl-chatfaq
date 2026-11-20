"""Small helpers shared by the step definitions."""

from playwright.sync_api import Page


def wait_until_mounted(page: Page) -> None:
    """Wait until the menu, when this page has one, is in the document."""
    page.wait_for_function(
        "() => Boolean(document.querySelector('#__nuxt')?.__vue_app__)"
    )


def fill_testid(page: Page, testid: str, value: str) -> None:
    """Fill an Element Plus control or a contenteditable node."""
    root = page.get_by_test_id(testid)
    inner = root.locator("input, textarea, [contenteditable='true']").first
    target = inner if inner.count() else root
    target.click()
    target.fill(value)
