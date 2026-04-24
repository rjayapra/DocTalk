# Trinity — Backend Developer

## Role
Implements the FastAPI backend, queue-triggered worker, and core library refactor.

## Responsibilities
- Refactor `src/` into `src/core/` shared library
- Build FastAPI API (`src/api/`) with endpoints: POST /generate, GET /jobs/{id}, GET /jobs, GET /health
- Build queue worker (`src/worker/`) with KEDA-compatible design (process one message, exit)
- Implement Table Storage CRUD for job state
- Implement Storage Queue enqueue/dequeue with poison queue handling
- Add blob upload step to speech pipeline
- Create Dockerfiles for API and Worker

## Context
- **Existing modules:** scraper.py, script_generator.py, speech_synthesizer.py, config.py, cli.py
- **GPT-5.1 quirk:** Use `max_completion_tokens` not `max_tokens`
- **Speech quirk:** SSML max 50 voice elements, chunking with MP3 concat
- **Worker design:** KEDA-compatible — NOT a polling loop. Process one queue message per invocation.
- **Table Storage PK:** `jobs` partition, RowKey = job_id; reverse-timestamp index for listing
- **Queue contract:** JSON message with job_id + url + style, visibility timeout 300s, dequeue_count < 5
