from __future__ import annotations

from datetime import datetime
from typing import Dict, List
from uuid import uuid4


class InMemoryStore:
    def __init__(self) -> None:
        self.files: Dict[str, dict] = {}
        self.mappings: Dict[str, dict] = {}
        self.jobs: Dict[str, dict] = {}
        self.runs: Dict[str, dict] = {}
        self.templates: Dict[str, dict] = {}

    def create_file(self, filename: str, bytes_size: int) -> dict:
        file_id = str(uuid4())
        record = {
            "file_id": file_id,
            "filename": filename,
            "bytes": bytes_size,
            "checksum": str(uuid4()).replace("-", ""),
            "created_at": datetime.utcnow(),
            "sheets": [
                {
                    "name": "Sheet1",
                    "headers": ["id", "name", "value"],
                }
            ],
        }
        self.files[file_id] = record
        return record

    def finalise_file(self, file_id: str) -> dict:
        return self.files[file_id]

    def create_mapping(self, file_id: str, mapping_json: dict) -> dict:
        mapping_id = str(uuid4())
        registry = {
            "file_id": file_id,
            "columns": [
                {
                    "path": "/workbook/Sheet1/id",
                    "column_id": "col-1",
                },
                {
                    "path": "/workbook/Sheet1/value",
                    "column_id": "col-2",
                },
            ],
        }
        self.mappings[mapping_id] = {
            "mapping_json": mapping_json,
            "registry": registry,
            "created_at": datetime.utcnow(),
        }
        return {"mapping_id": mapping_id, "registry_json": registry}

    def create_job(self, title: str, prompt: str, mapping_id: str) -> dict:
        job_id = str(uuid4())
        spec_preview = {
            "inputs": [
                {
                    "mapping_id": mapping_id,
                    "binding": "primary",
                }
            ],
            "ops": [
                {
                    "op": "select",
                    "columns": ["col-1", "col-2"],
                }
            ],
        }
        tests = [
            {"type": "row_count_greater_than", "value": 0},
        ]
        record = {
            "job_id": job_id,
            "title": title,
            "prompt": prompt,
            "mapping_id": mapping_id,
            "spec_preview": spec_preview,
            "tests": tests,
            "created_at": datetime.utcnow(),
        }
        self.jobs[job_id] = record
        return {"job_id": job_id, "spec_preview": spec_preview, "test_preview": tests}

    def create_run(self, job_id: str) -> dict:
        run_id = str(uuid4())
        record = {
            "run_id": run_id,
            "job_id": job_id,
            "status": "queued",
            "started_at": datetime.utcnow(),
            "finished_at": None,
            "tests": [],
            "summary": {},
        }
        self.runs[run_id] = record
        return record

    def start_run(self, run_id: str) -> None:
        record = self.runs[run_id]
        record["status"] = "running"

    def complete_run(self, run_id: str) -> None:
        record = self.runs[run_id]
        record["status"] = "succeeded"
        record["finished_at"] = datetime.utcnow()
        record["tests"] = [{"type": "row_count", "result": "passed"}]
        record["summary"] = {
            "row_counts": {"before": 100, "after": 98},
            "notes": "Sample run completed successfully.",
        }

    def get_run(self, run_id: str) -> dict:
        return self.runs[run_id]

    def get_run_artefacts(self, run_id: str) -> List[dict]:
        return [
            {
                "kind": "csv",
                "display_name": "output.csv",
                "storage_key": f"artefacts/{run_id}/output.csv",
                "bytes": 1024,
            }
        ]

    def create_template(self, name: str, job_id: str | None, mapping_id: str | None, spec_json: dict | None) -> dict:
        template_id = str(uuid4())
        record = {
            "template_id": template_id,
            "name": name,
            "job_id": job_id,
            "mapping_id": mapping_id,
            "spec_json": spec_json or {},
            "created_at": datetime.utcnow(),
        }
        self.templates[template_id] = record
        return record

    def create_template_run(self, template_id: str, file_ids: List[str]) -> dict:
        template = self.templates[template_id]
        run = self.create_run(template.get("job_id", "unknown"))
        run["files"] = file_ids
        return run


def seeded_store() -> InMemoryStore:
    store = InMemoryStore()
    file_record = store.create_file("demo.csv", 512)
    mapping = store.create_mapping(file_record["file_id"], {"columns": []})
    job = store.create_job("Demo job", "Summarise", mapping["mapping_id"])
    run = store.create_run(job["job_id"])
    store.start_run(run["run_id"])
    store.complete_run(run["run_id"])
    return store
