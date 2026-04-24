"""DocTalk FastAPI API — podcast generation service."""
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
from azure.data.tables import TableServiceClient
from azure.storage.queue import QueueClient
from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions
from azure.identity import DefaultAzureCredential
import base64

from ..config import Config
from ..core.models import Job, JobStatus, QueueMessage
from .copilot import router as copilot_router

app = FastAPI(title="DocTalk API", version="2.0.0")

# CORS middleware for webapp access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(copilot_router)
credential = DefaultAzureCredential()


@app.get("/")
async def root():
    """Redirect root to webapp."""
    return RedirectResponse(url="/app/index.html")


class GenerateRequest(BaseModel):
    url: str
    style: str = "conversation"
    title: str = ""


class JobResponse(BaseModel):
    id: str
    url: str
    style: str
    status: str
    title: str
    audio_url: str
    error: str
    created_at: str
    updated_at: str


def _get_table_client():
    account_url = f"https://{Config.AZURE_STORAGE_ACCOUNT_NAME}.table.core.windows.net"
    service = TableServiceClient(endpoint=account_url, credential=credential)
    return service.get_table_client(Config.AZURE_STORAGE_TABLE_NAME)


def _get_queue_client():
    account_url = f"https://{Config.AZURE_STORAGE_ACCOUNT_NAME}.queue.core.windows.net"
    return QueueClient(account_url=account_url, queue_name=Config.AZURE_STORAGE_QUEUE_NAME, credential=credential)


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "doctalk-api", "version": "2.0.0"}


@app.post("/generate", response_model=JobResponse, status_code=202)
async def generate(request: GenerateRequest):
    """Submit a podcast generation job."""
    job = Job(url=request.url, style=request.style, title=request.title)

    # Save to Table Storage
    table = _get_table_client()
    table.upsert_entity(job.to_table_entity())

    # Enqueue message
    queue = _get_queue_client()
    msg = QueueMessage(job_id=job.id, url=job.url, style=job.style)
    # Storage Queue messages must be base64 encoded
    msg_json = json.dumps({"job_id": msg.job_id, "url": msg.url, "style": msg.style})
    encoded = base64.b64encode(msg_json.encode()).decode()
    queue.send_message(encoded, visibility_timeout=0, time_to_live=86400)

    return _job_to_response(job)


@app.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job(job_id: str):
    """Get job status and details."""
    table = _get_table_client()
    try:
        entity = table.get_entity(partition_key="jobs", row_key=job_id)
        job = Job.from_table_entity(entity)
        return _job_to_response(job)
    except Exception:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")


@app.get("/jobs", response_model=list[JobResponse])
async def list_jobs(limit: int = 20):
    """List recent jobs."""
    table = _get_table_client()
    entities = table.query_entities(
        query_filter="PartitionKey eq 'jobs'",
        select=["RowKey", "url", "style", "status", "title", "audio_url", "error", "created_at", "updated_at"],
    )
    jobs = []
    for entity in entities:
        jobs.append(_job_to_response(Job.from_table_entity(entity)))
        if len(jobs) >= limit:
            break
    return jobs


def _get_blob_service_client():
    account_url = f"https://{Config.AZURE_STORAGE_ACCOUNT_NAME}.blob.core.windows.net"
    return BlobServiceClient(account_url=account_url, credential=credential)


def _add_sas_token(audio_url: str) -> str:
    """Add a User Delegation SAS token to a blob URL for browser access."""
    if not audio_url or "?" in audio_url:
        return audio_url
    try:
        parts = audio_url.split(f"/{Config.AZURE_STORAGE_CONTAINER_NAME}/")
        if len(parts) != 2:
            return audio_url
        blob_name = parts[1]

        blob_service = _get_blob_service_client()

        start_time = datetime.now(timezone.utc)
        expiry_time = start_time + timedelta(hours=1)
        udk_expiry = start_time + timedelta(days=1)

        user_delegation_key = blob_service.get_user_delegation_key(
            key_start_time=start_time,
            key_expiry_time=udk_expiry,
        )

        sas_token = generate_blob_sas(
            account_name=Config.AZURE_STORAGE_ACCOUNT_NAME,
            container_name=Config.AZURE_STORAGE_CONTAINER_NAME,
            blob_name=blob_name,
            user_delegation_key=user_delegation_key,
            permission=BlobSasPermissions(read=True),
            expiry=expiry_time,
            content_type="audio/mpeg",
        )
        return f"{audio_url}?{sas_token}"
    except Exception as e:
        print(f"Warning: SAS generation failed: {e}")
        return audio_url


def _job_to_response(job: Job) -> JobResponse:
    return JobResponse(
        id=job.id,
        url=job.url,
        style=job.style,
        status=job.status.value,
        title=job.title,
        audio_url=_add_sas_token(job.audio_url),
        error=job.error,
        created_at=job.created_at,
        updated_at=job.updated_at,
    )


# Serve webapp static files (must be after all route definitions)
webapp_dir = Path(__file__).parent.parent / "webapp"
if webapp_dir.exists():
    app.mount("/app", StaticFiles(directory=str(webapp_dir), html=True), name="webapp")
