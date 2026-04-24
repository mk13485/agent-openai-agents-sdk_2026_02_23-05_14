import importlib
import json
import os
from pathlib import Path
from typing import Any

from openai import OpenAI

BASE_DIR = Path(__file__).resolve().parent
SYSTEM_PROMPT = (BASE_DIR / "system_prompt.txt").read_text(encoding="utf-8")

client = OpenAI(
    api_key=os.environ.get("OPENROUTER_API_KEY"),
    base_url=os.environ.get("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
    default_headers={
        "HTTP-Referer": os.environ.get("APP_URL", "https://github.com/robert2687"),
        "X-Title": os.environ.get("APP_NAME", "PERFECT-AGENT"),
    },
)

MODEL = os.environ.get("PERFECT_AGENT_MODEL", "nvidia/nemotron-3-super-120b-a12b:free")
MAX_TOOL_ROUNDS = int(os.environ.get("PERFECT_AGENT_MAX_TOOL_ROUNDS", "5"))

TOOLS = {
    "read_file": "agents.perfect_agent.tools.file:read_file",
    "write_file": "agents.perfect_agent.tools.file:write_file",
    "http_get": "agents.perfect_agent.tools.http:http_get",
    "http_post": "agents.perfect_agent.tools.http:http_post",
    "run_shell": "agents.perfect_agent.tools.shell:run",
}


def load_tool(name: str):
    module_path, func_name = TOOLS[name].split(":")
    module = importlib.import_module(module_path)
    return getattr(module, func_name)


def call_tool(name: str, args: dict):
    fn = load_tool(name)
    return fn(**args)


def tool_schemas() -> list[dict[str, Any]]:
    return [
        {
            "type": "function",
            "function": {
                "name": "read_file",
                "description": "Read a text file from the workspace.",
                "parameters": {
                    "type": "object",
                    "properties": {"path": {"type": "string"}},
                    "required": ["path"],
                    "additionalProperties": False,
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "write_file",
                "description": "Write text content to a file.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string"},
                        "content": {"type": "string"},
                    },
                    "required": ["path", "content"],
                    "additionalProperties": False,
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "http_get",
                "description": "Perform an HTTP GET request.",
                "parameters": {
                    "type": "object",
                    "properties": {"url": {"type": "string"}},
                    "required": ["url"],
                    "additionalProperties": False,
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "http_post",
                "description": "Perform an HTTP POST request.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "url": {"type": "string"},
                        "json_body": {"type": "object"},
                    },
                    "required": ["url", "json_body"],
                    "additionalProperties": False,
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "run_shell",
                "description": "Run a shell command.",
                "parameters": {
                    "type": "object",
                    "properties": {"cmd": {"type": "string"}},
                    "required": ["cmd"],
                    "additionalProperties": False,
                },
            },
        },
    ]


def _tool_calls_to_dicts(tool_calls) -> list[dict[str, Any]]:
    return [
        {
            "id": call.id,
            "type": "function",
            "function": {
                "name": call.function.name,
                "arguments": call.function.arguments or "{}",
            },
        }
        for call in tool_calls
    ]


def chat_with_agent(user_message: str) -> str:
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_message},
    ]

    for _ in range(MAX_TOOL_ROUNDS):
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=tool_schemas(),
            tool_choice="auto",
        )

        msg = response.choices[0].message
        if not msg.tool_calls:
            return msg.content or ""

        messages.append(
            {
                "role": "assistant",
                "content": msg.content or "",
                "tool_calls": _tool_calls_to_dicts(msg.tool_calls),
            }
        )

        for call in msg.tool_calls:
            tool_name = call.function.name
            try:
                args = json.loads(call.function.arguments or "{}")
                if not isinstance(args, dict):
                    raise ValueError("Tool arguments must be a JSON object")
                result = call_tool(tool_name, args)
            except Exception as e:  # noqa: BLE001
                result = {"ok": False, "tool": tool_name, "error": str(e)}

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": call.id,
                    "name": tool_name,
                    "content": json.dumps(result, ensure_ascii=False, default=str),
                }
            )

    return "Stopped after max tool rounds without a final response."


def main() -> None:
    if not os.environ.get("OPENROUTER_API_KEY"):
        print("ERROR: OPENROUTER_API_KEY is not set")
        return

    print("PERFECT-AGENT (OpenRouter). Ctrl+C to exit.")
    while True:
        try:
            user_input = input("\nYou: ").strip()
            if not user_input:
                continue
            if user_input.lower() in {"exit", "quit"}:
                print("Exiting.")
                break

            reply = chat_with_agent(user_input)
            print("\nAgent:\n")
            print(reply)
        except KeyboardInterrupt:
            print("\nExiting.")
            break
        except Exception as e:  # noqa: BLE001
            print(f"\nERROR: {e}")


if __name__ == "__main__":
    main()
