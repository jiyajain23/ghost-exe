"""Environment configuration, without dotenv or startup network calls."""
import os
from urllib.parse import urlsplit
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class Settings(BaseModel):
    agent_mode: Literal['mock', 'ollama'] = 'mock'
    ollama_base_url: str = 'http://127.0.0.1:11434'
    ollama_model: str = 'gemma3:1b'
    model_timeout_seconds: float = Field(default=20, gt=0, le=120)

    @field_validator('ollama_base_url')
    @classmethod
    def loopback_only(cls, value: str) -> str:
        url = urlsplit(value)
        if (url.scheme != 'http' or url.hostname not in {'127.0.0.1', 'localhost', '::1'}
                or url.username or url.password or url.query or url.fragment
                or url.path not in {'', '/'}):
            raise ValueError('OLLAMA_BASE_URL must be an HTTP loopback origin')
        _ = url.port  # Validate port syntax.
        return value.rstrip('/')

    @classmethod
    def from_environment(cls) -> 'Settings':
        names = {'agent_mode': 'GHOST_AGENT_MODE', 'ollama_base_url': 'OLLAMA_BASE_URL',
                 'ollama_model': 'OLLAMA_MODEL', 'model_timeout_seconds': 'GHOST_MODEL_TIMEOUT_SECONDS'}
        return cls(**{field: os.environ[name] for field, name in names.items() if name in os.environ})
