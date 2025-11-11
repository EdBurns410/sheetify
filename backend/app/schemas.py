from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class SheetHeader(BaseModel):
    name: str
    headers: List[str] = Field(default_factory=list)


class WorkbookSummary(BaseModel):
    file_id: str
    workbook_name: str
    sheets: List[SheetHeader]


class SignedUrlResponse(BaseModel):
    file_id: str
    signed_url: str
    expires_in_seconds: int = 900


class FinaliseFileRequest(BaseModel):
    file_id: str


class FinaliseFileResponse(BaseModel):
    file: WorkbookSummary


class MappingRequest(BaseModel):
    file_id: str
    mapping_json: dict


class MappingResponse(BaseModel):
    mapping_id: str
    registry_json: dict


class JobCreateRequest(BaseModel):
    title: str
    prompt_raw: str
    mapping_id: str


class JobPreview(BaseModel):
    job_id: str
    spec_preview: dict
    test_preview: List[dict]


class RunRequest(BaseModel):
    pass


class RunResponse(BaseModel):
    run_id: str


class RunStatus(BaseModel):
    run_id: str
    status: str
    started_at: datetime
    finished_at: Optional[datetime]
    logs_pointer: Optional[str] = None
    tests: List[dict] = Field(default_factory=list)
    summary: dict = Field(default_factory=dict)


class Artefact(BaseModel):
    kind: str
    display_name: str
    storage_key: str
    bytes: int


class ArtefactList(BaseModel):
    artefacts: List[Artefact]


class TemplateCreateRequest(BaseModel):
    job_id: Optional[str] = None
    mapping_id: Optional[str] = None
    name: str
    spec_json: Optional[dict] = None


class TemplateCreateResponse(BaseModel):
    template_id: str


class TemplateRunRequest(BaseModel):
    file_ids: List[str]


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "0.1.0"
