"""Preconditions shared by the admin scenarios."""

import httpx
from django.contrib.auth import get_user_model
from playwright.sync_api import Page, expect
from pytest_bdd import given, parsers, when

from .utils import fill_testid, wait_until_mounted

LOGIN_EMAIL = "ada@chatfaq.test"
LOGIN_PASSWORD = "correct"

PAGES = {
    "home": "",
    "login": "login",
    "dashboard": "",
    "labeling": "labeling",
    "data": "data",
    "AI config": "ai_config",
    "widget config": "widget_config",
    "stats": "stats",
    "user management": "user_management",
}


def ensure_admin_user():
    user_model = get_user_model()
    user, _created = user_model.objects.get_or_create(
        email=LOGIN_EMAIL,
        defaults={"first_name": "Ada", "last_name": "Lovelace"},
    )
    user.first_name = "Ada"
    user.last_name = "Lovelace"
    # The user list and user creation endpoints allow staff only.
    user.is_staff = True
    user.set_password(LOGIN_PASSWORD)
    user.save()
    return user


def open_page(page_name: str, page: Page, front_server: str) -> None:
    name = page_name.strip("/")
    path = PAGES.get(name, name)
    page.goto(str(httpx.URL(front_server).join(f"/{path}")))
    # The server HTML is ready before Svelte mounts. Filling or clicking earlier
    # hits controls that do not have their listeners yet.
    wait_until_mounted(page)


@given("the admin user exists")
def admin_user_exists():
    ensure_admin_user()


@given("I am logged in")
def logged_in(page: Page, front_server: str):
    ensure_admin_user()
    open_page("login", page, front_server)
    fill_testid(page, "email", LOGIN_EMAIL)
    fill_testid(page, "password", LOGIN_PASSWORD)
    page.get_by_test_id("login").click()
    expect(page.get_by_text("Welcome, Ada")).to_be_visible()
    # The welcome text is in the server HTML, before the menu is painted.
    wait_until_mounted(page)


@given(parsers.cfparse("I am on the {page_name} page"))
@when(parsers.cfparse("I am on the {page_name} page"))
def on_page(page_name: str, page: Page, front_server: str):
    open_page(page_name, page, front_server)
