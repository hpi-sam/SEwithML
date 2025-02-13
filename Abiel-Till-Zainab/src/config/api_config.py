import os
from pydantic import BaseModel, SecretStr


class APIConfig(BaseModel):
    """API configuration with secret keys"""

    openai_api_key: SecretStr
    groq_api_key: SecretStr
    jina_api_key: SecretStr

    @classmethod
    def from_env(cls) -> "APIConfig":
        """Create config from environment variables"""
        return cls(
            openai_api_key=SecretStr(os.getenv("OPENAI_API_KEY", "")),
            groq_api_key=SecretStr(os.getenv("GROQ_API_KEY", "")),
            jina_api_key=SecretStr(os.getenv("JINA_API_KEY", "")),
        )
