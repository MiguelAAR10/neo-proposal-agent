from fastapi import FastAPI

from src.agent.graph import run_agent
from src.config import get_settings

app = FastAPI(title="neo-proposal-agent", version="0.1.0")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/config")
def config_status() -> dict[str, bool]:
    settings = get_settings()
    return {
        "qdrant_url_configured": bool(settings.qdrant_url),
        "qdrant_api_key_configured": bool(settings.qdrant_api_key),
        "gemini_api_key_configured": bool(settings.gemini_api_key),
    }


@app.post("/agent/run")
def run(payload: dict[str, str]) -> dict[str, str]:
    result = run_agent(payload.get("input", ""))
    return {"answer": result["answer"]}
