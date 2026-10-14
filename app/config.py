from __future__ import annotations
import os, yaml
from dataclasses import dataclass

@dataclass
class Settings:
    business_config: str = os.getenv("BUSINESS_CONFIG", "knowledge/generic_service_business.yaml")
    llm_base_url: str = os.getenv("LLM_BASE_URL", "")
    llm_api_key: str = os.getenv("LLM_API_KEY", "")
    llm_model: str = os.getenv("LLM_MODEL", "")
    llm_protocol: str = os.getenv("LLM_PROTOCOL", "openai")
    llm_session: str = os.getenv("LLM_SESSION", "")
    tts_provider: str = os.getenv("TTS_PROVIDER", "edge")
    edge_tts_voice: str = os.getenv("EDGE_TTS_VOICE", "en-GB-RyanNeural")
    default_locale: str = os.getenv("DEFAULT_LOCALE", "en-GB")
    support_db: str = os.getenv("SUPPORT_DB", "runtime/support.db")

    @classmethod
    def load_business(cls, path: str):
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
