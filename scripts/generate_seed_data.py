from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"

DEPARTMENTS = ["Operaciones", "Seguridad", "Onboarding", "Politicas internas"]
SYSTEMS = ["LogiCore ERP", "RutaNexo", "AlmaTrack WMS", "SafeGate", "OnboardHub", "DocuFlow"]


def build_documents() -> list[dict]:
    docs = []
    templates = [
        (
            "Operaciones",
            "procedimiento",
            "LogiCore ERP",
            "Gestión de entregas parciales",
            "Para registrar una entrega parcial en LogiCore ERP, el operador debe abrir el pedido, marcar los bultos realmente expedidos y dejar el resto en estado pendiente. El sistema genera un evento de trazabilidad y actualiza la promesa de entrega.",
        ),
        (
            "Operaciones",
            "procedimiento",
            "RutaNexo",
            "Replanificación por corte de carretera",
            "Cuando una ruta se bloquea, el coordinador en RutaNexo debe activar la opción de recalculo asistido, revisar restricciones del vehiculo y confirmar la nueva secuencia antes de enviar la ruta al conductor.",
        ),
        (
            "Operaciones",
            "politica",
            "AlmaTrack WMS",
            "Conteo ciclico en almacen",
            "AlmaTrack WMS exige que los conteos ciclicos con diferencia superior al 2 por ciento queden revisados por un supervisor. Hasta entonces la ubicacion queda en cuarentena operativa.",
        ),
        (
            "Seguridad",
            "procedimiento",
            "SafeGate",
            "Acceso temporal para personal externo",
            "El acceso temporal a SafeGate para visitas tecnicas requiere solicitud del responsable interno, validacion de Seguridad y fecha de expiracion obligatoria. Nunca se debe reutilizar una credencial antigua.",
        ),
        (
            "Seguridad",
            "politica",
            "SafeGate",
            "Uso de credenciales compartidas",
            "Las credenciales compartidas estan prohibidas. Cada acceso debe estar asociado a una persona identificable. Las excepciones deben aprobarse por Seguridad y quedar documentadas.",
        ),
        (
            "Onboarding",
            "guia",
            "OnboardHub",
            "Alta de nuevos conductores",
            "OnboardHub centraliza la alta de conductores. El equipo de onboarding debe validar licencia, documentacion fiscal, curso de seguridad y asignacion de supervisor antes del primer turno.",
        ),
        (
            "Onboarding",
            "guia",
            "DocuFlow",
            "Entrega de manuales operativos",
            "DocuFlow almacena los manuales de arranque para personal de operaciones. Cada nuevo empleado debe confirmar lectura de politicas de seguridad, rutas y uso de dispositivos moviles.",
        ),
        (
            "Politicas internas",
            "politica",
            "DocuFlow",
            "Escalado de incidencias criticas",
            "Toda incidencia con impacto en expediciones de mas de dos almacenes debe escalarse en menos de 15 minutos al responsable de continuidad y abrir ticket con prioridad alta.",
        ),
        (
            "Politicas internas",
            "politica",
            "LogiCore ERP",
            "Cambios maestros de clientes",
            "Los cambios de datos maestros de clientes en LogiCore ERP requieren doble validacion cuando afectan direcciones de entrega recurrentes o reglas de facturacion.",
        ),
        (
            "Operaciones",
            "procedimiento",
            "DocuFlow",
            "Consulta de SOPs operativos",
            "Las SOPs vigentes se consultan siempre en DocuFlow. Si una copia local contradice el documento publicado, prevalece la version con fecha mas reciente del repositorio interno.",
        ),
    ]

    for idx in range(20):
        department, doc_type, system, title, body = templates[idx % len(templates)]
        docs.append(
            {
                "title": f"{title} #{idx + 1}",
                "document_type": doc_type,
                "department": department,
                "affected_system": system,
                "content": f"{body}\n\nVersion interna {idx + 1}. Este documento aplica al area de {department} y al sistema {system}.",
                "tags": [department.lower().replace(" ", "-"), system.lower().replace(" ", "-")],
                "source_url": f"https://intranet.logistica.local/{system.lower().replace(' ', '-')}/doc-{idx + 1}",
            }
        )
    return docs


