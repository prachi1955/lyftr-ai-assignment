import os
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import time

load_dotenv()
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Header

from database import init_db, save_message, get_messages
from schemas import ChatRequest
from llm import generate_response, MODEL_NAME, parse_simulated_failures, API_KEYS
DEFAULT_SYSTEM_PROMPT = "You are a helpful AI assistant."
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create the SQLite tables when the backend starts
    await init_db()
    yield


app = FastAPI(lifespan=lifespan)
allowed_origins = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:3000"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "keys_configured": len(API_KEYS),
        "cache_enabled": True
    }
@app.post("/chat")
async def chat(
    request: ChatRequest,
    x_simulate_failure: str = Header(default=None)
):

    history = await get_messages(request.session_id)

    messages = []

    system_prompt = request.system_prompt or DEFAULT_SYSTEM_PROMPT

    messages.append({
       "role": "system",
        "content": system_prompt
    })

    for message in history:
       messages.append({
          "role": message["role"],
          "content": message["content"]
    })

    messages.append({
       "role": "user",
       "content": request.message
})
    failure_simulation_enabled = (
    os.getenv("ENABLE_FAILURE_SIMULATION", "false").lower() == "true"
)

    simulated_failures = {}

    if failure_simulation_enabled:
       simulated_failures = parse_simulated_failures(
        x_simulate_failure
    )
    start_time = time.perf_counter()

    try:
        result = await generate_response(
        messages,
        simulated_failures=simulated_failures
)
    except Exception:
        raise HTTPException(
            status_code=503,
            detail="all providers unavailable"
        )

    latency_ms = int((time.perf_counter() - start_time) * 1000)

    response = result["response"]
    key_id = result["key_id"]
    fallback_attempts = result["fallback_attempts"]
    cache_hit = result["cache_hit"]

    reply = response.choices[0].message.content
    usage = response.usage

    metadata = {
        "resolution_source": "LLM_CACHE" if cache_hit else "LIVE_INFERENCE",
        "model": MODEL_NAME,
        "latency_ms": latency_ms,
        "input_tokens": usage.prompt_tokens,
        "output_tokens": usage.completion_tokens,
        "key_id": key_id,
        "fallback_attempts": fallback_attempts
    }

    await save_message(
        session_id=request.session_id,
        role="user",
        content=request.message
    )

    await save_message(
        session_id=request.session_id,
        role="assistant",
        content=reply,
        metadata=metadata
    )

    return {
        "session_id": request.session_id,
        "reply": reply,
        "metadata": metadata
    }
@app.get("/sessions/{session_id}/messages")
async def session_messages(session_id: str):
    messages = await get_messages(session_id)

    if not messages:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=404,
            detail="session not found"
        )

    return {
        "session_id": session_id,
        "messages": messages
    }