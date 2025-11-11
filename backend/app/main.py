from __future__ import annotations

from fastapi import FastAPI, HTTPException

from . import schemas
from .storage import InMemoryStore, seeded_store

app = FastAPI(title="Sheetify API", version="0.1.0")
store: InMemoryStore = seeded_store()


@app.get("/health", response_model=schemas.HealthResponse)
def health() -> schemas.HealthResponse:
    return schemas.HealthResponse()


@app.post("/v1/files", response_model=schemas.SignedUrlResponse)
def request_upload(filename: str, bytes: int) -> schemas.SignedUrlResponse:
    record = store.create_file(filename, bytes)
    return schemas.SignedUrlResponse(
        file_id=record["file_id"],
        signed_url=f"https://uploads.example.com/{record['file_id']}",
    )


@app.post("/v1/files:finalise", response_model=schemas.FinaliseFileResponse)
def finalise_file(payload: schemas.FinaliseFileRequest) -> schemas.FinaliseFileResponse:
    file_record = store.finalise_file(payload.file_id)
    summary = schemas.WorkbookSummary(
        file_id=file_record["file_id"],
        workbook_name=file_record["filename"],
        sheets=[
            schemas.SheetHeader(name=s["name"], headers=s["headers"]) for s in file_record["sheets"]
        ],
    )
    return schemas.FinaliseFileResponse(file=summary)


@app.post("/v1/mappings", response_model=schemas.MappingResponse)
def create_mapping(payload: schemas.MappingRequest) -> schemas.MappingResponse:
    if payload.file_id not in store.files:
        raise HTTPException(status_code=404, detail="file not found")
    created = store.create_mapping(payload.file_id, payload.mapping_json)
    return schemas.MappingResponse(**created)


@app.post("/v1/jobs", response_model=schemas.JobPreview)
def create_job(payload: schemas.JobCreateRequest) -> schemas.JobPreview:
    if payload.mapping_id not in store.mappings:
        raise HTTPException(status_code=404, detail="mapping not found")
    created = store.create_job(payload.title, payload.prompt_raw, payload.mapping_id)
    return schemas.JobPreview(**created)


@app.post("/v1/jobs/{job_id}/run", response_model=schemas.RunResponse)
def start_job_run(job_id: str) -> schemas.RunResponse:
    if job_id not in store.jobs:
        raise HTTPException(status_code=404, detail="job not found")
    run = store.create_run(job_id)
    store.start_run(run["run_id"])
    store.complete_run(run["run_id"])
    return schemas.RunResponse(run_id=run["run_id"])


@app.get("/v1/runs/{run_id}", response_model=schemas.RunStatus)
def get_run(run_id: str) -> schemas.RunStatus:
    if run_id not in store.runs:
        raise HTTPException(status_code=404, detail="run not found")
    run = store.get_run(run_id)
    return schemas.RunStatus(
        run_id=run["run_id"],
        status=run["status"],
        started_at=run["started_at"],
        finished_at=run["finished_at"],
        logs_pointer=f"https://logs.example.com/{run_id}",
        tests=run["tests"],
        summary=run["summary"],
    )


@app.get("/v1/runs/{run_id}/artefacts", response_model=schemas.ArtefactList)
def get_run_artefacts(run_id: str) -> schemas.ArtefactList:
    if run_id not in store.runs:
        raise HTTPException(status_code=404, detail="run not found")
    artefacts = store.get_run_artefacts(run_id)
    return schemas.ArtefactList(artefacts=[schemas.Artefact(**a) for a in artefacts])


@app.post("/v1/templates", response_model=schemas.TemplateCreateResponse)
def create_template(payload: schemas.TemplateCreateRequest) -> schemas.TemplateCreateResponse:
    if payload.job_id and payload.job_id not in store.jobs:
        raise HTTPException(status_code=404, detail="job not found")
    if payload.mapping_id and payload.mapping_id not in store.mappings:
        raise HTTPException(status_code=404, detail="mapping not found")
    template = store.create_template(payload.name, payload.job_id, payload.mapping_id, payload.spec_json)
    return schemas.TemplateCreateResponse(template_id=template["template_id"])


@app.post("/v1/templates/{template_id}/run", response_model=schemas.RunResponse)
def run_template(template_id: str, payload: schemas.TemplateRunRequest) -> schemas.RunResponse:
    if template_id not in store.templates:
        raise HTTPException(status_code=404, detail="template not found")
    run = store.create_template_run(template_id, payload.file_ids)
    store.start_run(run["run_id"])
    store.complete_run(run["run_id"])
    return schemas.RunResponse(run_id=run["run_id"])
