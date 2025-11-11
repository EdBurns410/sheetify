# Sheetify SaaS Product Specification

## 1. Vision and Scope

Build a scalable SaaS where users upload CSV or XLSX, select worksheets, map headers, then describe a task in plain English.

The system plans, generates safe code, runs it in an isolated runtime, and returns results plus an audit trail.

First customers are data savvy operators who do repetitive spreadsheet jobs. The app turns ad hoc work into repeatable recipes.

Out of scope for MVP: real time collaboration in the same job, desktop agents, direct database connectors, custom Python packages per user.

## 2. User Roles

- **Visitor**: no account. Can only see marketing pages.
- **Member**: can create jobs, upload files, run tasks, download artefacts.
- **Admin**: all Member abilities plus team invites, role management, billing, quotas.
- **System agent roles**: Planner, Coder, Tester, Executor, Critic, Fixer. These are internal AI agents used by the platform.

## 3. End to End User Journey

1. Sign up or sign in.
2. Create a new task.
3. Upload one or more CSV or XLSX files.
4. If XLSX, select worksheets to include.
5. Review and edit auto suggested header mapping.
6. Write a natural language prompt.
7. Preview a generated plan and tests.
8. Run in a sandbox.
9. Review outputs, charts, logs, tests.
10. Save as a template or schedule it.
11. Re run with new files later.

## 4. Functional Requirements

### 4.1 Authentication and Tenancy

- Email plus password, magic link optional.
- Multi tenant Postgres with row level security.
- Session timeouts and refresh tokens.
- Admin can invite members by email.

### 4.2 File Ingestion

- Accept CSV, XLSX.
- Max file size per plan.
- Virus and content type checks.
- Store raw files in S3 compatible storage with signed URLs and expiry.
- Record checksum and size for dedupe.

### 4.3 Workbook and Sheet Discovery

- For each XLSX, detect all sheets and read row 1 as headers.
- For CSV, create a pseudo worksheet named CSV.
- Return JSON with workbook name, sheets, and header lists.
- For large files allow a header only read without scanning all rows.

### 4.4 Column Mapping

- Show a mapping UI with source headers on the left and target fields or freeform names on the right.
- Auto suggestions using normalisation and alias lists.
- Support ignore, rename, and required field checks with counts of nulls.
- Save mapping as a versioned object per workbook and sheet.
- Import and export mappings as JSON or CSV.

### 4.5 Path Addressing Syntax

- Users can reference any column using path notation: `/workbook/worksheet/header`.
- CSV uses the pseudo worksheet CSV.
- Support quoted segments for names containing slashes.
- Case insensitive lookup with original case preserved for display.
- On submit, resolve paths to stable column ids stored in a registry.

### 4.6 Task Specification

- Planner converts the prompt plus registry into a Task Spec JSON.
- Spec must include: inputs, bindings of path to column id, ops list, and tests.
- Supported ops for MVP: `select`, `filter`, `sort`, `dedupe`, `mutate`, `aggregate`, `pivot`, `join`, `fuzzy_match`, `standardise_dates`, `group window summary`, `type cast`, `regex extract`.
- Each op references columns by id.
- Tests include row count expectations, unique constraints, null checks, and sample invariants.

### 4.7 Agent Workflow

- **Planner**: builds the plan, validates paths, and proposes tests.
- **Coder**: converts the plan into Polars and or DuckDB code using approved templates only.
- **Tester**: runs on a sample subset before full execution.
- **Executor**: runs full code in a sandbox without internet.
- **Critic and Fixer**: parse errors and offer at most two retries with bounded edits.
- All agent steps and prompts are stored in run history.

### 4.8 Execution Environment

- Ephemeral containers or micro VMs with resource limits.
- Read only mount for inputs, a writeable temp for outputs.
- No outbound network access during execution.
- Timeouts per plan tier.
- Outputs saved to S3 with content hashes.

### 4.9 Results and Artefacts

- Download outputs as CSV and XLSX.
- Auto EDA summary: row counts, column types, missingness, top values.
- Chart suggestions for common summaries.
- Provide a Recipe bundle with the Task Spec, final code, tests, and a run summary JSON.
- Keep versioned run history with logs and metrics.

