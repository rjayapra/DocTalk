"""DocTalk core — shared library for scraping, script generation, and speech synthesis."""

from .scraper import fetch_docs
from .script_generator import generate_script
from .speech_synthesizer import synthesize_single_narrator, synthesize_conversation
from .models import Job, JobStatus, QueueMessage
from .pipeline import run_pipeline

__all__ = [
    "fetch_docs",
    "generate_script",
    "synthesize_single_narrator",
    "synthesize_conversation",
    "Job",
    "JobStatus",
    "QueueMessage",
    "run_pipeline",
]
