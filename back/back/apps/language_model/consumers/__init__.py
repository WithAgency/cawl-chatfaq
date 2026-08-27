import json
import time
import uuid
from logging import getLogger
from typing import Awaitable, Callable, Dict, List, Optional, Union

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.contrib.auth.models import AnonymousUser
from ray.serve import get_deployment_handle

from back.apps.broker.consumers.message_types import RPCMessageType
from back.apps.broker.models.message import AgentType, Conversation
from back.apps.broker.serializers.rpc import (
    RPCLLMRequestSerializer,
    RPCPromptRequestSerializer,
    RPCResponseSerializer,
    RPCRetrieverRequestSerializer,
)
from back.apps.language_model.models import (
    KnowledgeItem,
    LLMConfig,
    PromptConfig,
    RetrieverConfig,
)
from back.apps.language_model.models.enums import LLMChoices
from back.config import settings
from back.utils import WSStatusCodes
from back.utils.custom_channels import CustomAsyncConsumer

# --- START chat_rag _format_tools monkey-patch (temporary) ---
# This monkey-patch must run before importing chat_rag.llms.load_llm
import logging as _mp_logging
_mp_logger = _mp_logging.getLogger(__name__)
try:
    from chat_rag.llms import mistral_client as _mc
    from chat_rag.llms.format_tools import format_tools as _format_tools_func, Mode as _Mode
except Exception as _e:
    _mp_logger.exception("Could not import chat_rag modules for monkey-patch: %s", _e)
else:
    def _format_tools_shim(self, tools=None, tool_choice=None):
        # call upstream helper (may return list or (list, tool_choice))
        res = _format_tools_func(tools=tools, tool_choice=tool_choice, mode=_Mode.MISTRAL_TOOLS)

        # Unpack tuple if returned
        if isinstance(res, tuple) and len(res) == 2 and isinstance(res[0], list):
            tools_formatted, returned_choice = res
            if tool_choice is None:
                tool_choice = returned_choice
        else:
            tools_formatted = res

        # Normalize OpenAI-style function shapes to flat dicts with "name"
        normalized_tools = []
        for t in tools_formatted or []:
            if isinstance(t, dict):
                if "name" in t:
                    normalized_tools.append(t)
                    continue
                fn = t.get("function") if isinstance(t.get("function"), dict) else None
                if fn:
                    normalized_tools.append({
                        "name": fn.get("name"),
                        "description": fn.get("description"),
                        "parameters": fn.get("parameters"),
                    })
                    continue
            normalized_tools.append(t)

        # Validate as original code expects if tool_choice provided
        tool_names = [tool.get("name") for tool in normalized_tools if isinstance(tool, dict)]
        valid_choices = [*tool_names, "auto", "none"]
        if tool_choice is not None and tool_choice not in valid_choices:
            raise ValueError(
                f"tool_choice must be 'none', 'auto', or one of the tool names: {', '.join([str(n) for n in tool_names])}"
            )

        return normalized_tools, tool_choice

    _mc.MistralChatModel._format_tools = _format_tools_shim
    _mp_logger.info("Applied chat_rag Mistral _format_tools monkey-patch (tolerant tuple + normalized shapes)")
# --- END monkey-patch ---

from chat_rag.llms import load_llm
from chat_rag.llms.types import Content, Message, ToolResult, ToolUse

from back.apps.health.models import Event

logger = getLogger(__name__)


