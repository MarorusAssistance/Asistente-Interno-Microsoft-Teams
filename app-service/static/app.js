const samples = [
  "Como se registra una entrega parcial en ventana critica en LogiCore ERP?",
  "Como solicito acceso temporal a SafeGate para personal externo?",
  "Que debo revisar si RutaNexo no deja cerrar una ruta?",
  "Tengo un bloqueo de pedido intercentro en LogiCore ERP.",
  "Soy nuevo en operaciones. Que pasos de onboarding debo completar?",
  "No encuentro solucion para un error nuevo en AlmaTrack WMS.",
  "No util, la respuesta no me sirve.",
];

const state = {
  apiBase: "",
  userId: "",
  conversationId: null,
  lastMessageId: null,
  busy: false,
};

const elements = {
  apiBaseInput: document.querySelector("#apiBaseInput"),
  userIdInput: document.querySelector("#userIdInput"),
  sameOriginButton: document.querySelector("#sameOriginButton"),
  localButton: document.querySelector("#localButton"),
  healthButton: document.querySelector("#healthButton"),
  healthStatus: document.querySelector("#healthStatus"),
  deepStatus: document.querySelector("#deepStatus"),
  messages: document.querySelector("#messages"),
  chatForm: document.querySelector("#chatForm"),
  messageInput: document.querySelector("#messageInput"),
  sendButton: document.querySelector("#sendButton"),
  samples: document.querySelector("#samples"),
  resetButton: document.querySelector("#resetButton"),
  sources: document.querySelector("#sources"),
  sourceCount: document.querySelector("#sourceCount"),
  usefulButton: document.querySelector("#usefulButton"),
  notUsefulButton: document.querySelector("#notUsefulButton"),
  feedbackStatus: document.querySelector("#feedbackStatus"),
  rawResponse: document.querySelector("#rawResponse"),
};

function defaultApiBase() {
  if (window.location.protocol.startsWith("http")) {
    return `${window.location.origin}/api`;
  }
  return "http://127.0.0.1:8000/api";
}

function normalizeBase(value) {
  return value.trim().replace(/\/+$/, "");
}

function loadState() {
  state.apiBase = normalizeBase(localStorage.getItem("logiassist.apiBase") || defaultApiBase());
  state.userId =
    localStorage.getItem("logiassist.userId") || `web-demo-${Math.random().toString(16).slice(2, 8)}`;
  elements.apiBaseInput.value = state.apiBase;
  elements.userIdInput.value = state.userId;
}

function persistConnection() {
  state.apiBase = normalizeBase(elements.apiBaseInput.value || defaultApiBase());
  state.userId = elements.userIdInput.value.trim() || "web-demo";
  elements.apiBaseInput.value = state.apiBase;
  elements.userIdInput.value = state.userId;
  localStorage.setItem("logiassist.apiBase", state.apiBase);
  localStorage.setItem("logiassist.userId", state.userId);
}

function setPill(element, text, kind) {
  element.textContent = text;
  element.className = `pill ${kind}`;
}

function appendMessage(role, text, kind = role) {
  const item = document.createElement("article");
  item.className = `message ${kind}`;

  const meta = document.createElement("span");
  meta.className = "message-meta";
  meta.textContent = role === "user" ? "Usuario" : role === "error" ? "Error" : "Asistente";

  const body = document.createElement("span");
  body.textContent = text;

  item.append(meta, body);
  elements.messages.append(item);
  elements.messages.scrollTop = elements.messages.scrollHeight;
}

function truncate(value, maxLength = 230) {
  const text = String(value || "").trim();
  if (text.length <= maxLength) {
    return text;
  }
  return `${text.slice(0, maxLength - 1).trim()}...`;
}

function renderSources(sources = [], relatedIncidents = []) {
  elements.sourceCount.textContent = String(sources.length);
  elements.sources.innerHTML = "";

  if (!sources.length && !relatedIncidents.length) {
    elements.sources.className = "source-list empty";
    elements.sources.textContent = "Sin fuentes para esta respuesta.";
    return;
  }

  elements.sources.className = "source-list";
  for (const source of sources) {
    const item = document.createElement("div");
    item.className = "source-item";

    const title = document.createElement("span");
    title.className = "source-title";
    title.textContent = source.title || `${source.source_type}:${source.source_id}`;

    const meta = document.createElement("span");
    meta.className = "source-meta";
    meta.textContent = `${source.source_type}:${source.source_id} · chunk ${source.chunk_id}`;

    const excerpt = document.createElement("span");
    excerpt.className = "source-excerpt";
    excerpt.textContent = truncate(source.source_url || source.excerpt);

    item.append(title, meta, excerpt);
    elements.sources.append(item);
  }

  for (const incident of relatedIncidents.slice(0, 3)) {
    const item = document.createElement("div");
    item.className = "source-item";
    const title = document.createElement("span");
    title.className = "source-title";
    title.textContent = incident.external_id || `incident:${incident.id}`;
    const excerpt = document.createElement("span");
    excerpt.className = "source-excerpt";
    excerpt.textContent = `${incident.title || "Incidencia relacionada"} (${incident.status || "sin estado"})`;
    item.append(title, excerpt);
    elements.sources.append(item);
  }
}