### 4.10 Templates and Scheduling

- Save any plan and mapping as a reusable template.
- Re run a template with new files.
- Optional scheduling with cron like UI.
- Email notification with links to artefacts.

### 4.11 Team Features

- Workspaces per team.
- Role based permissions.
- Shared templates and mappings.
- Organisation usage dashboard.

### 4.12 Billing and Quotas

- Stripe subscriptions plus metered usage for compute minutes and storage.
- Plan limits on file size, concurrency, timeouts, and history retention.
- Graceful error messages when limits hit.

### 4.13 API

- Signed upload endpoints.
- Jobs CRUD.
- Runs start and status.
- Artefact download via time limited signed URLs.
- Webhooks for run complete and failure events.

## 5. Non Functional Requirements

### 5.1 Security

- Data encrypted at rest and in transit.
- Secrets stored in a parameter store.
- No secrets in containers.
- Strict CORS and CSRF settings.
- Audit log for admin actions.
- PII detection on upload with simple pattern rules and a redaction option.

### 5.2 Reliability and Performance

- P99 plan generation under 3 seconds.
- P95 run queue start under 30 seconds for Pro.
- Horizontal scaling for workers.
- Idempotent endpoints for create and run.
- At least once delivery for webhooks.

### 5.3 Availability

- Target 99.5 percent for MVP.
- Graceful degradation when LLM is unavailable with cached templates and manual run.

### 5.4 Observability

- Structured logs with trace ids.
- Metrics: run count, success rate, median duration, OOM and timeout counts, queue latency.
- Error tracking in Sentry or similar.

### 5.5 Privacy and Compliance

- UK and EU data residency option.
- Right to be forgotten workflow.
- Data retention policy per plan.

## 6. Data Model Summary

- `tenants`: id, name, created_at
- `users`: id, tenant_id, email, role, created_at
- `files`: id, tenant_id, user_id, display_name, storage_key, checksum, bytes, mime, created_at
- `sheets`: id, file_id, name, header_row_index
- `columns`: id, sheet_id, header_display, header_norm, dtype_detected
- `mappings`: id, tenant_id, file_id, mapping_json, version, created_at
- `jobs`: id, tenant_id, user_id, title, prompt_raw, registry_json, spec_json, status, created_at
- `runs`: id, job_id, started_at, finished_at, status, cpu_sec, mem_mb, logs_key, tests_json, summary_json
- `artefacts`: id, run_id, kind, display_name, storage_key, bytes
- `templates`: id, tenant_id, name, mapping_id, spec_json, created_at
- `billing_usage`: id, tenant_id, month, compute_minutes, storage_gb

## 7. API Contract Outline

### Uploads

- `POST /v1/files:request url`
  - Input: filename, bytes, checksum
  - Output: signed URL, file_id
- `POST` direct to S3 using the signed URL
- `POST /v1/files:finalise`
  - Input: file_id
  - Output: file meta and detected sheets and headers

### Mapping

- `POST /v1/mappings`
  - Input: file_id, mapping_json
  - Output: mapping_id and registry_json

### Jobs and Runs

- `POST /v1/jobs`
  - Input: title, prompt_raw, mapping_id
  - Output: job_id, spec_preview, test_preview
- `POST /v1/jobs/{job_id}/run`
  - Output: run_id
- `GET /v1/runs/{run_id}`
  - Output: status, logs pointer, tests, summary, artefacts
- `GET /v1/runs/{run_id}/artefacts`
  - Output: list with signed URLs

### Templates

- `POST /v1/templates` from job or mapping
- `POST /v1/templates/{id}/run` with new files

### Webhooks

- `POST` to customer URL with run status, artefact list, and summary

## 8. Planner Specification and Guardrails

**Input to Planner**:

- User prompt
- Registry of files, sheets, columns with col ids and detected types
- Mapping choices and aliases
- Previous spec if editing

**Planner must**:

- Resolve all path references to valid col ids
- Emit a deterministic spec using only the approved ops
- Include tests that can be executed without external data
- Refuse to proceed if a path is ambiguous

**Rewriting rules**:

