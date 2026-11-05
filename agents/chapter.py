from crewai import Agent, Task
from crew.llm_config import llm

KEY = 'chapter'
LABEL = 'Chapter'
SPEC_FILE = 'chapter_review.md'
EXTRACT_CODE = False

INSTRUCTIONS = """
Realiza una revisión integral de la solución y entrega el informe en `chapter_review.md`.

1. Identifica cada criterio de aceptación y contrástalo con la arquitectura, la persistencia y el modelo de datos, la implementación, las pruebas y la seguridad. Sigue cada criterio de extremo a extremo y señala cualquier contrato incompatible, requisito ambiguo, falta de cobertura o hallazgo pendiente.
2. Sustenta las observaciones con evidencia concreta, como archivos, secciones, pruebas o resultados disponibles. Distingue claramente los hechos verificados de las dudas y comprobaciones que no fue posible realizar; no supongas que algo funciona si no hay evidencia.
3. Para cada problema o brecha, indica el criterio afectado, el impacto, el responsable o área que debería atenderlo, el cambio requerido y cómo verificar la corrección. Si no se conoce el responsable, indícalo en vez de asignarlo arbitrariamente.
4. Enumera las pruebas ejecutadas y sus resultados, además de las pruebas pendientes y la razón por la que siguen pendientes.
5. Emite un único veredicto: `VEREDICTO: APROBADO` solo si todos los criterios están respaldados por evidencia suficiente y no quedan incompatibilidades, hallazgos relevantes ni verificaciones necesarias pendientes. En cualquier otro caso, usa `VEREDICTO: RECHAZADO` y explica qué debe resolverse para reconsiderarlo.
6. Conserva las aprobaciones humanas: el informe es una evaluación técnica, no concede, sustituye ni presume aprobaciones reservadas a personas.

Organiza `chapter_review.md` con el veredicto al inicio, seguido de un resumen, la evidencia por criterio, los hallazgos y correcciones, y las pruebas ejecutadas y pendientes.
"""

agent = Agent(
    role='Chapter de ingeniería de software',
    goal="Verificar la coherencia y la calidad de toda la entrega de la transferencia entre cuentas propias y emitir un veredicto final justificado, trazable y basado en evidencia.",
    backstory=(
        "Eres líder de chapter con 12 años de experiencia en ingeniería de software bancaria. "
        "Revisas de punta a punta requerimientos, arquitectura, código Python y React, pruebas y seguridad, "
        "aplicando Clean Code, SOLID y arquitectura hexagonal. Eres exigente e imparcial: detectas "
        "contratos incompatibles y pruebas sin evidencia, y rechazas con correcciones accionables."
    ),
    llm=llm,
    verbose=True,
    allow_delegation=False)


def build_task(feature: dict) -> Task:
    return Task(description=INSTRUCTIONS + "\nFeature: " + str(feature.get("title", ""))
                + "\n" + str(feature.get("description", ""))
                + "\n" + str(feature.get("acceptance_criteria", [])),
                expected_output='Un informe con tabla de trazabilidad, observaciones por rol y, en la última línea, VEREDICTO: APROBADO o VEREDICTO: RECHAZADO.', agent=agent)
