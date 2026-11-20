"""Assertions shared by the browser scenarios."""

import re

from playwright.sync_api import Page, expect
from pytest_bdd import parsers, then

from .utils import wait_until_mounted


@then(parsers.cfparse('I should see the text "{text}"'))
def should_see_text(text: str, page: Page):
    expect(page.get_by_text(text).first).to_be_visible()


@then(parsers.cfparse('I should not see the text "{text}"'))
def should_not_see_text(text: str, page: Page):
    expect(page.get_by_text(text)).to_have_count(0)


@then(parsers.cfparse('I should see "{testid}"'))
def should_see_testid(testid: str, page: Page):
    expect(page.get_by_test_id(testid).first).to_be_visible()


@then(parsers.cfparse('I should not see "{testid}"'))
def should_not_see_testid(testid: str, page: Page):
    expect(page.get_by_test_id(testid)).to_have_count(0)


def _url_pattern(fragment: str) -> re.Pattern[str]:
    return re.compile(f".*{re.escape(fragment)}.*")


@then(parsers.cfparse('I should be at a URL with "{fragment}"'))
def at_url_with(fragment: str, page: Page):
    expect(page).to_have_url(_url_pattern(fragment))


@then(parsers.cfparse('I should not be at a URL with "{fragment}"'))
def not_at_url_with(fragment: str, page: Page):
    expect(page).not_to_have_url(_url_pattern(fragment))


@then(parsers.cfparse('I should not see the "{name}" tab'))
def should_not_see_tab(name: str, page: Page):
    expect(page.get_by_role("tab", name=name)).to_have_count(0)


@then(parsers.cfparse('the stat "{title}" should show "{value}"'))
def stat_should_show(title: str, value: str, page: Page):
    expect(page.get_by_test_id(f"stat {title}")).to_contain_text(value)


@then(parsers.cfparse('the "{testid}" field should be masked'))
def field_should_be_masked(testid: str, page: Page):
    # Element Plus puts data-testid on the native input. A wrapper would keep
    # the input inside it. Resolve either shape on every retry: reading
    # count() once would keep asserting the wrapper after the input appears.
    field = page.get_by_test_id(testid)
    control = field.locator("xpath=self::input | .//input")
    expect(control).to_have_attribute("type", "password")


@then(parsers.cfparse('"{testid}" should be off'))
def switch_should_be_off(testid: str, page: Page):
    # Element Plus puts data-testid on the switch root and aria-checked on the
    # inner checkbox. Vue removes the attribute when the value is boolean
    # false, so the off state is an unchecked box, not aria-checked="false".
    switch = page.get_by_test_id(testid)
    control = switch.locator("xpath=self::input | .//input[@type='checkbox']")
    expect(control).not_to_be_checked()


@then("there should be no console errors")
def no_console_errors(browser_console):
    errors = [message.text for message in browser_console if message.type == "error"]
    assert errors == [], errors


@then(parsers.cfparse('the page should match the "{name}" snapshot'))
def match_snapshot(name: str, page: Page, assert_snapshot):
    wait_until_mounted(page)
    page.set_viewport_size({"width": 1280, "height": 720})
    image = page.screenshot(animations="disabled")
    difference = assert_snapshot(image, f"{name}-1280x720.png")
    assert difference is None, f"Visual difference for {name}"
