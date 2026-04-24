"""End-to-end podcast generation pipeline."""
import os
import time
import tempfile
from azure.storage.blob import BlobServiceClient
from azure.identity import DefaultAzureCredential

from .scraper import fetch_docs
from .script_generator import generate_script
from .speech_synthesizer import synthesize_single_narrator, synthesize_conversation
from .models import Job, JobStatus


def run_pipeline(job: Job, config) -> Job:
    """Run the full podcast generation pipeline.

    Steps: scrape → generate script → synthesize audio → upload blob → update job
    """
    # Step 1: Scrape
    docs = fetch_docs(job.url)
    job.title = docs["title"]

    # Step 2: Generate script
    script = generate_script(docs, style=job.style)

    # Step 3: Synthesize to temp file
    temp_dir = tempfile.mkdtemp(prefix="doctalk_")
    temp_path = os.path.join(temp_dir, "podcast.mp3")

    try:
        if job.style == "single":
            synthesize_single_narrator(script, temp_path)
        else:
            synthesize_conversation(script, temp_path)

        # Step 4: Upload to blob
        blob_name = f"{job.id}.mp3"
        blob_url = _upload_to_blob(temp_path, blob_name, config)
        job.audio_url = blob_url
        job.status = JobStatus.COMPLETED

        # Get file size for duration estimate
        file_size = os.path.getsize(temp_path)
        job.duration_seconds = file_size / (128 * 1024 / 8)  # rough estimate from bitrate
    finally:
        # Cleanup temp files
        for attempt in range(3):
            try:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                os.rmdir(temp_dir)
                break
            except OSError:
                time.sleep(0.5)

    return job


def _upload_to_blob(file_path: str, blob_name: str, config) -> str:
    """Upload file to Azure Blob Storage and return the URL."""
    credential = DefaultAzureCredential()
    account_url = f"https://{config.AZURE_STORAGE_ACCOUNT_NAME}.blob.core.windows.net"
    blob_service = BlobServiceClient(account_url=account_url, credential=credential)
    container_client = blob_service.get_container_client(config.AZURE_STORAGE_CONTAINER_NAME)

    with open(file_path, "rb") as data:
        container_client.upload_blob(name=blob_name, data=data, overwrite=True)

    return f"{account_url}/{config.AZURE_STORAGE_CONTAINER_NAME}/{blob_name}"
