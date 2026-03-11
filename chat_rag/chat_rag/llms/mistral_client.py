import json
import os
from typing import Callable, Dict, List, Union
from chat_rag.llms.types import Content, Message, ToolUse, Usage

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

    def format_prompt(
        self,
        messages: List[Dict[str, str]],
    ) -> List[Dict[str, str]]:
        """
        Formats the prompt to be used by the model into the correct Mistral format.
        """
        final_messages = [
            {"role": message["role"], "content": message["content"]}
            for message in messages
        ]

        return final_messages

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

        tools_formatted = format_tools(
            tools=tools, tool_choice=tool_choice, mode=Mode.MISTRAL_TOOLS
        )

        tool_names = [tool["name"] for tool in tools_formatted]
        valid_choices = [*tool_names, "auto", "none"]

        if tool_choice not in valid_choices:
            raise ValueError(
                f"tool_choice must be 'none', 'auto', or one of the tool names: {', '.join(tool_names)}"
            )

        return tools_formatted, tool_choice

    def _extract_tool_info(self, message) -> List[Dict]:
        """
        Format the tool information from the anthropic response to a standard format.
        """
        tools = []
        for tool in getattr(message, "tool_calls", []):
            tools.append(
                {
                    "id": tool.id,
                    "name": tool.function.name,
                    "args": tool.function.arguments,
                }
            )

        return tools

    ...

    def _map_mistral_message(self, message) -> Message:
        """
        Map a Mistral message (from generate/agenerate/stream) to the standard Message format.
        """
        content_list = []

        if hasattr(message, "content") and message.content:
            content_list.append(Content(type="text", text=message.content))

        if hasattr(message, "tool_calls") and message.tool_calls:
            content_list.extend(
                Content(
                    type="tool_use",
                    tool_use=ToolUse(
                        id=tool_call.id,
                        name=tool_call.function.name,
                        args=json.loads(tool_call.function.arguments),
                    ),
                )
                for tool_call in message.tool_calls
            )

        usage = None
        if hasattr(message, "usage") and message.usage:
            usage = Usage(
                input_tokens=message.usage.prompt_tokens,
                output_tokens=message.usage.completion_tokens,
                cache_creation_read_tokens=getattr(
                    message.usage.prompt_tokens_details, "cached_tokens", 0
                ),
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

        messages = self.format_prompt(
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

        messages = self.format_prompt(
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

        messages = self.format_prompt(
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
        if getattr(chat_response.choices[0], "finish_reason", None) == "tool_calls":
            return self._extract_tool_info(message)

        return self._map_mistral_message(message)

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

        messages = self.format_prompt(
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
        if chat_response.choices[0].finish_reason == "tool_calls":
            return self._extract_tool_info(message)

        return self._map_mistral_message(message)
