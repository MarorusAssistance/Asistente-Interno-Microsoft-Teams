from __future__ import annotations

import argparse
import json
from pathlib import Path


DEMO_QUESTIONS = [
    {
        "id": "demo-01",
        "question": "Como se registra una entrega parcial en ventana critica en LogiCore ERP?",
        "goal": "Mostrar una respuesta de documentacion operativa con fuentes claras.",
        "expected_behavior": "answer_with_sources",
        "expected_sources": ["document:1", "document:2"],
        "technical_point": "Retrieval hibrido, respuesta grounded y citas limpias.",
    },
    {
        "id": "demo-02",
        "question": "Como solicito acceso temporal a SafeGate para personal externo?",
        "goal": "Demostrar una politica interna de seguridad y el uso de fuentes documentales.",
        "expected_behavior": "answer_with_sources",
        "expected_sources": ["document:9", "incident:1"],
        "technical_point": "Cruce entre documentacion y tickets resueltos.",
    },
    {
        "id": "demo-03",
        "question": "Que pasos de onboarding debo completar en la primera semana?",
        "goal": "Mostrar cobertura funcional fuera de operaciones puras.",
        "expected_behavior": "answer_with_sources",
        "expected_sources": ["document:15"],
        "technical_point": "Cobertura multi area del corpus RAG.",
    },
    {
        "id": "demo-04",
        "question": "Que politica aplica al uso de credenciales compartidas?",
        "goal": "Mostrar una politica interna con respuesta apoyada en documentacion.",
        "expected_behavior": "answer_with_sources",
        "expected_sources": ["document:20"],
        "technical_point": "Cobertura de politicas internas y citas legibles.",
    },
    {
        "id": "demo-05",
        "question": "Que hago si RutaNexo no sincroniza una ruta aprobada?",
        "goal": "Ensenar una incidencia resuelta y la relacion entre fuente documental e incidente.",
        "expected_behavior": "say_incident_resolved",
        "expected_sources": ["incident:12", "document:4"],
        "technical_point": "Uso de incidencias historicas como conocimiento operativo.",
    },
    {
        "id": "demo-06",
        "question": "Como se revisa un pedido bloqueado por validacion manual?",
        "goal": "Mostrar una respuesta operativa basada en trazabilidad y procedimientos.",
        "expected_behavior": "answer_with_sources",
        "expected_sources": ["document:3", "incident:20"],
        "technical_point": "Fuentes ordenadas por relevancia.",
    },
    {
        "id": "demo-07",
        "question": "No puedo entrar",
        "goal": "Forzar el camino de aclaracion.",
        "expected_behavior": "ask_clarification",
        "expected_sources": [],
        "technical_point": "Abstencion temprana y flujo de aclaraciones.",
    },
    {
        "id": "demo-08",
        "question": "El torno principal sigue rechazando el acceso y no aparece ningun caso parecido",
        "goal": "Demostrar el cierre del flujo en oferta de registro de incidencia.",
        "expected_behavior": "abstain_and_offer_incident_registration",
        "expected_sources": [],
        "technical_point": "Cuando no hay evidencia suficiente, el asistente no inventa respuesta.",
    },
    {
        "id": "demo-09",
        "question": "no util",
        "goal": "Ensenar el loop de feedback.",
        "expected_behavior": "feedback",
        "expected_sources": [],
        "technical_point": "Registro de feedback y mejora de trazabilidad.",
    },
]


def render_markdown() -> str:
    lines = [
        "# Demo Questions",
        "",
        "| id | pregunta | objetivo | comportamiento esperado | fuentes esperadas | punto tecnico |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for item in DEMO_QUESTIONS:
        lines.append(
            "| {id} | {question} | {goal} | {expected_behavior} | {expected_sources} | {technical_point} |".format(
                id=item["id"],
                question=item["question"].replace("|", "/"),
                goal=item["goal"].replace("|", "/"),
                expected_behavior=item["expected_behavior"],
                expected_sources=", ".join(item["expected_sources"]) or "-",
                technical_point=item["technical_point"].replace("|", "/"),
            )
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Exporta las preguntas de demo para portfolio.")
    parser.add_argument("--format", choices=("json", "markdown"), default="json")
    parser.add_argument("--output", default="")
    args = parser.parse_args()

    content = json.dumps(DEMO_QUESTIONS, ensure_ascii=False, indent=2) if args.format == "json" else render_markdown()
    if args.output:
        Path(args.output).write_text(content, encoding="utf-8")
    else:
        print(content)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
