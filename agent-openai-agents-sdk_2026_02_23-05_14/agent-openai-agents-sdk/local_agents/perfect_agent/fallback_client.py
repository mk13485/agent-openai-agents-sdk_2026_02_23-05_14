import os
from openai import OpenAI

NEMOTRON = "nvidia/nemotron-3-super-120b-a12b:free"
QWEN = "qwen/qwen-2.5-72b-instruct"
GPT4 = "gpt-4.1"

def get_clients():
    return {
        "openrouter": OpenAI(
            api_key=os.environ.get("OPENROUTER_API_KEY"),
            base_url="https://openrouter.ai/api/v1",
            default_headers={
                "HTTP-Referer": os.environ.get("APP_URL", "https://github.com/robert2687"),
                "X-Title": os.environ.get("APP_NAME", "PERFECT-AGENT"),
            }
        ),
        "openai": OpenAI(
            api_key=os.environ.get("OPENAI_API_KEY"),
        )
    }

def try_model(client, model, messages, tools=None):
    try:
        return client.chat.completions.create(
            model=model,
            messages=messages,
            tools=tools,
            tool_choice="auto" if tools else None,
        )
    except Exception:
        return None

def fallback_chat(messages, tools=None):
    clients = get_clients()

    for provider, model in [
        ("openrouter", NEMOTRON),
        ("openrouter", QWEN),
        ("openai", GPT4),
    ]:
        r = try_model(clients[provider], model, messages, tools)
        if r:
            return r

    raise RuntimeError("All models failed (Nemotron → Qwen → GPT‑4.1).")
