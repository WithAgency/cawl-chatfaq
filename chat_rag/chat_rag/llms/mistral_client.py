import json
import os
from typing import Callable, Dict, List, Union

from chat_rag.llms.types import Content, Message, ToolResult, ToolUse, Usage
from mistralai import Mistral


from .base_llm import LLM
from .format_tools import Mode, format_tools


class MistralChatModel(LLM):
    def __init__(
        self,
        llm_name: str = "mistral-large-latest",
        **kwargs,
    ):
        self.client = Mistral(api_key=os.environ["MISTRAL_API_KEY"])
        self.llm_name = llm_name

    def _format_messages(self, messages: List[Union[Dict, Message]]) -> List[Dict]:
        """
        Convert standard chat messages to Mistral/OpenAI format.
        Mirrors the OpenAI client's _format_messages method.
        """
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"INPUT: Received {len(messages)} messages to format")

        def format_content(message: Message):
            content_list = []
            tool_calls = []
            tool_results = []

            if isinstance(message.content, str):
                return message.content, [], []
            else:
                for content in message.content:
                    if content.type == "text":
                        content_list.append(content.text)
                    elif content.type == "tool_use":
                        part = {
                            "type": "function",
                            "id": content.tool_use.id,
                            "function": {
                                "name": content.tool_use.name,
                                "arguments": json.dumps(content.tool_use.args),
                            },
                        }
                        tool_calls.append(part)
                    elif content.type == "tool_result":
                        tool_results.append(
                            {
                                "tool_call_id": content.tool_result.id,
                                "role": "tool",
                                "content": json.dumps(content.tool_result.result) if isinstance(content.tool_result.result, dict) else str(content.tool_result.result),
                            }
                        )

            return " ".join(content_list) if content_list else None, tool_calls, tool_results

        import logging
        logger = logging.getLogger(__name__)

        messages_formatted = []
        skip_next_tool_results = False

        for idx, message in enumerate(messages):
            # Handle dict messages with tool_calls or tool results (from FSM orchestrator)
            if isinstance(message, Dict):
                # Do not mutate the caller's message while normalizing it.
                message = message.copy()
                # Handle tool role messages: {"role": "tool", "tool_call_id": "...", "name": "...", "content": "..."}
                if message.get("role") == "tool":
                    logger.error(f"🔧 DICT MESSAGE: Found tool message at index {idx}, tool_call_id={message.get('tool_call_id')}")
                    # Convert tool dict to Message with ToolResult content
                    message = Message(
                        role="user",  # Tool results are treated as user messages in the content flow
                        content=[
                            Content(
                                type="tool_result",
                                tool_result=ToolResult(
                                    id=message.get("tool_call_id"),
                                    result=message.get("content")
                                )
                            )
                        ]
                    )
                    logger.error(f"   ✅ Converted to ToolResult: id={message.content[0].tool_result.id}")
                else:
                    # Handle cases where content might be None - convert to empty string
                    if message.get("content") is None:
                        message["content"] = ""

                    # Extract tool_calls from dict before converting to Message
                    # FSM sends: {"role": "assistant", "content": None, "tool_calls": [...]}
                    dict_tool_calls = message.pop("tool_calls", None)

                    message = Message(**message)

                    # If dict had tool_calls, convert them to Content objects
                    if dict_tool_calls:
                        logger.error(f"🔧 DICT MESSAGE: Found {len(dict_tool_calls)} tool_calls in dict message at index {idx}")
                        if isinstance(message.content, str):
                            # Convert string content to list
                            message.content = [Content(type="text", text=message.content)] if message.content else []
                        elif not isinstance(message.content, list):
                            message.content = []

                        # Add tool_calls as Content objects
                        for tc in dict_tool_calls:
                            message.content.append(
                                Content(
                                    type="tool_use",
                                    tool_use=ToolUse(
                                        id=tc.get("id"),
                                        name=tc["function"]["name"],
                                        args=json.loads(tc["function"]["arguments"]) if isinstance(tc["function"]["arguments"], str) else tc["function"]["arguments"]
                                    )
                                )
                            )
                            logger.error(f"   ✅ Converted tool_call to Content: id={tc.get('id')}, name={tc['function']['name']}")

            content, tool_calls, tool_results = format_content(message)

            logger.error(f"Processing message {idx}: role={message.role}, has_content={bool(content)}, has_tool_calls={len(tool_calls)}, has_tool_results={len(tool_results)}, skip_flag={skip_next_tool_results}")

            # If there are tool results
            if tool_results:
                logger.error(f"Found tool_results, skip_flag={skip_next_tool_results}, num_results={len(tool_results)}")
                # Skip tool results if the previous assistant message was skipped
                if skip_next_tool_results:
                    logger.error(f"SKIPPING tool results because flag is set")
                    skip_next_tool_results = False
                    # If there's also user text alongside tool results, add it as a user message
                    if content and message.role == "user":
                        logger.error(f"Adding user text after skipped tools: {content[:50]}")
                        messages_formatted.append({
                            "role": "user",
                            "content": content
                        })
                    continue

                # Add tool results only if we have a valid assistant message before them
                logger.error(f"Adding {len(tool_results)} tool messages")
                messages_formatted.extend(tool_results)

                # If there's also user text alongside tool results, add it as a user message
                if content and message.role == "user":
                    logger.error(f"Adding user text: {content[:50]}")
                    messages_formatted.append({
                        "role": "user",
                        "content": content
                    })
                continue
            else:
                msg_dict = {
                    "role": message.role,
                    "content": content if content else None,
                }
                # Only add tool_calls if present (Mistral doesn't accept tool_calls: null)
                if tool_calls:
                    msg_dict["tool_calls"] = tool_calls

                # Mistral requires assistant messages to have either non-empty content or tool_calls
                # Skip messages that have neither (these are malformed from conversation history)
                if message.role == "assistant" and not msg_dict.get("content") and not msg_dict.get("tool_calls"):
                    # Skip this malformed assistant message and flag to skip following tool results
                    skip_next_tool_results = True
                    continue

                messages_formatted.append(msg_dict)
                skip_next_tool_results = False

        import logging
        logger = logging.getLogger(__name__)

        # Helper to truncate content for cleaner logging
        def truncate_message(msg):
            msg_copy = msg.copy()
            if isinstance(msg_copy.get("content"), str) and len(msg_copy["content"]) > 100:
                msg_copy["content"] = msg_copy["content"][:100] + "..."
            return msg_copy

        logger.error(f"MISTRAL FORMATTED MESSAGES: {json.dumps([truncate_message(m) for m in messages_formatted], indent=2)}")

        # Final validation: remove tool messages that do not correspond to a pending
        # call from the immediately preceding assistant turn. A single assistant
        # turn may contain multiple calls, and Mistral requires one response for
        # each call; therefore checking only the immediately preceding message
        # incorrectly drops every result after the first one.
        validated_messages = []
        pending_tool_call_ids = set()
        for i, msg in enumerate(messages_formatted):
            if msg.get("role") == "assistant":
                tool_calls = msg.get("tool_calls") or []
                pending_tool_call_ids = {
                    tool_call.get("id")
                    for tool_call in tool_calls
                    if tool_call.get("id")
                }
                validated_messages.append(msg)
            elif msg.get("role") == "tool":
                tool_call_id = msg.get("tool_call_id")
                if tool_call_id in pending_tool_call_ids:
                    validated_messages.append(msg)
                    pending_tool_call_ids.remove(tool_call_id)
                else:
                    logger.error(f"DROPPING orphaned tool message at index {i}: {tool_call_id or 'unknown'}")
            else:
                # A new user/system message starts a new turn. Any calls left
                # unresolved by that point cannot be paired safely.
                pending_tool_call_ids.clear()
                validated_messages.append(msg)

        if len(validated_messages) != len(messages_formatted):
            logger.error(f"VALIDATED MESSAGES (removed {len(messages_formatted) - len(validated_messages)} orphaned tools): {json.dumps([truncate_message(m) for m in validated_messages], indent=2)}")

        # CRITICAL: Detect infinite loop caused by malformed conversation history
        # If we keep dropping tool messages and ending up with just [system, user],
        # this means tool_calls are being lost during serialization to the database
        if len(validated_messages) == 2 and validated_messages[0].get("role") == "system" and validated_messages[1].get("role") == "user":
            # Check if we dropped assistant messages (indicating corrupted history)
            dropped_assistant_count = sum(1 for m in messages_formatted if m.get("role") == "assistant")
            dropped_tool_count = len(messages_formatted) - len(validated_messages)

            if dropped_assistant_count > 0 or dropped_tool_count > 0:
                logger.error(f"🔴 INFINITE LOOP DETECTED:")
                logger.error(f"   - Dropped {dropped_assistant_count} assistant messages without tool_calls")
                logger.error(f"   - Dropped {dropped_tool_count} orphaned tool messages")
                logger.error(f"   - This indicates tool_calls are being lost during conversation history serialization")
                logger.error(f"   - Returning ONLY [system, user] to prevent infinite loop")
                logger.error(f"   - WARNING: Conversation history is not being preserved!")
                logger.error(f"   - ACTION REQUIRED: Fix upstream tool_calls serialization in consumers/__init__.py")

                # Return just system and user - conversation history is broken anyway
                return [validated_messages[0], validated_messages[1]]

        return validated_messages

    def _format_tools(
        self, tools: list[Union[Callable, dict]] = None, tool_choice: str = None
    ):
        """
        Format the tools from a openai dict or a callable function to the Mistral format.
        """
        if not tools:
            return [], "none"

        if tool_choice is None:
            tool_choice = "none"

        # format_tools returns (tools_formatted, tool_choice)
        tools_formatted, tool_choice = format_tools(
            tools=tools, tool_choice=tool_choice, mode=Mode.MISTRAL_TOOLS
        )

        # Extract tool names for validation (tools are in OpenAI format: {"type": "function", "function": {...}})
        tool_names = [tool["function"]["name"] for tool in tools_formatted]
        valid_choices = [*tool_names, "auto", "none"]

        if tool_choice not in valid_choices:
            raise ValueError(
                f"tool_choice must be 'none', 'auto', or one of the tool names: {', '.join(tool_names)}"
            )

        return tools_formatted, tool_choice


    def _map_mistral_message(self, message, usage_info=None) -> Message:
        """
        Map a Mistral message (from generate/agenerate/stream) to the standard Message format.
        """
        content_list = []

        message_content = getattr(message, "content", None)

        if message_content:
            # Mistral may return either a plain string or a list of chunks.
            if isinstance(message_content, str):
                content_list.append(
                    Content(type="text", text=message_content)
                )

            elif isinstance(message_content, list):
                for chunk in message_content:
                    # TextChunk and similar Mistral content objects
                    text = getattr(chunk, "text", None)

                    if text is not None:
                        content_list.append(
                            Content(type="text", text=text)
                        )

        tool_calls = getattr(message, "tool_calls", None)

        if tool_calls:
            for tool_call in tool_calls:
                arguments = tool_call.function.arguments

                # Depending on the Mistral SDK/version, arguments may
                # already be decoded rather than a JSON string.
                if isinstance(arguments, str):
                    arguments = json.loads(arguments)

                content_list.append(
                    Content(
                        type="tool_use",
                        tool_use=ToolUse(
                            id=tool_call.id,
                            name=tool_call.function.name,
                            args=arguments,
                        ),
                    )
                )

        usage = None

        if usage_info:
            prompt_tokens_details = getattr(usage_info, "prompt_tokens_details", None)
            usage = Usage(
                input_tokens=usage_info.prompt_tokens,
                output_tokens=usage_info.completion_tokens,
                cache_creation_read_tokens=getattr(
                    prompt_tokens_details, "cached_tokens", 0
                ) if prompt_tokens_details else 0,
            )

        return Message(
            role=getattr(message, "role", "assistant"),
            content=content_list,
            usage=usage,
        )

    def stream(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 1.0,
        max_tokens: int = 1024,
        seed: int | None = None,
        **kwargs,
    ):
        """
        Generate text from a prompt using the model in streaming mode.
        Parameters
        ----------
        messages : List[Tuple[str, str]]
            The messages to use for the prompt. Pair of (role, message).
        Returns
        -------
        str
            The generated text.
        """

        messages = self._format_messages(
            messages=messages,
        )

        for chunk in self.client.chat.stream(
            model=self.llm_name,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            random_seed=seed,
        ):
            content = chunk.data.choices[0].delta.content
            if content is not None:
                yield content

    async def astream(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 1.0,
        max_tokens: int = 1024,
        seed: int | None = None,
        **kwargs,
    ):
        """
        Generate text from a prompt using the model in streaming mode.
        Parameters
        ----------
        messages : List[Tuple[str, str]]
            The messages to use for the prompt. Pair of (role, message).
        Returns
        -------
        str
            The generated text.
        """

        messages = self._format_messages(
            messages=messages,
        )

        # **await the coroutine first**, then async for
        stream_iter = await self.client.chat.stream_async(
            model=self.llm_name,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            random_seed=seed,
        )

        async for chunk in stream_iter:
            content = chunk.data.choices[0].delta.content
            if content is not None:
                yield content

    def generate(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 1.0,
        max_tokens: int = 1024,
        seed: int = None,
        tools: List[Union[Callable, Dict]] = None,
        tool_choice: str = None,
        **kwargs,
    ):
        """
        Generate text from a prompt using a model.
        Parameters
        ----------
        messages : List[Tuple[str, str]]
            The messages to use for the prompt. Pair of (role, message).
        Returns
        -------
        str
            The generated text.
        """

        messages = self._format_messages(
            messages=messages,
        )

        if tools:
            tools, tool_choice = self._format_tools(tools, tool_choice)

        chat_response = self.client.chat.complete(
            model=self.llm_name,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            random_seed=seed,
            tools=tools,
            tool_choice=tool_choice,
        )

        message = chat_response.choices[0].message
        return self._map_mistral_message(message, usage_info=chat_response.usage)

    async def agenerate(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 1.0,
        max_tokens: int = 1024,
        seed: int | None = None,
        tools: List[Union[Callable, Dict]] | None = None,
        tool_choice: str | None = None,
        **kwargs,
    ):
        """
        Generate text from a prompt using a model.
        Parameters
        ----------
        messages : List[Tuple[str, str]]
            The messages to use for the prompt. Pair of (role, message).
        Returns
        -------
        str
            The generated text.
        """

        messages = self._format_messages(
            messages=messages,
        )

        if tools:
            tools, tool_choice = self._format_tools(tools, tool_choice)

        chat_response = await self.client.chat.complete_async(
            model=self.llm_name,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            random_seed=seed,
            tools=tools,
            tool_choice=tool_choice,
        )

        message = chat_response.choices[0].message

        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"MISTRAL RESPONSE: role={message.role}, has_content={bool(message.content)}, has_tool_calls={bool(message.tool_calls)}, tool_call_count={len(message.tool_calls) if message.tool_calls else 0}")

        return self._map_mistral_message(message, usage_info=chat_response.usage)

    async def aparse(
        self,
        messages: List[Union[Dict, Message]],
        schema: Dict,
        **kwargs,
    ) -> Dict:
        """Generate and decode one response matching a JSON schema."""
        messages = self._format_messages(messages)
        response = await self.client.chat.complete_async(
            model=self.llm_name,
            messages=messages,
            temperature=kwargs.get("temperature", 0.2),
            max_tokens=kwargs.get("max_tokens", 4096),
            random_seed=kwargs.get("seed"),
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": schema["title"],
                    "schema": schema,
                    "strict": True,
                },
            },
        )
        content = response.choices[0].message.content
        if not content:
            raise ValueError("Mistral returned empty structured output")
        return json.loads(content)
