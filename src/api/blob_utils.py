"""Utilities for generating SAS-signed blob URLs."""
import logging
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse

from azure.identity import DefaultAzureCredential
from azure.storage.blob import (
    BlobSasPermissions,
    BlobServiceClient,
    generate_blob_sas,
)

logger = logging.getLogger(__name__)

_SAS_EXPIRY_HOURS = 1


def add_sas_to_url(blob_url: str, account_name: str) -> str:
    """Append a user-delegation SAS token to an Azure Blob Storage URL.

    Returns the original URL unchanged if it is empty or not a blob URL.
    Uses managed identity (DefaultAzureCredential) — no connection strings.
    The managed identity needs Storage Blob Data Reader + Storage Blob Delegator roles.
    """
    if not blob_url or ".blob.core.windows.net" not in blob_url:
        return blob_url or ""

    try:
        parsed = urlparse(blob_url)
        # Path format: /<container>/<blob_name>
        path_parts = parsed.path.lstrip("/").split("/", 1)
        if len(path_parts) < 2:
            logger.warning("Could not parse container/blob from URL: %s", blob_url)
            return blob_url

        container_name, blob_name = path_parts

        credential = DefaultAzureCredential()
        account_url = f"https://{account_name}.blob.core.windows.net"
        blob_service = BlobServiceClient(account_url=account_url, credential=credential)

        now = datetime.now(timezone.utc)
        user_delegation_key = blob_service.get_user_delegation_key(
            key_start_time=now - timedelta(minutes=5),
            key_expiry_time=now + timedelta(hours=_SAS_EXPIRY_HOURS),
        )

        sas_token = generate_blob_sas(
            account_name=account_name,
            container_name=container_name,
            blob_name=blob_name,
            user_delegation_key=user_delegation_key,
            permission=BlobSasPermissions(read=True),
            expiry=now + timedelta(hours=_SAS_EXPIRY_HOURS),
            start=now - timedelta(minutes=5),
        )

        return f"{blob_url}?{sas_token}"

    except Exception:
        logger.exception("Failed to generate SAS token for %s", blob_url)
        return blob_url
