"""DocTalk FastAPI API — podcast generation service."""
import json
from datetime import datetime, timezone
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, HttpUrl
from azure.data.tables import TableServiceClient
from azure.storage.queue import QueueClient
from azure.identity import DefaultAzureCredential
import base64

from ..config import Config
from ..core.models import Job, JobStatus, QueueMessage

app = FastAPI(title="DocTalk API", version="2.0.0")
credential = DefaultAzureCredential()


class GenerateRequest(BaseModel):
    url: str
    style: str = "conversation"


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
    job = Job(url=request.url, style=request.style)

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


def _job_to_response(job: Job) -> JobResponse:
    return JobResponse(
        id=job.id,
        url=job.url,
        style=job.style,
        status=job.status.value,
        title=job.title,
        audio_url=job.audio_url,
        error=job.error,
        created_at=job.created_at,
        updated_at=job.updated_at,
    )
