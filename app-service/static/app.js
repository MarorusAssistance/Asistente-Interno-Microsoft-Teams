const systems = [
  {
    name: "LogiCore ERP",
    area: "Pedidos, compras, stock, proveedores y facturación.",
    example: "Cómo se libera un pedido retenido por validación manual en LogiCore ERP?",
  },
  {
    name: "AlmaTrack WMS",
    area: "Almacén, ubicaciones, picking, packing y movimientos de stock.",
    example: "Cómo cierro una expedición pendiente en AlmaTrack WMS?",
  },
  {
    name: "RutaNexo TMS",
    area: "Transporte, rutas, transportistas, entregas y POD/CMR.",
    example: "Qué reviso si RutaNexo TMS no publica una nueva secuencia válida?",
  },
  {
    name: "HelpOps",
    area: "Tickets internos, escalado y coordinación de soporte.",
    example: "Cómo se escala una incidencia crítica en HelpOps?",
  },
  {
    name: "DocuFlow",
    area: "Procedimientos, políticas, versiones y fuentes internas.",
    example: "Debe el asistente presentar un caso parecido como solución definitiva?",
  },
  {
    name: "OnboardHub",
    area: "Onboarding, formación y alta de personal operativo.",
    example: "Qué pasos debe completar un coordinador nuevo en OnboardHub?",
  },
  {
    name: "SafeGate",
    area: "Accesos, seguridad física, permisos y credenciales temporales.",
    example: "Cómo se gestiona un permiso temporal en SafeGate?",
  },
  {
    name: "QualiTrace QMS",
    area: "Calidad, auditorías, no conformidades y lotes bloqueados.",
    example: "Cómo se trata una no conformidad en QualiTrace QMS sin dictamen final?",
  },
  {
    name: "ScanBridge IDP",
    area: "OCR, extracción documental y validación de documentos.",
    example: "Qué hago si ScanBridge IDP marca un CMR como ilegible?",
  },
  {
    name: "OpsLake",
    area: "KPIs operativos, datos consolidados y cuadros de seguimiento.",
    example: "Cómo se revisa una diferencia de KPI en OpsLake?",
  },
];

const sampleGroups = [
  {
    title: "Documentación operativa",
    description: "Procedimientos de almacén, pedidos y transporte.",
    questions: [
      "Cómo cierro una expedición pendiente en AlmaTrack WMS?",
      "Cómo se libera un pedido retenido por validación manual en LogiCore ERP?",
      "Qué reviso si RutaNexo TMS no publica una nueva secuencia válida?",
    ],
  },
  {
    title: "Seguridad y accesos",
    description: "Permisos temporales, credenciales y accesos físicos.",
    questions: [
      "Cómo se gestiona un permiso temporal en SafeGate?",
      "Cuándo hay que revocar una credencial temporal en SafeGate?",
    ],
  },
  {
    title: "Onboarding",
    description: "Primeros pasos de coordinadores y personal operativo.",
    questions: [
      "Qué pasos debe completar un coordinador nuevo en OnboardHub?",
      "Soy nuevo en operaciones. Qué tareas de iniciación debo completar esta semana?",
    ],
  },
  {
    title: "Calidad, documentos y KPIs",
    description: "Calidad, OCR, políticas internas y datos consolidados.",
    questions: [
      "Cómo se trata una no conformidad en QualiTrace QMS sin dictamen final?",
      "Qué hago si ScanBridge IDP marca un CMR como ilegible?",
      "Cómo se revisa una diferencia de KPI en OpsLake?",
      "Debe el asistente presentar un caso parecido como solución definitiva?",
    ],
  },
  {
    title: "Incidencias conocidas",
    description: "Casos resueltos, abiertos y errores nuevos sin evidencia directa.",
    questions: [
      "Cómo se resolvió la ruta congelada tras parada prioritaria en RutaNexo TMS?",
      "Hay una ubicación RF inconsistente en AlmaTrack WMS, existe solución definitiva?",
      "No encuentro solución para un error nuevo en AlmaTrack WMS.",
    ],
  },
  {
    title: "Flujo de demo",
    description: "Aclaraciones, registro de incidencia y feedback.",
    questions: [
      "No puedo cerrar la operación, qué debo revisar?",
      "El torno principal sigue rechazando el acceso y no aparece ningún caso parecido.",
      "No útil, la respuesta no me sirve.",
    ],
  },
];