def format_msgs_chain_to_llm_context(msgs_chain) -> List[Message]:
    """
    Returns a list of chat_rag Message objects representing the conversation context.
    Consecutive messages coming from the same sender type are concatenated into one Message.
    The content of each Message is a list of chat_rag Content objects, which can include plain text,
    tool calls (tool_use) and tool results (tool_result).

    Parameters
    ----------
    msgs_chain :
        A list of messages in the broker format.

    Returns
    -------
    List[Message]
        A list of chat_rag Message objects with messages concatenated by sender.
    """
    aggregated_messages = []
    current_role = None  # "user" for human and "assistant" for bot
    aggregated_contents = []  # list of Content objects for the current group

    def process_stack(stack) -> List[Content]:
        """
        Process a single stack item into a list of chat_rag Content objects.
        It checks for text content, tool calls, and tool results.
        """
        contents = []
        payload = stack.get("payload", {})
        type = stack.get("type")

        # Create a text content if available.
        if type == "message" or type == "message_chunk":
            contents.append(Content(text=payload.get("content"), type="text"))

        # Check if this stack represents a tool call (tool use).
        if type == "tool_use":
            tool_use_obj = ToolUse(**payload)
            contents.append(Content(tool_use=tool_use_obj, type="tool_use"))

        # Check if this stack represents a tool result.
        if type == "tool_result":
            tool_result_obj = ToolResult(**payload)
            contents.append(Content(tool_result=tool_result_obj, type="tool_result"))

        return contents

    def process_msg(msg) -> List[Content]:
        """
        Process each broker message into a list of chat_rag Content objects by iterating over its stacks.
        """
        contents = []
        for stack in msg.stack:
            contents.extend(process_stack(stack))
        return contents

    def merge_contents(existing: List[Content], new: List[Content]) -> List[Content]:
        """
        Merge two lists of chat_rag Content objects.
        If the last element of the existing list and the first element of the new list are both text,
        then they are concatenated.
        """
        if not existing:
            return new
        if not new:
            return existing

        merged = existing.copy()
        # If the last and first items are text, merge them.
        if merged and new and merged[-1].type == "text" and new[0].type == "text":
            merged[-1].text = merged[-1].text.strip() + " " + new[0].text.strip()
            merged.extend(new[1:])
        else:
            merged.extend(new)
        return merged
    # Iterate over each message in the msgs_chain, grouping contiguous messages by sender type.
    for msg in msgs_chain:
        # Map sender type to LLM context role.
        sender_type = msg.sender.get("type")
        if sender_type == AgentType.human.value:
            role = "user"
        elif sender_type == AgentType.bot.value:
            role = "assistant"
        else:
            # Skip messages that are not from a human or bot.
            continue

        # Process the message stacks to obtain its list of Content objects.
        msg_contents = process_msg(msg)
        if not msg_contents:
            continue

        if current_role is None:
            # Start a new group.
            current_role = role
            aggregated_contents = msg_contents
        elif current_role == role:
            # Same role: merge new contents with the existing group.
            aggregated_contents = merge_contents(aggregated_contents, msg_contents)
        else:
            # Role changed, so package the current group into a Message.
            aggregated_messages.append(
                Message(
                    role=current_role,
                    content=aggregated_contents,
                    usage=None,
                    stop_reason="end_turn"
                ).model_dump()
            )
            # Start a new group for the new role.
            current_role = role
            aggregated_contents = msg_contents

    # Append any remaining aggregated messages.
    if current_role is not None and aggregated_contents:
        aggregated_messages.append(
            Message(
                role=current_role,
                content=aggregated_contents,
                usage=None,
                stop_reason="end_turn"
            ).model_dump()
        )

    return aggregated_messages


async def resolve_references(reference_kis, retriever_config):
    # ColBERT only returns the k item id, similarity and content, so we need to get the full k item fields
    # We also adapt the pgvector retriever to match colbert's output

    for index, ki in enumerate(reference_kis):
        ki_item = await database_sync_to_async(
            KnowledgeItem.objects.prefetch_related("knowledgeitemimage_set").get
        )(pk=ki["k_item_id"])
        reference_kis[index] = {
            **ki_item.to_retrieve_context(),
            "similarity": ki["similarity"],
        }

    logger.info(f"References:\n{reference_kis}")
    # All images of the conversation so far
    reference_ki_images = {}
    for reference_ki in reference_kis:
        reference_ki_images = {**reference_ki_images, **reference_ki["image_urls"]}

    # TODO: We no longer associate the knowledge items with messages, in the future we will modify this
    # TODO: to associate the query with the knowledge items and the retriever used.
    # if relate_kis_to_msgs:  # Only when the generated text based on a human message then we will associate the generated text with it
    #     last_human_mml = await database_sync_to_async(conv.get_last_human_mml)()
    #     msgs2kis = [
    #         MessageKnowledgeItem(
    #             message=last_human_mml,
    