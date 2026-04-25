import logging

import os
# Point mlflow at a local directory so it never tries to contact a remote tracking server
os.environ.setdefault("MLFLOW_TRACKING_URI", "mlruns")

from dotenv import load_dotenv
from mlflow.genai.agent_server import AgentServer, setup_mlflow_git_based_version_tracking

# Load env vars from .env before importing the agent for proper auth
load_dotenv(dotenv_path=".env", override=True)

# Need to import the agent to register the functions with the server
from agent_server import agent as agent_module  # noqa: E402

agent_server = AgentServer("ResponsesAgent", enable_chat_proxy=True)
# Define the app as a module level variable to enable multiple workers
app = agent_server.app  # noqa: F841
setup_mlflow_git_based_version_tracking()

LOGGER = logging.getLogger(__name__)


@app.on_event("startup")
async def log_startup_banner() -> None:
    LOGGER.warning(
        "Agent startup | backend=%s model=%s fallback_model=%s retries=%s base_retry_seconds=%s",
        agent_module.BACKEND,
        agent_module.MODEL,
        agent_module.FALLBACK_MODEL or "<none>",
        agent_module.MAX_RETRIES,
        agent_module.RETRY_BASE_SECONDS,
    )


@app.get("/health")
async def health() -> dict:
    return {
        "status": "ok",
        "backend": agent_module.BACKEND,
        "model": agent_module.MODEL,
        "fallback_model": agent_module.FALLBACK_MODEL or None,
        "max_retries": agent_module.MAX_RETRIES,
        "retry_base_seconds": agent_module.RETRY_BASE_SECONDS,
    }


def main():
    agent_server.run(app_import_string="agent_server.start_server:app")
