from fastapi import FastAPI
from local_agents.perfect_agent.runner import chat_with_agent

app = FastAPI(title="PERFECT-AGENT API")


@app.post("/chat")
def chat(payload: dict):
    return {"response": chat_with_agent(payload["message"])}