- If a header is ambiguous across sheets, ask for a disambiguation.
- If a column type is unknown, insert a type cast step with a safe default.

## 9. Executor Requirements

- Read only inputs from a mounted directory.
- Write only to a temp output directory.
- Emit a `RUN_SUMMARY.json` with input file hashes, row counts before and after each op, and test results.
- Package outputs into a zip plus individual file downloads.

## 10. Frontend Requirements

### Pages

- Sign in and sign up
- Dashboard with job list and run status
- New task wizard
- Mapping editor
- Plan preview and run page
- Run detail with logs, tests, charts, and downloads
- Templates library
- Billing and usage

### UX Details

- Upload with resumable chunks and a visible progress bar.
- Mapping grid with search and auto fill.
- Path helper that inserts correct `/workbook/worksheet/header` syntax as the user types.
- Diff view if schema drifts between versions.
- Accessible components with keyboard support.

## 11. AI Agent Design

- Use function calling to force JSON output for the plan.
- Temperature low for planning, slightly higher for critiquing error messages.
- Templates library of audited code blocks per op. The Coder composes these blocks rather than free writing.
- Tester always runs on a sample capped at 5k rows to fail fast.
- Critic reads stack traces and proposes a single minimal patch.
- Fixer applies at most two patches then stops.

## 12. Limits and Pricing for Launch

- **Free**: 50 MB per run, 1 concurrent run, 2 minute cap, 7 day history.
- **Pro**: 1 GB per run, 3 concurrent runs, 10 minute cap, 30 day history, scheduling.
- **Team**: shared workspaces, SSO, audit logs, webhooks, custom limits.

## 13. QA and Acceptance Criteria

### Happy Path

1. Upload a 2 sheet workbook.
2. System lists sheets and headers.
3. User accepts auto mapping with one manual fix.
4. Prompt references two columns via path.
5. Planner returns a valid spec in under 3 seconds.
6. Test on sample passes.
7. Full run completes under 60 seconds on 100k rows.
8. Output matches expected CSV and XLSX, row counts reconcile, tests pass.

### Edge Cases

- Header duplicates within a sheet. Expect a suffix to disambiguate.
- Ambiguous header across two sheets. Expect a prompt to choose.
- File with wrong extension. Expect a clear error.
- Run exceeds memory or time. Expect graceful abort and partial logs.
- Planner downtime. Expect a retry with exponential backoff and a human readable message.

## 14. Delivery Plan and Milestones

- **Milestone 1 – Foundation**: Auth, tenants, file uploads with signed URLs, sheet and header discovery, mapping UI, Postgres schema, S3 wiring.
- **Milestone 2 – Planning**: Registry, path syntax, Planner with function calling, JSON Spec, safe op set, tests preview.
- **Milestone 3 – Execution**: Sandbox runners, Polars templates, sample tests then full run, artefact packaging, run history.
- **Milestone 4 – UX Polish**: Charts, EDA summary, template save and re run, notifications.
- **Milestone 5 – Billing and Limits**: Stripe plans, quotas and enforcement, usage dashboard.

## 15. Engineering Checklist

- Repo with frontend and backend folders.
- Docker compose with Postgres, Redis, backend, frontend.
- `.env` and secrets template.
- CI on pull request for lint, type checks, unit tests.
- API smoke tests for upload, mapping, plan, run.
- Load test on 100 MB CSV.
- Observability dashboards and alerts.

## 16. Developer Quickstart

The repository now ships with a minimal vertical slice to help prototype the experience described above.

### Backend API (FastAPI)

1. `cd backend`
2. `python -m venv .venv && source .venv/bin/activate`
3. `pip install -r requirements.txt`
4. `uvicorn app.main:app --reload`

The server exposes the REST contract from section 7 with in-memory storage. Responses echo the specification structure so the frontend can be exercised without standing up the full platform.

### Frontend Console (static)

1. In another terminal, `cd frontend`
2. Serve the directory (for example `python -m http.server 3000`)
3. Navigate to `http://localhost:3000`

The console walks through upload, mapping, job creation, execution, and template flows by calling the FastAPI backend on `http://localhost:8000`.
