import os
import pytest
from local_agents.perfect_agent.runner import chat_with_agent


@pytest.mark.skipif(
    not (os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY")),
    reason="API keys not configured"
)
def test_perfect_agent_basic_response():
    resp = chat_with_agent("Say 'integration test ok' in one short sentence.")
    assert isinstance(resp, str)
    assert "integration" in resp.lower()