async function requestJson(path, options = {}) {
  persistConnection();
  const response = await fetch(`${state.apiBase}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
  });
  const text = await response.text();
  let payload = null;
  if (text) {
    try {
      payload = JSON.parse(text);
    } catch {
      payload = { raw: text };
    }
  }
  if (!response.ok) {
    const detail = payload?.detail || payload?.raw || `${response.status} ${response.statusText}`;
    throw new Error(Array.isArray(detail) ? JSON.stringify(detail) : String(detail));
  }
  return payload;
}

async function checkHealth() {
  setPill(elements.healthStatus, "Health comprobando", "neutral");
  setPill(elements.deepStatus, "Deep health comprobando", "neutral");
  try {
    await requestJson("/health");
    setPill(elements.healthStatus, "Health OK", "ok");
  } catch (error) {
    setPill(elements.healthStatus, "Health FAIL", "fail");
  }

  try {
    const report = await requestJson("/health/deep");
    const chunks = report?.checks?.chunks?.count;
    const suffix = typeof chunks === "number" ? ` · ${chunks} chunks` : "";
    setPill(elements.deepStatus, `Deep health OK${suffix}`, "ok");
  } catch (error) {
    setPill(elements.deepStatus, "Deep health FAIL", "fail");
  }
}

async function sendMessage(message) {
  if (!message || state.busy) {
    return;
  }

  state.busy = true;
  elements.sendButton.disabled = true;
  appendMessage("user", message);

  try {
    const payload = {
      conversation_id: state.conversationId,
      user_id: state.userId,
      message,
      channel: "web-demo",
    };
    const response = await requestJson("/chat", {
      method: "POST",
      body: JSON.stringify(payload),
    });

    state.conversationId = response.conversation_id;
    state.lastMessageId = response.message_id;
    appendMessage("assistant", response.answer || response.fallback_text || "Respuesta vacia");
    renderSources(response.sources, response.related_incidents);
    elements.rawResponse.textContent = JSON.stringify(response, null, 2);
    setFeedbackEnabled(Boolean(response.conversation_id));
  } catch (error) {
    appendMessage("error", error.message, "error");
  } finally {
    state.busy = false;
    elements.sendButton.disabled = false;
    elements.messageInput.focus();
  }
}

function setFeedbackEnabled(enabled) {
  elements.usefulButton.disabled = !enabled;
  elements.notUsefulButton.disabled = !enabled;
  elements.feedbackStatus.textContent = enabled
    ? "Puedes marcar la ultima respuesta como util o no util."
    : "Disponible tras recibir una respuesta.";
}

async function sendFeedback(feedbackType) {
  if (!state.conversationId) {
    return;
  }
  try {
    await requestJson("/feedback", {
      method: "POST",
      body: JSON.stringify({
        conversation_id: state.conversationId,
        message_id: state.lastMessageId,
        user_id: state.userId,
        feedback_type: feedbackType,
      }),
    });
    elements.feedbackStatus.textContent = "Feedback registrado.";
  } catch (error) {
    elements.feedbackStatus.textContent = `No se pudo guardar feedback: ${error.message}`;
  }
}

function resetConversation() {
  state.conversationId = null;
  state.lastMessageId = null;
  elements.messages.innerHTML = "";
  elements.rawResponse.textContent = "{}";
  renderSources([], []);
  setFeedbackEnabled(false);
  appendMessage(
    "assistant",
    "Nueva conversacion iniciada. Puedes lanzar una pregunta de demo o escribir una incidencia nueva."
  );
}

function renderSamples() {
  elements.samples.innerHTML = "";
  for (const sample of samples) {
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = sample;
    button.addEventListener("click", () => {
      elements.messageInput.value = sample;
      elements.messageInput.focus();
    });
    elements.samples.append(button);
  }
}

elements.chatForm.addEventListener("submit", (event) => {
  event.preventDefault();
  const message = elements.messageInput.value.trim();
  elements.messageInput.value = "";
  sendMessage(message);
});

elements.sameOriginButton.addEventListener("click", () => {
  elements.apiBaseInput.value = defaultApiBase();
  persistConnection();
  checkHealth();
});

elements.localButton.addEventListener("click", () => {
  elements.apiBaseInput.value = "http://127.0.0.1:8000/api";
  persistConnection();
  checkHealth();
});

elements.healthButton.addEventListener("click", checkHealth);
elements.resetButton.addEventListener("click", resetConversation);
elements.usefulButton.addEventListener("click", () => sendFeedback("useful"));
elements.notUsefulButton.addEventListener("click", () => sendFeedback("not_useful"));

loadState();
renderSamples();
resetConversation();
checkHealth();
