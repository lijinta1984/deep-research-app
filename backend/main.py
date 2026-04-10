import asyncio
import json
import time
import uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse
from dotenv import load_dotenv
import os

from backend.db.database import init_db, list_sessions, get_session, delete_session
from backend.agent.orchestrator import run_research
from backend.models.schemas import ResearchRequest, ResearchStep

load_dotenv()


QUEUE_TTL_SECONDS = 600  # 10 minutes — abandon threshold for unread queues


async def _cleanup_stale_queues(app: FastAPI):
    """Periodic task that removes queues older than QUEUE_TTL_SECONDS."""
    while True:
        await asyncio.sleep(60)
        now = time.time()
        stale = [sid for sid, (_, ts) in app.state.queues.items() if now - ts > QUEUE_TTL_SECONDS]
        for sid in stale:
            app.state.queues.pop(sid, None)


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.queues = {}  # {session_id: (asyncio.Queue, created_timestamp)}
    init_db()
    cleanup_task = asyncio.create_task(_cleanup_stale_queues(app))
    yield
    cleanup_task.cancel()


app = FastAPI(title="Deep Research API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:5173").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Routes ---


@app.post("/api/research")
async def start_research(request: ResearchRequest, background_tasks: BackgroundTasks):
    session_id = str(uuid.uuid4())
    queue = asyncio.Queue()
    app.state.queues[session_id] = (queue, time.time())
    background_tasks.add_task(run_research, request, session_id, queue)
    return {"session_id": session_id}


@app.get("/api/research/{session_id}/stream")
async def stream_research(session_id: str, request: Request):
    async def event_generator():
        entry = app.state.queues.get(session_id)
        if not entry:
            yield {"data": json.dumps({"type": "error", "message": "Session not found"})}
            return
        queue = entry[0]
        if not queue:
            yield {"data": json.dumps({"type": "error", "message": "Queue is empty"})}
            return

        while True:
            if await request.is_disconnected():
                app.state.queues.pop(session_id, None)
                break
            try:
                step = await asyncio.wait_for(queue.get(), timeout=1.0)
                yield {"data": json.dumps(step.model_dump())}
                if step.type in ("complete", "error"):
                    # Clean up queue from state after session ends
                    app.state.queues.pop(session_id, None)
                    break
            except asyncio.TimeoutError:
                # Keepalive ping — prevents browser from closing the SSE connection
                yield {"data": json.dumps({"type": "ping", "message": ""})}

    return EventSourceResponse(event_generator())


@app.get("/api/sessions")
async def get_sessions():
    return await asyncio.to_thread(list_sessions, 20)


@app.get("/api/sessions/{session_id}")
async def get_session_by_id(session_id: str):
    return await asyncio.to_thread(get_session, session_id)


@app.delete("/api/sessions/{session_id}")
async def remove_session(session_id: str):
    await asyncio.to_thread(delete_session, session_id)
    return {"deleted": True}
