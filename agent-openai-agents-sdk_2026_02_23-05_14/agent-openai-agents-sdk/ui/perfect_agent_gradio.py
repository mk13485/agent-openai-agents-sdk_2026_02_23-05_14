import gradio as gr
from agents.perfect_agent.runner import chat_with_agent


def chat_fn(message, history):
    reply = chat_with_agent(message)
    history = history + [[message, reply]]
    return history, history


with gr.Blocks(title="PERFECT-AGENT") as demo:
    gr.Markdown("# PERFECT-AGENT\nNemotron → Qwen → GPT‑4.1 fallback")
    chat = gr.Chatbot()
    msg = gr.Textbox(label="Message")
    clear = gr.Button("Clear")

    msg.submit(chat_fn, [msg, chat], [chat, chat])
    clear.click(lambda: ([], []), None, [chat, chat])

if __name__ == "__main__":
    demo.launch()
