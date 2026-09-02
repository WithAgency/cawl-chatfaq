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
        api_key: str = None,
        **kwargs,
    ):
        api_key = api_key or os.environ.get("MISTRAL_API_KEY")
        if not api_key:
            raise ValueError("MISTRAL_API_KEY is required")

        self.client = Mistral(api_key=api_key)
        self.aclient = Mistral(api_key=api_key)
        self.llm_name = llm_name

    @staticmethod
    def _format_content(message: Message) -> tuple[str | None, list[dict], list[dict]]:
        content_list = []
        tool_calls = []
        tool_results = []

        if isinstance(message.content, str):
            return message.content, tool_calls, tool_results

        for content in message.content:
            if content.type == "text":
                content_list.append(content.text)
            elif content.type == "tool_use":
                tool_calls.append(
                    {
                        "type": "function",
                        "id": content.tool_use.id,
                        "function": {
                            "name": content.tool_use.name,
                            "arguments": json.dumps(content.tool_use.args),
                        },
                    }
                )
            elif content.type == "tool_result":
                result = content.tool_result.result
                tool_results.append(
                    {
                        "tool_call_id": content.tool_result.id,
                        "role": "tool",
                        "content": json.dumps(result) if isinstance(result, dict) else str(result),
                    }
                )

        return " ".join(content_list) if content_list else None, tool_calls, tool_results

    @staticmethod
    def _normalize_message(message: Union[Dict, Message]) -> Message:
        if not isinstance(message, dict):
            return message

        message = message.copy()
        if message.get("role") == "tool":
            return Message(
                role="user",
                content=[
                    Content(
                        type="tool_result",
                        tool_result=ToolResult(
                            id=message.get("tool_call_id"),
                            result=message.get("content"),
                        ),
                    )
                ],
            )

        if message.get("content") is None:
            message["content"] = ""

        dict_tool_calls = message.pop("tool_calls", None)
        normalized = Message(**message)

        if dict_tool_calls:
            if isinstance(normalized.content, str):
                normalized.content = (
                    [Content(type="text", text=normalized.content)]
                    if normalized.content
                    else []
                )
            elif not isinstance(normalized.content, list):
                normalized.content = []

            for tool_call in dict_tool_calls:
                arguments = tool_call["function"]["arguments"]
                if isinstance(arguments, str):
                    arguments = json.loads(arguments)
                normalized.content.append(
                    Content(
                        type="tool_use",
                        tool_use=ToolUse(
                            id=tool_call.get("id"),
                            name=tool_call["function"]["name"],
                            args=arguments,
                        ),
                    )
                )

        return normalized

    @staticmethod
    def _validate_tool_messages(messages: list[dict]) -> list[dict]:
        validated_messages = []
        pending_tool_call_ids = set()

        for message in messages:
            if message.get("role") == "assistant":
                pending_tool_call_ids = {
                    tool_call.get("id")
                    for tool_call in message.get("tool_calls") or []
                    if tool_call.get("id")
                }
                validated_messages.append(message)
            elif message.get("role") == "tool":
                tool_call_id = message.get("tool_call_id")
                if tool_call_id in pending_tool_call_ids:
                    validated_messages.append(message)
                    pending_tool_call_ids.remove(tool_call_id)
            else:
                pending_tool_call_ids.clear()
                validated_messages.append(message)

        return validated_messages

    def _format_messages(self, messages: List[Union[Dict, Message]]) -> List[Dict]:
        """
        Convert standard chat messages to Mistral/OpenAI format.
        Mirrors the OpenAI client's _format_messages method.
        """
        messages_formatted = []
        skip_next_tool_results = False

        for message in messages:
            message = self._normalize_message(message)
            content, tool_calls, tool_results = self._format_content(message)

            # If there are tool results
            if tool_results:
                # Skip tool results if the previous assistant message was skipped
                if skip_next_tool_results:
                    skip_next_tool_results = False
                    # If there's also user text alongside tool results, add it as a user message
                    if content and message.role == "user":
                        messages_formatted.append({
                            "role": "user",
                            "content": content
                        })
                    continue

                # Add tool results only if we have a valid assistant message before them
                messages_formatted.extend(tool_results)

                # If there's also user text alongside tool results, add it as a user message
                if content and message.role == "user":
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

        return self._validate_tool_messages(messages_formatted)

    def _format_tools(
        self,
        tools: list[Union[Callable, dict]] = None,
        tool_choice: str = None,
    ) -> tuple[list[dict], str]:
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


    def _map_mistral_message(
        self, message, usage_info=None, stop_reason: str = None
    ) -> Message:
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

        stop_reason = stop_reason or getattr(message, "stop_reason", None)
        if stop_reason is None:
            stop_reason = getattr(message, "finish_reason", None)
        stop_reason = {
            "stop": "end_turn",
            "length": "max_tokens",
            "tool_calls": "tool_use",
        }.get(stop_reason, stop_reason)
        if stop_reason not in {"end_turn", "max_tokens", "tool_use", "content_filter"}:
            stop_reason = None

        return Message(
            role=getattr(message, "role", "assistant"),
            content=content_list,
            usage=usage,
            stop_reason=stop_reason,
        )

    def stream(
        self,
        messages: List[Union[Dict, Message]],
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
        messages: List[Union[Dict, Message]],
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
        stream_iter = await self.aclient.chat.stream_async(
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
        messages: List[Union[Dict, Message]],
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
        return self._map_mistral_message(
            message,
            usage_info=chat_response.usage,
            stop_reason=getattr(chat_response.choices[0], "finish_reason", None),
        )

    async def agenerate(
        self,
        messages: List[Union[Dict, Message]],
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

        chat_response = await self.aclient.chat.complete_async(
            model=self.llm_name,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            random_seed=seed,
            tools=tools,
            tool_choice=tool_choice,
        )

        message = chat_response.choices[0].message

        return self._map_mistral_message(
            message,
            usage_info=chat_response.usage,
            stop_reason=getattr(chat_response.choices[0], "finish_reason", None),
        )

    def parse(
        self,
        messages: List[Union[Dict, Message]],
        schema: Dict,
        **kwargs,
    ) -> Dict:
        """Generate and decode one response matching a JSON schema."""
        messages = self._format_messages(messages)
        response = self.client.chat.complete(
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

    async def aparse(
        self,
        messages: List[Union[Dict, Message]],
        schema: Dict,
        **kwargs,
    ) -> Dict:
        """Generate and decode one response matching a JSON schema."""
        messages = self._format_messages(messages)
        response = await self.aclient.chat.complete_async(
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
