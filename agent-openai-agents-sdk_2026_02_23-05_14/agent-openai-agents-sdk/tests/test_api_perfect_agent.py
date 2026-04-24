import os
import pytest
from fastapi.testclient import TestClient
from api.perfect_agent_api import app

client = TestClient(app)


@pytest.mark.skipif(
    not (os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY")),
    reason="API keys not configured"
)
def test_api_chat_endpoint():
    r = client.post("/chat", json={"message": "hello from test"})
    assert r.status_code == 200
    data = r.json()
    assert "response" in data
    assert isinstance(data["response"], str)
