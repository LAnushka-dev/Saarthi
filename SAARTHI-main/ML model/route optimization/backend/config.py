import os
from dataclasses import dataclass

from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class Settings:
    port: int
    anthropic_api_key: str | None
    anthropic_model: str
    allow_llm_fallback: bool


def get_settings() -> Settings:
    return Settings(
        port=int(os.getenv("PORT", "8000")),
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY") or None,
        anthropic_model=os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-latest"),
        allow_llm_fallback=os.getenv("ALLOW_LLM_FALLBACK", "true").lower() == "true",
    )

