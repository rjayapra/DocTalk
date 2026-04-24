"""Job and queue message models for DocTalk Phase 2."""
import uuid
from datetime import datetime, timezone
from enum import Enum
from dataclasses import dataclass, field


class JobStatus(str, Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Job:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    url: str = ""
    style: str = "conversation"
    status: JobStatus = JobStatus.QUEUED
    title: str = ""
    audio_url: str = ""
    error: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    duration_seconds: float = 0.0

    def to_table_entity(self) -> dict:
        """Convert to Azure Table Storage entity."""
        return {
            "PartitionKey": "jobs",
            "RowKey": self.id,
            "url": self.url,
            "style": self.style,
            "status": self.status.value,
            "title": self.title,
            "audio_url": self.audio_url,
            "error": self.error,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "duration_seconds": self.duration_seconds,
        }

    @classmethod
    def from_table_entity(cls, entity: dict) -> "Job":
        return cls(
            id=entity["RowKey"],
            url=entity.get("url", ""),
            style=entity.get("style", "conversation"),
            status=JobStatus(entity.get("status", "queued")),
            title=entity.get("title", ""),
            audio_url=entity.get("audio_url", ""),
            error=entity.get("error", ""),
            created_at=entity.get("created_at", ""),
            updated_at=entity.get("updated_at", ""),
            duration_seconds=float(entity.get("duration_seconds", 0)),
        )


@dataclass
class QueueMessage:
    job_id: str = ""
    url: str = ""
    style: str = "conversation"