const recommendedQuestions = sampleGroups
  .flatMap((group) => group.questions)
  .filter((question) => !question.toLowerCase().startsWith("no útil"));

const state = {
  apiBase: "",
  userId: "",
  conversationId: null,
  lastMessageId: null,
  busy: false,
  recommendationIndex: 0,
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
  systems: document.querySelector("#systems"),
  samples: document.querySelector("#samples"),
  surpriseButton: document.querySelector("#surpriseButton"),
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
  body.className = "message-body";
  body.textContent = text;

  item.append(meta, body);
  elements.messages.append(item);
  scrollMessages();
  return { item, body };
}

function scrollMessages() {
  elements.messages.scrollTop = elements.messages.scrollHeight;
}

function truncate(value, maxLength = 230) {
  const text = String(value || "").trim();
  if (text.length <= maxLength) {
    return text;
  }
  return `${text.slice(0, maxLength - 1).trim()}...`;
}

function fillComposer(question) {
  elements.messageInput.value = question;
  elements.messageInput.focus();
}

function renderSources(sources = [], relatedIncidents = []) {
  elements.sourceCount.textContent = String(sources.length);
  elements.sources.innerHTML = "";

  if (!sources.length && !relatedIncidents.length) {
    elements.sources.className = "source-list empty";
    elements.sources.textContent = "Sin fuentes para esta respuesta. Puede ser una aclaración, una abstención o un flujo de registro.";
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
  const assistantMessage = appendMessage("assistant", "");

  const payload = {
    conversation_id: state.conversationId,
    user_id: state.userId,
    message,
    channel: "web-demo",
  };

  let receivedUsefulStreamEvent = false;
  try {
    await requestStream("/chat/stream", payload, {
      onToken(text) {
        receivedUsefulStreamEvent = true;
        assistantMessage.body.textContent += text;
        scrollMessages();
      },
      onSources(data) {
        renderSources(data.sources || [], data.related_incidents || []);
      },
      onFinal(response) {
        receivedUsefulStreamEvent = true;
        applyChatResponse(response, assistantMessage.body);
      },
      onError(data) {
        throw new Error(data.message || "No se pudo completar el stream.");
      },
    });
  } catch (error) {
    if (!receivedUsefulStreamEvent) {
      try {
        const response = await requestJson("/chat", {
          method: "POST",
          body: JSON.stringify(payload),
        });
        applyChatResponse(response, assistantMessage.body);
      } catch (fallbackError) {
        assistantMessage.item.remove();
        appendMessage("error", fallbackError.message, "error");
      }
    } else {
      appendMessage("error", error.message, "error");
    }
  } finally {
    state.busy = false;
    elements.sendButton.disabled = false;
    elements.messageInput.focus();
  }
}

function applyChatResponse(response, bodyElement) {
  state.conversationId = response.conversation_id;
  state.lastMessageId = response.message_id;
  bodyElement.textContent = response.answer || response.fallback_text || "Respuesta vacía";
  renderSources(response.sources, response.related_incidents);
  elements.rawResponse.textContent = JSON.stringify(response, null, 2);
  setFeedbackEnabled(Boolean(response.conversation_id));
  scrollMessages();
}

async function requestStream(path, payload, handlers) {
  persistConnection();
  const response = await fetch(`${state.apiBase}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok || !response.body) {
    const text = await response.text();
    throw new Error(text || `${response.status} ${response.statusText}`);
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  while (true) {
    const { done, value } = await reader.read();
    if (done) {
      break;
    }
    buffer += decoder.decode(value, { stream: true });
    const events = buffer.split(/\n\n/);
    buffer = events.pop() || "";
    for (const rawEvent of events) {
      dispatchSseEvent(rawEvent, handlers);
    }
  }
  if (buffer.trim()) {
    dispatchSseEvent(buffer, handlers);
  }
}

function dispatchSseEvent(rawEvent, handlers) {
  const parsed = parseSseEvent(rawEvent);
  if (!parsed) {
    return;
  }
  if (parsed.event === "token") {
    handlers.onToken?.(parsed.data.text || "");
  } else if (parsed.event === "sources") {
    handlers.onSources?.(parsed.data);
  } else if (parsed.event === "final") {
    handlers.onFinal?.(parsed.data);
  } else if (parsed.event === "error") {
    handlers.onError?.(parsed.data);
  }
}

function parseSseEvent(rawEvent) {
  let event = "message";
  const dataLines = [];
  for (const line of rawEvent.split(/\r?\n/)) {
    if (line.startsWith("event:")) {
      event = line.slice("event:".length).trim();
    } else if (line.startsWith("data:")) {
      dataLines.push(line.slice("data:".length).trimStart());
    }
  }
  if (!dataLines.length) {
    return null;
  }
  try {
    return { event, data: JSON.parse(dataLines.join("\n")) };
  } catch {
    return { event, data: { raw: dataLines.join("\n") } };
  }
}

function setFeedbackEnabled(enabled) {
  elements.usefulButton.disabled = !enabled;
  elements.notUsefulButton.disabled = !enabled;
  elements.feedbackStatus.textContent = enabled
    ? "Puedes marcar la última respuesta como útil o no útil."
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
    [
      "Nueva conversación iniciada.",
      "Puedo ayudarte con almacén, pedidos, rutas, accesos, onboarding, calidad, documentos y KPIs.",
      "Prueba con una pregunta del panel lateral, por ejemplo: “Cómo cierro una expedición pendiente en AlmaTrack WMS?”, “Cómo se resolvió la ruta congelada en RutaNexo TMS?” o “No puedo cerrar la operación, qué debo revisar?”.",
    ].join("\n\n")
  );
}

function renderSystems() {
  elements.systems.innerHTML = "";
  for (const system of systems) {
    const item = document.createElement("button");
    item.type = "button";
    item.className = "system-card";
    item.addEventListener("click", () => fillComposer(system.example));

    const name = document.createElement("span");
    name.className = "system-name";
    name.textContent = system.name;

    const area = document.createElement("span");
    area.className = "system-area";
    area.textContent = system.area;

    const example = document.createElement("span");
    example.className = "system-example";
    example.textContent = `Ejemplo: ${system.example}`;

    item.append(name, area, example);
    elements.systems.append(item);
  }
}

function renderSamples() {
  elements.samples.innerHTML = "";
  for (const group of sampleGroups) {
    const section = document.createElement("div");
    section.className = "sample-group";

    const title = document.createElement("h3");
    title.textContent = group.title;

    const description = document.createElement("p");
    description.textContent = group.description;

    section.append(title, description);
    for (const sample of group.questions) {
      const button = document.createElement("button");
      button.type = "button";
      button.textContent = sample;
      button.addEventListener("click", () => fillComposer(sample));
      section.append(button);
    }
    elements.samples.append(section);
  }
}

function suggestQuestion() {
  const question = recommendedQuestions[state.recommendationIndex % recommendedQuestions.length];
  state.recommendationIndex += 1;
  fillComposer(question);
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
elements.surpriseButton.addEventListener("click", suggestQuestion);
elements.resetButton.addEventListener("click", resetConversation);
elements.usefulButton.addEventListener("click", () => sendFeedback("useful"));
elements.notUsefulButton.addEventListener("click", () => sendFeedback("not_useful"));

loadState();
renderSystems();
renderSamples();
resetConversation();
checkHealth();
