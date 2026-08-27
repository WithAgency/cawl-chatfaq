import json
import ast
from typing import Any

from chat_rag.llms.format_tools import Mode, format_tools
from chat_rag.llms.mistral_client import MistralChatModel


def test_format_tools_mistral_mode():
    def sample_tool(a: int, b: str = "x"):
        """Sample tool"""
        return None

    tools_formatted, choice = format_tools([sample_tool], tool_choice=None, mode=Mode.MISTRAL_TOOLS)
    assert isinstance(tools_formatted, list)
    assert tools_formatted[0]["name"] == "sample_tool"
    assert "parameters" in tools_formatted[0]


def test_map_mistral_message_parses_args():
    # Create a fake tool_call object with nested function and string arguments
    class Func:
        def __init__(self, name, arguments):
            self.name = name
            self.arguments = arguments

    class ToolCall:
        def __init__(self, id, function):
            self.id = id
            self.function = function

    class MessageObj:
        def __init__(self, content, tool_calls):
            self.content = content
            self.tool_calls = tool_calls
            self.role = "assistant"

    args_dict = {"x": 1, "y": "z"}
    func = Func("do_it", json.dumps(args_dict))
    tool_call = ToolCall("tool-1", func)
    msg = MessageObj("hello", [tool_call])

    # Create instance without calling __init__ (which requires MISTRAL_API_KEY env var)
    inst = MistralChatModel.__new__(MistralChatModel)

    mapped = inst._map_mistral_message(msg)
    # Expect one content entry for content and one tool_use
    assert any(c.type == "tool_use" for c in mapped.content)
    tool_contents = [c for c in mapped.content if c.type == "tool_use"]
    assert tool_contents[0].tool_use.args == args_dict
