"""Data created in Django for a scenario."""

import httpx
import pytest
from django.utils import timezone
from playwright.sync_api import Page
from pytest_bdd import given, parsers, when

from back.apps.broker.models.message import Conversation, Message
from back.apps.language_model.models import (
    KnowledgeBase,
    KnowledgeItem,
    LLMConfig,
    RetrieverConfig,
)
from back.apps.widget.models import Widget


@given("Ray is available")
def ray_is_available(settings):
    if not settings.USE_RAY:
        pytest.skip("Ray is disabled")


@given(parsers.cfparse('a knowledge base named "{name}" exists'))
def knowledge_base_exists(name: str, seeded: dict):
    seeded["knowledge_base"] = KnowledgeBase.objects.create(name=name, lang="en")


@given(parsers.cfparse('that knowledge base has an item titled "{title}"'))
def knowledge_item_exists(title: str, seeded: dict):
    KnowledgeItem.objects.create(
        knowledge_base=seeded["knowledge_base"],
        title=title,
        content="Nine to five",
    )


@given(parsers.cfparse('an LLM named "{name}" exists'))
def llm_exists(name: str):
    LLMConfig.objects.create(name=name, llm_name="gpt-4o", enabled=True)


@given(parsers.cfparse('a retriever named "{name}" exists'))
def retriever_exists(name: str):
    base = KnowledgeBase.objects.create(name=f"{name} base", lang="en")
    RetrieverConfig.objects.create(name=name, knowledge_base=base, enabled=True)


@given(parsers.cfparse('a widget named "{name}" exists'))
def widget_exists(name: str):
    Widget.objects.create(name=name, domain="https://example.test")


@given(parsers.cfparse('a conversation named "{name}" from "{user_id}" exists'))
def conversation_exists(name: str, user_id: str):
    conversation = Conversation.objects.create(
        platform_conversation_id=name,
        name=name,
    )
    Message.objects.create(
        conversation=conversation,
        sender={"type": "human", "id": user_id},
        send_time=timezone.now(),
        stack=[{"type": "text", "payload": {"content": name}}],
    )


@given(parsers.cfparse('a demo widget named "{name}" exists'))
def demo_widget_exists(name: str, seeded: dict):
    widget = Widget.objects.create(
        name=name,
        domain="http://127.0.0.1:*",
        title="Hello there",
        fsm_def="llm_fsm",
    )
    seeded["widget_id"] = str(widget.id)


@given("I open the widget demo")
@when("I open the widget demo")
def open_widget_demo(page: Page, widget_server: str, seeded: dict):
    # widget_server may already end in /demo. An absolute join keeps a single prefix.
    page.goto(
        str(
            httpx.URL(widget_server).join(
                f"/demo/?widget_id={seeded['widget_id']}"
            )
        )
    )
