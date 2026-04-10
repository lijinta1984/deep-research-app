import asyncio
import json
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


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.queues = {}
    init_db()
    yield


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
    app.state.queues[session_id] = queue
    background_tasks.add_task(run_research, request, session_id, queue)
    return {"session_id": session_id}


@app.get("/api/research/{session_id}/stream")
async def stream_research(session_id: str, request: Request):
    async def event_generator():
        queue = app.state.queues.get(session_id)
        if not queue:
            yield {"data": json.dumps({"type": "error", "message": "Session not found"})}
            return

        while True:
            if await request.is_disconnected():
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
    return list_sessions(limit=20)


@app.get("/api/sessions/{session_id}")
async def get_session_by_id(session_id: str):
    return get_session(session_id)


@app.delete("/api/sessions/{session_id}")
async def remove_session(session_id: str):
    delete_session(session_id)
    return {"deleted": True}
