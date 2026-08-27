import json
import os
import ast
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
        Format the tool information from the mistral response to a standard format.
        """
        tools = []
        for tool in getattr(message, "tool_calls", []):
            # tool.function.arguments may be a JSON string or already a dict
            args_raw = getattr(tool.function, "arguments", None)
            args = args_raw
            if isinstance(args_raw, str):
                try:
                    args = json.loads(args_raw)
                except Exception:
                    try:
                        args = ast.literal_eval(args_raw)
                    except Exception:
                        args = args_raw

            tools.append(
                {
                    "id": getattr(tool, "id", None),
                    "name": getattr(tool.function, "name", None),
                    "args": args,
                }
            )

        return tools

    ...

    def _map_mistral_message(self, message, usage_info=None) -> Message:
        """
        Map a Mistral message (from generate/agenerate/stream) to the standard Message format.
        """
        content_list = []

        if hasattr(message, "content") and message.content:
            content_list.append(Content(type="text", text=message.content))

        if hasattr(message, "tool_calls") and message.tool_calls:
            def _parse_args(arg_value):
                if isinstance(arg_value, str):
                    try:
                        return json.loads(arg_value)
                    except Exception:
                        try:
                            return ast.literal_eval(arg_value)
                        except Exception:
                            return arg_value
                return arg_value

            for tool_call in message.tool_calls:
                args_raw = getattr(tool_call.function, "arguments", None)
                args = _parse_args(args_raw)
                content_list.append(
                    Content(
                        type="tool_use",
                        tool_use=ToolUse(
                            id=getattr(tool_call, "id", None),
                            name=getattr(tool_call.function, "name", None),
                            args=args,
                        ),
                    )
                )

        usage = None
        if usage_info:
            usage = Usage(
                input_tokens=usage_info.prompt_tokens,
                output_tokens=usage_info.completion_tokens,
                cache_creation_read_tokens=getattr(
                    usage_info.prompt_tokens_details, "cached_tokens", 0
                ) if usage_info.prompt_tokens_details else 0,
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
