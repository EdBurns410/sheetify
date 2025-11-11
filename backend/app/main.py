from __future__ import annotations

import re
from datetime import datetime
from typing import List

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, select

from . import schemas
from .storage import get_session, init_db, seed_example, session_dependency

app = FastAPI(title="Sheetify Tool Builder", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    init_db()
    with get_session() as session:
        seed_example(session)
from fastapi import FastAPI, HTTPException

from . import schemas
from .storage import InMemoryStore, seeded_store

app = FastAPI(title="Sheetify API", version="0.1.0")
store: InMemoryStore = seeded_store()


@app.get("/health", response_model=schemas.HealthResponse)
def health() -> schemas.HealthResponse:
    return schemas.HealthResponse()


def _slugify(text: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9\s]", "", text).strip().lower()
    if not cleaned:
        return "tool"
    return re.sub(r"\s+", "-", cleaned)


def _title_from_prompt(prompt: str) -> str:
    words = [word for word in re.split(r"\s+", prompt.strip()) if word]
    if not words:
        return "Untitled Tool"
    sample = " ".join(words[:5])
    return sample.title()


def _build_tool_from_prompt(prompt: str) -> schemas.Tool:
    prompt_clean = prompt.strip()
    created = datetime.utcnow()
    title = _title_from_prompt(prompt_clean)
    slug = _slugify(title)
    mini_app = {
        "title": title,
        "prompt_summary": prompt_clean,
        "layout": {
            "sidebar": [
                {"component": "filePicker", "label": "Source data"},
                {"component": "notes", "label": "Insights"},
            ],
            "workspace": [
                {"component": "table", "label": "Preview table", "source": "primary"},
                {"component": "chart", "label": "Quick chart", "source": "primary"},
            ],
        },
        "actions": [
            {
                "id": "summarise",
                "label": "Summarise data",
                "description": "Runs an automated summary tailored to the prompt.",
            },
            {
                "id": "export",
                "label": "Export results",
                "description": "Packages the insights as a CSV download.",
            },
        ],
    }
    memory = {
        "events": [
            {
                "type": "creation",
                "timestamp": created.isoformat() + "Z",
                "message": f"Tool initialised from prompt: {prompt_clean}",
            }
        ]
    }
    storage = {
        "workspace_path": f"tools/{slug}.json",
        "files": [
            {
                "name": f"{slug}.json",
                "description": "Blueprint for the generated mini tool",
            }
        ],
    }
    return schemas.Tool(
        name=title,
        prompt=prompt_clean,
        mini_app=mini_app,
        memory=memory,
        storage=storage,
        created_at=created,
    )


@app.post("/tools", response_model=schemas.ToolRead, status_code=201)
def create_tool(
    payload: schemas.ToolCreate, session: Session = Depends(session_dependency)
) -> schemas.ToolRead:
    prompt = payload.prompt.strip()
    if not prompt:
        raise HTTPException(status_code=422, detail="Prompt cannot be empty.")

    tool = _build_tool_from_prompt(prompt)
    session.add(tool)
    session.commit()
    session.refresh(tool)
    return tool


@app.get("/tools", response_model=List[schemas.ToolRead])
def list_tools(session: Session = Depends(session_dependency)) -> List[schemas.ToolRead]:
    tools = session.exec(select(schemas.Tool).order_by(schemas.Tool.created_at.desc())).all()
    return tools


@app.get("/tools/{tool_id}", response_model=schemas.ToolRead)
def get_tool(tool_id: int, session: Session = Depends(session_dependency)) -> schemas.ToolRead:
    tool = session.get(schemas.Tool, tool_id)
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found.")
    return tool
