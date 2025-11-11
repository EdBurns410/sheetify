const API_BASE = "http://localhost:8000";

const output = (elementId, payload) => {
  const target = document.getElementById(elementId);
  target.textContent = JSON.stringify(payload, null, 2);
};

const handle = (formId, callback) => {
  const form = document.getElementById(formId);
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    form.classList.remove("error");
    try {
      await callback(new FormData(form));
    } catch (error) {
      form.classList.add("error");
      alert(error.message || "Unexpected error");
    }
  });
};

handle("auth-form", async (data) => {
  localStorage.setItem("sheetify.auth", JSON.stringify({
    email: data.get("auth-email"),
    token: `demo-${Date.now()}`,
  }));
  output("file-output", { message: "Signed in locally" });
});

handle("file-form", async (data) => {
  const response = await fetch(`${API_BASE}/v1/files?filename=${encodeURIComponent(
    data.get("file-name")
  )}&bytes=${encodeURIComponent(data.get("file-size"))}`, {
    method: "POST",
  });
  const payload = await response.json();
  if (!response.ok) throw new Error(payload.detail || "Upload request failed");
  output("file-output", payload);
  document.getElementById("finalise-file-id").value = payload.file_id;
  document.getElementById("mapping-file-id").value = payload.file_id;
});

handle("finalise-form", async (data) => {
  const response = await fetch(`${API_BASE}/v1/files:finalise`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ file_id: data.get("finalise-file-id") }),
  });
  const payload = await response.json();
  if (!response.ok) throw new Error(payload.detail || "Finalise failed");
  output("finalise-output", payload);
});

handle("mapping-form", async (data) => {
  let mapping;
  try {
    mapping = JSON.parse(data.get("mapping-json"));
  } catch (error) {
    throw new Error("Mapping JSON is invalid");
  }
  const response = await fetch(`${API_BASE}/v1/mappings`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      file_id: data.get("mapping-file-id"),
      mapping_json: mapping,
    }),
  });
  const payload = await response.json();
  if (!response.ok) throw new Error(payload.detail || "Mapping failed");
  output("mapping-output", payload);
  document.getElementById("job-mapping-id").value = payload.mapping_id;
  document.getElementById("template-mapping-id").value = payload.mapping_id;
});

handle("job-form", async (data) => {
  const response = await fetch(`${API_BASE}/v1/jobs`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      mapping_id: data.get("job-mapping-id"),
      title: data.get("job-title"),
      prompt_raw: data.get("job-prompt"),
    }),
  });
  const payload = await response.json();
  if (!response.ok) throw new Error(payload.detail || "Job creation failed");
  output("job-output", payload);
  document.getElementById("run-job-id").value = payload.job_id;
  document.getElementById("template-job-id").value = payload.job_id;
});

handle("run-form", async (data) => {
  const jobId = data.get("run-job-id");
  const response = await fetch(`${API_BASE}/v1/jobs/${jobId}/run`, {
    method: "POST",
  });
  const payload = await response.json();
  if (!response.ok) throw new Error(payload.detail || "Run failed");
  output("run-output", payload);
  document.getElementById("status-run-id").value = payload.run_id;
  document.getElementById("artefact-run-id").value = payload.run_id;
  document.getElementById("template-run-files").value = document
    .getElementById("template-run-files")
    .value || document.getElementById("mapping-file-id").value;
});

handle("status-form", async (data) => {
  const runId = data.get("status-run-id");
  const response = await fetch(`${API_BASE}/v1/runs/${runId}`);
  const payload = await response.json();
  if (!response.ok) throw new Error(payload.detail || "Status failed");
  output("status-output", payload);
});

handle("artefact-form", async (data) => {
  const runId = data.get("artefact-run-id");
  const response = await fetch(`${API_BASE}/v1/runs/${runId}/artefacts`);
  const payload = await response.json();
  if (!response.ok) throw new Error(payload.detail || "Artefact query failed");
  output("artefact-output", payload);
});

handle("template-form", async (data) => {
  const response = await fetch(`${API_BASE}/v1/templates`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      name: data.get("template-name"),
      job_id: data.get("template-job-id") || null,
      mapping_id: data.get("template-mapping-id") || null,
    }),
  });
  const payload = await response.json();
  if (!response.ok) throw new Error(payload.detail || "Template creation failed");
  output("template-output", payload);
  document.getElementById("template-run-id").value = payload.template_id;
});

handle("template-run-form", async (data) => {
  const templateId = data.get("template-run-id");
  const files = data
    .get("template-run-files")
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
  const response = await fetch(`${API_BASE}/v1/templates/${templateId}/run`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ file_ids: files }),
  });
  const payload = await response.json();
  if (!response.ok) throw new Error(payload.detail || "Template run failed");
  output("template-run-output", payload);
});
