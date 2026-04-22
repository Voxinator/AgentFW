"""
Gemma 4 tool call parser.

Gemma uses multiple raw text formats when structured tool calling fails:

Format 1: <|tool_call>call:func_name{key: value}<tool_call|>
Format 2: [Calling tool: func_name({"key": "value"})]

Gemma also uses <|"|> as string delimiters in Format 1.
"""

import json
import re
import uuid
from typing import List, Optional, Tuple

from openai.types.chat.chat_completion_message_tool_call import (
    ChatCompletionMessageToolCall,
    Function,
)

from environments.tool_call_parsers import ParseResult, ToolCallParser, register_parser


@register_parser("gemma")
class GemmaToolCallParser(ToolCallParser):

    PIPE_PATTERN = re.compile(
        r"<\|tool_call>call:(\w+)\{(.*?)\}<tool_call\|>|"
        r"<\|tool_call>call:(\w+)\{(.*)",
        re.DOTALL,
    )

    BRACKET_PATTERN = re.compile(
        r"\[Calling tool:\s*(\w+)\((\{.*?\})\)\]|"
        r"\[Calling tool:\s*(\w+)\((\{.*)",
        re.DOTALL,
    )

    def _clean_pipe_quotes(self, s):
        """Strip Gemma's pipe-quote tokens used as string delimiters."""
        return s.replace('<|"|>', '').strip()

    def _parse_pipe_args(self, raw):
        raw = raw.strip()
        # Strip pipe-quote tokens first
        raw = raw.replace('<|"|>', '"')

        # Try JSON
        try:
            return json.loads(raw if raw.startswith("{") else "{" + raw + "}")
        except (json.JSONDecodeError, TypeError):
            pass

        # Parse key: 'value' or key: "value" pairs
        result = {}
        pairs = re.findall(r'(\w+):\s*[\'"](.+?)[\'"]', raw, re.DOTALL)
        for k, v in pairs:
            result[k] = v
        if not result:
            pairs = re.findall(r'(\w+):\s*(.+?)(?:,|$)', raw)
            for k, v in pairs:
                result[k] = v.strip().strip('\'"')
        return result

    def parse(self, text):
        has_pipe = "<|tool_call>" in text
        has_bracket = "[Calling tool:" in text

        if not has_pipe and not has_bracket:
            return text, None

        try:
            tool_calls = []

            if has_pipe:
                for match in self.PIPE_PATTERN.finditer(text):
                    name = match.group(1) or match.group(3)
                    raw_args = match.group(2) or match.group(4) or ""
                    if not name:
                        continue
                    args = self._parse_pipe_args(raw_args)
                    # Clean pipe-quote tokens from all string values
                    for k, v in args.items():
                        if isinstance(v, str):
                            args[k] = self._clean_pipe_quotes(v)
                    tool_calls.append(
                        ChatCompletionMessageToolCall(
                            id="call_" + uuid.uuid4().hex[:8],
                            type="function",
                            function=Function(
                                name=name,
                                arguments=json.dumps(args, ensure_ascii=False),
                            ),
                        )
                    )

            if has_bracket:
                for match in self.BRACKET_PATTERN.finditer(text):
                    name = match.group(1) or match.group(3)
                    raw_args = match.group(2) or match.group(4) or "{}"
                    if not name:
                        continue
                    try:
                        args = json.loads(raw_args)
                    except json.JSONDecodeError:
                        try:
                            args = json.loads(raw_args + "}")
                        except json.JSONDecodeError:
                            args = {"command": raw_args}
                    tool_calls.append(
                        ChatCompletionMessageToolCall(
                            id="call_" + uuid.uuid4().hex[:8],
                            type="function",
                            function=Function(
                                name=name,
                                arguments=json.dumps(args, ensure_ascii=False),
                            ),
                        )
                    )

            if not tool_calls:
                return text, None

            first_marker = len(text)
            for marker in ["<|tool_call>", "[Calling tool:"]:
                idx = text.find(marker)
                if idx >= 0:
                    first_marker = min(first_marker, idx)

            content = text[:first_marker].strip()
            content = re.sub(r"<\|channel>thought\n<channel\|>", "", content).strip()

            return content if content else None, tool_calls

        except Exception:
            return text, None
