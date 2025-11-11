const API_BASE = window.API_BASE ?? "http://localhost:8000";

const state = {
  tools: [],
  selectedId: null,
};

const elements = {
  toolList: document.getElementById("tool-list"),
  detailPanel: document.getElementById("tool-detail"),
  emptyState: document.getElementById("empty-state"),
  detailTitle: document.getElementById("detail-title"),
  detailMeta: document.getElementById("detail-meta"),
  detailBlueprint: document.getElementById("detail-blueprint"),
  detailMemory: document.getElementById("detail-memory"),
  detailStorage: document.getElementById("detail-storage"),
  promptForm: document.getElementById("prompt-form"),
  promptInput: document.getElementById("prompt-input"),
  promptStatus: document.getElementById("prompt-status"),
  refreshButton: document.getElementById("refresh-tools"),
};

const formatDate = (value) => {
  try {
    return new Intl.DateTimeFormat(undefined, {
      dateStyle: "medium",
      timeStyle: "short",
    }).format(new Date(value));
  } catch (error) {
    return value;
  }
};

const showStatus = (message, tone = "info") => {
  elements.promptStatus.textContent = message;
  elements.promptStatus.dataset.tone = tone;
};

const renderList = () => {
  elements.toolList.innerHTML = "";
  if (state.tools.length === 0) {
    const empty = document.createElement("li");
    empty.textContent = "No tools saved yet";
    empty.className = "file-list__placeholder";
    elements.toolList.appendChild(empty);
    return;
  }

  state.tools.forEach((tool) => {
    const item = document.createElement("li");
    item.className = "file-list__item";
    if (tool.id === state.selectedId) {
      item.classList.add("active");
    }
    item.tabIndex = 0;
    item.addEventListener("click", () => selectTool(tool.id));
    item.addEventListener("keypress", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        selectTool(tool.id);
      }
    });

    const title = document.createElement("h3");
    title.textContent = tool.name;
    const meta = document.createElement("span");
    meta.textContent = formatDate(tool.created_at);

    item.appendChild(title);
    item.appendChild(meta);
    elements.toolList.appendChild(item);
  });
};

const renderDetail = () => {
  const selected = state.tools.find((tool) => tool.id === state.selectedId);
  if (!selected) {
    elements.detailPanel.hidden = true;
    elements.emptyState.hidden = false;
    return;
  }

  elements.detailPanel.hidden = false;
  elements.emptyState.hidden = true;

  elements.detailTitle.textContent = selected.name;
  elements.detailMeta.textContent = `Prompt saved · ${formatDate(selected.created_at)}`;
  elements.detailBlueprint.textContent = JSON.stringify(selected.mini_app, null, 2);
  elements.detailMemory.textContent = JSON.stringify(selected.memory, null, 2);
  elements.detailStorage.textContent = JSON.stringify(selected.storage, null, 2);
};

const selectTool = (toolId) => {
  state.selectedId = toolId;
  renderList();
  renderDetail();
};

const fetchTools = async () => {
  const response = await fetch(`${API_BASE}/tools`);
  if (!response.ok) {
    throw new Error("Unable to load tools");
  }
  const tools = await response.json();
  state.tools = tools;
  if (tools.length > 0 && !tools.some((tool) => tool.id === state.selectedId)) {
    state.selectedId = tools[0].id;
  }
  renderList();
  renderDetail();
};

const createTool = async (prompt) => {
  const response = await fetch(`${API_BASE}/tools`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ prompt }),
  });

  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    throw new Error(payload.detail || "Unable to create tool");
  }

  const tool = await response.json();
  state.tools = [tool, ...state.tools];
  state.selectedId = tool.id;
  renderList();
  renderDetail();
};

elements.promptForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const prompt = elements.promptInput.value.trim();
  if (!prompt) {
    showStatus("Enter a prompt to generate a tool.", "warning");
    return;
  }

  try {
    showStatus("Generating tool…", "info");
    await createTool(prompt);
    elements.promptForm.reset();
    showStatus("Tool saved to your workspace.", "success");
  } catch (error) {
    console.error(error);
    showStatus(error.message || "Something went wrong", "error");
  }
});

if (elements.refreshButton) {
  elements.refreshButton.addEventListener("click", async () => {
    try {
      showStatus("Refreshing saved tools…", "info");
      await fetchTools();
      showStatus("Tools synced.", "success");
    } catch (error) {
      console.error(error);
      showStatus(error.message || "Unable to refresh tools", "error");
    }
  });
}

fetchTools().catch((error) => {
  console.error(error);
  showStatus("Unable to load tools from the API.", "error");
});
