import json
import importlib
from pathlib import Path

from .fallback_client import fallback_chat

SYSTEM_PROMPT = Path(__file__).with_name("system_prompt.txt").read_text()

TOOLS = {
    "read_file": "agents.perfect_agent.tools.file:read_file",
    "write_file": "agents.perfect_agent.tools.file:write_file",
    "http_get": "agents.perfect_agent.tools.http:http_get",
    "http_post": "agents.perfect_agent.tools.http:http_post",
    "run_shell": "agents.perfect_agent.tools.shell:run",
}


def load_tool(name):
    module_path, func_name = TOOLS[name].split(":")
    module = importlib.import_module(module_path)
    return getattr(module, func_name)


def call_tool(name, args):
    return load_tool(name)(**args)


def tool_schemas():
    return [{"type": "function", "function": {"name": name}} for name in TOOLS]

def chat_with_agent(user_message):
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_message},
    ]

    response = fallback_chat(messages, tools=tool_schemas())
    msg = response.choices[0].message

    if msg.tool_calls:
        tool_results = []
        for call in msg.tool_calls:
            tool_name = call.function.name
            args = json.loads(call.function.arguments or "{}")
            result = call_tool(tool_name, args)
            tool_results.append(
                {
                    "role": "tool",
                    "tool_call_id": call.id,
                    "name": tool_name,
                    "content": json.dumps(result),
                }
            )

        messages.append({"role": "assistant", "tool_calls": msg.tool_calls})
        messages.extend(tool_results)

        final = fallback_chat(messages)
        return final.choices[0].message.content

    return msg.content


def main():
    print("PERFECT-AGENT CLI (Nemotron → Qwen → GPT‑4.1 fallback). Ctrl+C to exit.")
    while True:
        try:
            user_input = input("\nYou: ").strip()
            if user_input.lower() in {"exit", "quit"}:
                break
            print("\nAgent:\n")
            print(chat_with_agent(user_input))
        except KeyboardInterrupt:
            break


if __name__ == "__main__":
    main()
