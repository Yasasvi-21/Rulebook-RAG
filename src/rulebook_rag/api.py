from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from rulebook_rag.generate import Generator

from fastapi.responses import FileResponse

state = {}


@asynccontextmanager
async def lifespan(app):
    state["gen"] = Generator()      # load models ONCE, when the server starts
    yield                           # the server runs while we're paused here


app = FastAPI(title="Rulebook RAG", lifespan=lifespan)


class Question(BaseModel):
    question: str


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
def ask(q: Question):
    if not q.question.strip():
        raise HTTPException(status_code=400, detail="Question is empty.")
    text, chunks = state["gen"].answer(q.question)
    sources = [Source(id=c["id"], game=c["game"], page=c["page"]) for c in chunks]
    return Answer(answer=text, sources=sources)


@app.get("/")
def home():
       return FileResponse("src/rulebook_rag/static/index.html")