def build_tickets() -> list[dict]:
    tickets = []
    resolved_templates = [
        ("Retraso en sincronizacion de pedidos", "Operaciones", "integracion", "LogiCore ERP"),
        ("Ruta no recalculada tras incidencia vial", "Operaciones", "rutas", "RutaNexo"),
        ("Ubicacion bloqueada en conteo ciclico", "Operaciones", "almacen", "AlmaTrack WMS"),
        ("Acceso denegado al supervisor de guardia", "Seguridad", "accesos", "SafeGate"),
        ("Checklist incompleto de nuevo conductor", "Onboarding", "alta", "OnboardHub"),
        ("Version desactualizada del SOP", "Politicas internas", "documentacion", "DocuFlow"),
    ]
    unresolved_templates = [
        ("Caida intermitente al consultar pedidos", "Operaciones", "rendimiento", "LogiCore ERP"),
        ("Desfase de ventanas de entrega", "Operaciones", "rutas", "RutaNexo"),
        ("Lectores RF desconectados", "Operaciones", "hardware", "AlmaTrack WMS"),
        ("Bloqueo en doble factor", "Seguridad", "autenticacion", "SafeGate"),
        ("Alta sin supervisor asignado", "Onboarding", "workflow", "OnboardHub"),
    ]

    for idx in range(90):
        title, department, category, system = resolved_templates[idx % len(resolved_templates)]
        tickets.append(
            {
                "title": f"{title} #{idx + 1}",
                "description": (
                    f"El usuario reporto {title.lower()} en {system}. "
                    f"El problema afectaba al departamento de {department} y se reproducia al ejecutar el proceso operativo habitual."
                ),
                "department": department,
                "category": category,
                "affected_system": system,
                "priority": "media" if idx % 3 else "alta",
                "status": "resolved",
                "is_resolved": True,
                "resolution": (
                    f"Se reviso la configuracion de {system}, se reaplico el parametro operativo y se confirmo con el usuario "
                    "que el flujo volvia a completarse sin errores."
                ),
                "impact": "Impacto acotado al equipo solicitante",
                "expected_behavior": "El proceso debe completarse sin errores",
                "actual_behavior": "El proceso quedaba bloqueado o mostraba datos incompletos",
                "tags": [department.lower().replace(" ", "-"), system.lower().replace(" ", "-"), "resuelto"],
                "created_by": "seed-loader",
                "source": "custom_incidents_api",
                "source_url": f"https://incidents.logistica.local/{system.lower().replace(' ', '-')}/{idx + 1}",
            }
        )

    for idx in range(10):
        title, department, category, system = unresolved_templates[idx % len(unresolved_templates)]
        tickets.append(
            {
                "title": f"{title} #{idx + 91}",
                "description": (
                    f"Persisten errores asociados a {title.lower()} en {system}. "
                    "El equipo no dispone todavia de una causa raiz confirmada."
                ),
                "department": department,
                "category": category,
                "affected_system": system,
                "priority": "alta",
                "status": "open",
                "is_resolved": False,
                "resolution": None,
                "impact": "Afecta a la operativa diaria y genera retrasos en el equipo",
                "expected_behavior": "El sistema debe permitir completar el proceso de forma continua",
                "actual_behavior": "El sistema falla de forma intermitente o bloquea la tarea",
                "tags": [department.lower().replace(" ", "-"), system.lower().replace(" ", "-"), "pendiente"],
                "created_by": "seed-loader",
                "source": "custom_incidents_api",
                "source_url": f"https://incidents.logistica.local/{system.lower().replace(' ', '-')}/{idx + 91}",
            }
        )
    return tickets


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    (DATA_DIR / "seed_documents.json").write_text(
        json.dumps(build_documents(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (DATA_DIR / "seed_tickets.json").write_text(
        json.dumps(build_tickets(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print("Datasets generados en data/")


if __name__ == "__main__":
    main()
