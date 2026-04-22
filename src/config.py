import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Configuration loaded from environment variables."""

    AZURE_OPENAI_ENDPOINT: str = os.getenv("AZURE_OPENAI_ENDPOINT", "")
    AZURE_OPENAI_DEPLOYMENT_NAME: str = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-51")
    AZURE_SPEECH_REGION: str = os.getenv("AZURE_SPEECH_REGION", "eastus2")
    AZURE_SPEECH_KEY: str = os.getenv("AZURE_SPEECH_KEY", "")
    AZURE_SPEECH_RESOURCE_ID: str = os.getenv("AZURE_SPEECH_RESOURCE_ID", "")
    AZURE_STORAGE_ACCOUNT_NAME: str = os.getenv("AZURE_STORAGE_ACCOUNT_NAME", "")
    AZURE_STORAGE_CONTAINER_NAME: str = os.getenv("AZURE_STORAGE_CONTAINER_NAME", "podcasts")

    @classmethod
    def validate(cls) -> list[str]:
        errors = []
        if not cls.AZURE_OPENAI_ENDPOINT:
            errors.append("AZURE_OPENAI_ENDPOINT is required")
        if not cls.AZURE_SPEECH_REGION:
            errors.append("AZURE_SPEECH_REGION is required")
        return errors
