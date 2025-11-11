from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, JSON
from sqlmodel import Field, SQLModel


class ToolBase(SQLModel):
    name: str
    prompt: str
    mini_app: dict = Field(default_factory=dict, sa_column=Column(JSON, nullable=False))
    memory: dict = Field(default_factory=dict, sa_column=Column(JSON, nullable=False))
    storage: dict = Field(default_factory=dict, sa_column=Column(JSON, nullable=False))
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Tool(ToolBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)


class ToolCreate(SQLModel):
    prompt: str


class ToolRead(ToolBase):
    id: int

    class Config:
        orm_mode = True


class HealthResponse(SQLModel):
    status: str = "ok"
