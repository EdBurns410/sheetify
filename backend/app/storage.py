from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

from sqlmodel import Session, SQLModel, create_engine, select

from . import schemas

DATABASE_URL = "sqlite:///./sheetify.db"
engine = create_engine(DATABASE_URL, echo=False, connect_args={"check_same_thread": False})


def init_db() -> None:
    SQLModel.metadata.create_all(engine)


@contextmanager
def get_session() -> Iterator[Session]:
    with Session(engine) as session:
        yield session


def session_dependency() -> Iterator[Session]:
    with get_session() as session:
        yield session


def seed_example(session: Session) -> None:
    if session.exec(select(schemas.Tool)).first():
        return
    tool = schemas.Tool(
        name="Sample KPI Tracker",
        prompt="Track weekly KPIs across uploaded spreadsheets",
        mini_app={
            "layout": "dashboard",
            "widgets": [
                {"type": "chart", "title": "Weekly KPI trend", "source": "kpis"},
                {"type": "table", "title": "Latest KPI snapshot", "source": "kpis"},
            ],
        },
        memory={
            "events": [
                {
                    "type": "creation",
                    "message": "Seeded demo tool for quickstart",
                }
            ]
        },
        storage={
            "workspace_path": "tools/sample-kpi-tracker.json",
            "files": [
                {
                    "name": "sample-kpi-tracker.json",
                    "size_bytes": 512,
                }
            ],
        },
    )
    session.add(tool)
    session.commit()
