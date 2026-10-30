from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from rulebook_rag.generate import Generator

from fastapi.responses import FileResponse

import time
from collections import defaultdict, deque

from fastapi import Request
from pydantic import Field

state = {}
RATE_LIMIT = 5        # questions
WINDOW = 60           # per this many seconds
hits = defaultdict(deque)


def check_rate_limit(request: Request):
    # Fly.io puts the real visitor IP in this header; locally, use the direct connection
    ip = request.headers.get("fly-client-ip") or request.client.host
    now = time.time()
    q = hits[ip]
    while q and now - q[0] > WINDOW:     # forget requests older than the window
        q.popleft()
    if len(q) >= RATE_LIMIT:
        raise HTTPException(status_code=429, detail="Too many questions. Please wait a minute and try again.")
    q.append(now)

@asynccontextmanager
async def lifespan(app):
    state["gen"] = Generator()      # load models ONCE, when the server starts
    yield                           # the server runs while we're paused here


app = FastAPI(title="Rulebook RAG", lifespan=lifespan)


class Question(BaseModel):
    question: str = Field(max_length=500)


class Source(BaseModel):
    id: str
    game: str
    page: int


class Answer(BaseModel):
    answer: str
    sources: list[Source]


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/ask", response_model=Answer)
def ask(q: Question, request: Request):
    check_rate_limit(request)
    if not q.question.strip():
        raise HTTPException(status_code=400, detail="Question is empty.")
    text, chunks = state["gen"].answer(q.question)
    sources = [Source(id=c["id"], game=c["game"], page=c["page"]) for c in chunks]
    return Answer(answer=text, sources=sources)


@app.get("/")
def home():
       return FileResponse("src/rulebook_rag/static/index.html")