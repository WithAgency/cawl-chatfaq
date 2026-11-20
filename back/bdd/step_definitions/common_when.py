"""Actions shared by the browser scenarios."""

from playwright.sync_api import Page
from pytest_bdd import parsers, when

from .utils import fill_testid

LANGUAGES = {
    "en": "Language: EN",
    "es": "Lengua: ES",
    "fr": "Langue: FR",
}


@when(parsers.cfparse('I enter "{value}" in {testid}'))
def enter_value(value: str, testid: str, page: Page):
    fill_testid(page, testid, value)


@when(parsers.cfparse("I choose to {testid}"))
def choose(testid: str, page: Page):
    page.get_by_test_id(testid).click()


@when(parsers.cfparse('I open the "{name}" tab'))
def open_tab(name: str, page: Page):
    page.get_by_role("tab", name=name).click()


@when(parsers.cfparse('I choose the language "{code}"'))
def choose_language(code: str, page: Page):
    page.get_by_test_id("language").click()
    page.get_by_text(LANGUAGES[code], exact=True).click()


@when(parsers.cfparse('I search for "{value}"'))
def search_for(value: str, page: Page):
    fill_testid(page, "search Name", value)


@when(parsers.cfparse('I toggle "{testid}"'))
def toggle(testid: str, page: Page):
    with page.expect_response(
        lambda response: response.request.method == "PATCH" and response.ok
    ):
        page.get_by_test_id(testid).click()
