import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Configuration loaded from environment variables."""

    # Azure OpenAI
    AZURE_OPENAI_ENDPOINT: str = os.getenv("AZURE_OPENAI_ENDPOINT", "")
    AZURE_OPENAI_DEPLOYMENT_NAME: str = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-51")

    # Azure Speech
    AZURE_SPEECH_REGION: str = os.getenv("AZURE_SPEECH_REGION", "eastus2")
    AZURE_SPEECH_KEY: str = os.getenv("AZURE_SPEECH_KEY", "")
    AZURE_SPEECH_RESOURCE_ID: str = os.getenv("AZURE_SPEECH_RESOURCE_ID", "")

    # Azure Storage
    AZURE_STORAGE_ACCOUNT_NAME: str = os.getenv("AZURE_STORAGE_ACCOUNT_NAME", "")
    AZURE_STORAGE_CONTAINER_NAME: str = os.getenv("AZURE_STORAGE_CONTAINER_NAME", "podcasts")

    # Phase 2: Queue and Table
    AZURE_STORAGE_QUEUE_NAME: str = os.getenv("AZURE_STORAGE_QUEUE_NAME", "podcast-jobs")
    AZURE_STORAGE_TABLE_NAME: str = os.getenv("AZURE_STORAGE_TABLE_NAME", "podcastjobs")

    # Phase 2: API
    DOCTALK_API_URL: str = os.getenv("DOCTALK_API_URL", "")

    # Phase 2: App Insights
    APPLICATIONINSIGHTS_CONNECTION_STRING: str = os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING", "")

    @classmethod
    def validate(cls) -> list[str]:
        errors = []
        if not cls.AZURE_OPENAI_ENDPOINT:
            errors.append("AZURE_OPENAI_ENDPOINT is required")
        if not cls.AZURE_SPEECH_REGION:
            errors.append("AZURE_SPEECH_REGION is required")
        return errors

    @classmethod
    def validate_api(cls) -> list[str]:
        """Validate config for API/Worker mode (needs storage account)."""
        errors = cls.validate()
        if not cls.AZURE_STORAGE_ACCOUNT_NAME:
            errors.append("AZURE_STORAGE_ACCOUNT_NAME is required")
        return errors
