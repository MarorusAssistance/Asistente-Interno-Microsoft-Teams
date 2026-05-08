from __future__ import annotations

from dataclasses import asdict, dataclass, field


SYSTEM_NAMES = (
    "LogiCore ERP",
    "RutaNexo",
    "AlmaTrack WMS",
    "SafeGate",
    "OnboardHub",
    "DocuFlow",
)

NEW_ISSUE_TERMS = (
    "error nuevo",
    "nuevo error",
    "no encuentro solucion",
    "no encuentro solución",
    "sigue fallando",
    "sigue igual",
    "no se resuelve",
    "no esta resuelto",
    "no está resuelto",
)

PROCEDURE_TERMS = (
    "como ",
    "cómo ",
    "pasos",
    "procedimiento",
    "registrar",
    "completar",
    "hacer",
    "revisar",
    "onboarding",
    "iniciacion",
    "iniciación",
)

DISSATISFIED_FOLLOW_UP_TERMS = (
    "esa respuesta no me vale",
    "no me vale",
    "explicamelo mejor",
    "explícamelo mejor",
    "indicame mejor",
    "indícame mejor",
    "teniendo en cuenta",
    "lo anterior",
    "como te dije",
)


@dataclass(slots=True)
class QuerySignals:
    new_issue: bool = False
    procedure_request: bool = False
    dissatisfied_followup: bool = False
    mentioned_systems: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(slots=True)
class EvidenceAssessment:
    should_block_answer: bool
    requires_direct_evidence: bool
    reason_code: str
    clarification_question: str
    document_count: int
    incident_count: int
    source_types: list[str]
    source_systems: list[str]
    related_only: bool = False
    system_mismatch: bool = False
    has_matching_document: bool = False
    has_matching_source: bool = False
    direct_chunk_ids: list[int] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


def detect_query_signals(message: str) -> QuerySignals:
    normalized = _normalize(message)
    mentioned_systems = [system for system in SYSTEM_NAMES if _normalize(system) in normalized]
    return QuerySignals(
        new_issue=any(term in normalized for term in (_normalize(item) for item in NEW_ISSUE_TERMS)),
        procedure_request=any(term in normalized for term in (_normalize(item) for item in PROCEDURE_TERMS)),
        dissatisfied_followup=any(term in normalized for term in (_normalize(item) for item in DISSATISFIED_FOLLOW_UP_TERMS)),
        mentioned_systems=mentioned_systems,
    )


def assess_evidence(message: str, retrieved: list) -> tuple[QuerySignals, EvidenceAssessment]:
    signals = detect_query_signals(message)
    document_count = sum(1 for item in retrieved if getattr(item, "source_type", "") == "document")
    incident_count = sum(1 for item in retrieved if getattr(item, "source_type", "") == "incident")
    source_types = _unique([str(getattr(item, "source_type", "")) for item in retrieved if getattr(item, "source_type", "")])
    source_systems = _unique([_source_system(item) for item in retrieved if _source_system(item)])
    related_only = bool(retrieved) and incident_count == len(retrieved)

    matching_sources = _matching_sources(retrieved, signals.mentioned_systems)
    matching_documents = [item for item in matching_sources if getattr(item, "source_type", "") == "document"]
    direct_chunks = _direct_evidence_chunks(signals, retrieved, matching_sources, matching_documents)
    system_mismatch = bool(signals.mentioned_systems and retrieved and not matching_sources)

    reason_code = "sufficient_evidence"
    clarification_question = ""
    should_block = False
    requires_direct_evidence = bool(
        signals.new_issue or signals.procedure_request or signals.dissatisfied_followup or signals.mentioned_systems
    )

    if signals.dissatisfied_followup and not signals.mentioned_systems:
        should_block = True
        requires_direct_evidence = True
        reason_code = "follow_up_without_explicit_context"
        clarification_question = (
            "Para corregir la respuesta necesito que concretes el sistema o proceso exacto. "
            "Por ejemplo: OnboardHub para alta inicial, SafeGate para permisos o LogiCore ERP para pedidos."
        )
    elif system_mismatch:
        should_block = True
        requires_direct_evidence = True
        reason_code = "source_system_mismatch"
        clarification_question = (
            "Los fragmentos recuperados no pertenecen al sistema que mencionas. "
            "Confirma el sistema y el proceso afectado para buscar una respuesta fiable."
        )
    elif signals.new_issue and related_only:
        should_block = True
        requires_direct_evidence = True
        reason_code = "new_issue_only_similar_incidents"
        clarification_question = (
            "Al ser un error nuevo, necesito el error exacto, pantalla o paso donde falla, "
            "proceso afectado y referencia operativa como pedido, ruta o ubicacion."
        )
    elif signals.procedure_request and not document_count:
        should_block = True
        requires_direct_evidence = True
        reason_code = "procedure_without_document"
        clarification_question = (
            "No he recuperado un procedimiento documentado suficiente. "
            "Indica sistema, proceso y objetivo para evitar darte pasos inventados."
        )

    return signals, EvidenceAssessment(
        should_block_answer=should_block,
        requires_direct_evidence=requires_direct_evidence,
        reason_code=reason_code,
        clarification_question=clarification_question,
        document_count=document_count,
        incident_count=incident_count,
        source_types=source_types,
        source_systems=source_systems,
        related_only=related_only,
        system_mismatch=system_mismatch,
        has_matching_document=bool(matching_documents),
        has_matching_source=bool(matching_sources),
        direct_chunk_ids=[int(getattr(item, "chunk_id")) for item in direct_chunks],
    )


def build_policy_clarification_answer(assessment: EvidenceAssessment, clarification_attempts: int) -> str:
    question = assessment.clarification_question or (
        "Necesito un dato mas para responder con seguridad. Indica sistema, proceso, error exacto o contexto operativo."
    )
    return "\n".join(
        [
            "Resumen",
            "No tengo evidencia directa suficiente para darte una solucion fiable.",
            "",
            "Detalle",
            question,
            "",
            "Siguiente paso",
            f"Responde con ese dato para continuar. Intento de aclaracion {clarification_attempts} de 2.",
        ]
    )


def _matching_sources(retrieved: list, systems: list[str]) -> list:
    if not systems:
        return list(retrieved)
    wanted = {_normalize(system) for system in systems}
    return [item for item in retrieved if _normalize(_source_system(item)) in wanted]


def _direct_evidence_chunks(signals: QuerySignals, retrieved: list, matching_sources: list, matching_documents: list) -> list:
    if signals.procedure_request:
        if signals.mentioned_systems:
            return matching_documents
        return [item for item in retrieved if getattr(item, "source_type", "") == "document"]
    if signals.new_issue:
        return matching_documents
    if signals.dissatisfied_followup:
        return matching_documents
    if signals.mentioned_systems:
        return matching_sources
    return list(retrieved)


def _source_system(item) -> str:
    metadata = getattr(item, "metadata", {}) or {}
    return str(metadata.get("affected_system") or "")


def _unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if not value or value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


def _normalize(value: str) -> str:
    return value.strip().lower()
