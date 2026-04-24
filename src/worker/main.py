"""DocTalk Worker — processes podcast generation jobs from Azure Storage Queue."""
import json
import base64
import logging
import time
from datetime import datetime, timezone
from azure.storage.queue import QueueClient
from azure.data.tables import TableServiceClient
from azure.identity import DefaultAzureCredential

from ..config import Config
from ..core.models import Job, JobStatus, QueueMessage
from ..core.pipeline import run_pipeline

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("doctalk-worker")

VISIBILITY_TIMEOUT = 300  # 5 minutes
MAX_DEQUEUE_COUNT = 5
POISON_QUEUE_NAME = f"{Config.AZURE_STORAGE_QUEUE_NAME}-poison"

credential = DefaultAzureCredential()


def _get_queue_client(queue_name: str = None) -> QueueClient:
    account_url = f"https://{Config.AZURE_STORAGE_ACCOUNT_NAME}.queue.core.windows.net"
    return QueueClient(account_url=account_url, queue_name=queue_name or Config.AZURE_STORAGE_QUEUE_NAME, credential=credential)


def _get_table_client():
    account_url = f"https://{Config.AZURE_STORAGE_ACCOUNT_NAME}.table.core.windows.net"
    service = TableServiceClient(endpoint=account_url, credential=credential)
    return service.get_table_client(Config.AZURE_STORAGE_TABLE_NAME)


def _update_job_status(job_id: str, status: JobStatus, **kwargs):
    """Update job status in Table Storage."""
    table = _get_table_client()
    entity = {"PartitionKey": "jobs", "RowKey": job_id, "status": status.value, "updated_at": datetime.now(timezone.utc).isoformat()}
    entity.update(kwargs)
    table.update_entity(entity, mode="merge")


def process_one():
    """Process one message from the queue. KEDA-compatible: process and exit."""
    queue = _get_queue_client()
    messages = queue.receive_messages(max_messages=1, visibility_timeout=VISIBILITY_TIMEOUT)

    for msg in messages:
        job_id = None
        try:
            # Check dequeue count for poison handling
            if msg.dequeue_count >= MAX_DEQUEUE_COUNT:
                logger.warning(f"Message {msg.id} exceeded max dequeue count ({msg.dequeue_count}), moving to poison queue")
                _move_to_poison_queue(msg)
                queue.delete_message(msg)
                continue

            # Parse message
            decoded = base64.b64decode(msg.content).decode()
            payload = json.loads(decoded)
            job_id = payload["job_id"]
            logger.info(f"Processing job {job_id}")

            # Update status to processing
            _update_job_status(job_id, JobStatus.PROCESSING)

            # Build job object
            job = Job(id=job_id, url=payload["url"], style=payload.get("style", "conversation"))

            # Run pipeline
            job = run_pipeline(job, Config)

            # Update job as completed
            _update_job_status(
                job_id, JobStatus.COMPLETED,
                title=job.title,
                audio_url=job.audio_url,
                duration_seconds=job.duration_seconds,
            )

            # Delete message from queue
            queue.delete_message(msg)
            logger.info(f"Job {job_id} completed successfully")

        except Exception as e:
            logger.error(f"Failed to process message: {e}")
            try:
                if job_id:
                    _update_job_status(job_id, JobStatus.FAILED, error=str(e)[:500])
            except Exception:
                pass
            # Don't delete — will become visible again after timeout for retry


def _move_to_poison_queue(msg):
    """Move a message to the poison queue."""
    try:
        poison_queue = _get_queue_client(POISON_QUEUE_NAME)
        try:
            poison_queue.create_queue()
        except Exception:
            pass  # Already exists
        poison_queue.send_message(msg.content)
    except Exception as e:
        logger.error(f"Failed to move message to poison queue: {e}")


def main():
    """Entry point: process one message then exit (KEDA-compatible)."""
    logger.info("DocTalk Worker starting — processing one job")
    process_one()
    logger.info("DocTalk Worker done")


if __name__ == "__main__":
    main()
