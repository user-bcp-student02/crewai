"""Agente que redacta el PR con el que se publica output/ en el repositorio remoto."""
from crewai import Agent, Task
from crew.llm_config import llm

KEY = 'publisher'
LABEL = 'Publicador'

INSTRUCTIONS = """
Redacta el Pull Request que publicará en la carpeta `source/` del repositorio remoto
lo generado por el equipo de agentes. Responde SOLO con un objeto JSON válido, sin
bloques de código, con las claves `title` (máx. 72 caracteres) y `body` (Markdown en español).

El cuerpo debe incluir: resumen del feature, criterios de aceptación, árbol de archivos
publicados, veredicto del Chapter y pendientes que éste haya señalado. No inventes
información que no esté en el contexto.
"""

agent = Agent(
    role='Publicador de entregas',
    goal="Redactar un PR claro y trazable para publicar la fuente generada por los agentes.",
    backstory=(
        "Eres responsable de release en un equipo bancario. Resumes entregas con precisión, "
        "reflejas fielmente el veredicto de revisión y nunca ocultas hallazgos pendientes."
    ),
    llm=llm,
    verbose=False,
    allow_delegation=False)


def build_task(feature: dict, file_paths: list[str], chapter_text: str) -> Task:
    tree = "\n".join(f"- {p}" for p in file_paths)
    return Task(
        description=(INSTRUCTIONS + "\nFeature: " + str(feature.get("title", ""))
                     + "\n" + str(feature.get("description", ""))
                     + "\nCriterios: " + str(feature.get("acceptance_criteria", []))
                     + "\n\nArchivos a publicar:\n" + tree
                     + "\n\nInforme del Chapter (extracto):\n" + chapter_text[-3000:]),
        expected_output='JSON con las claves "title" y "body".',
        agent=agent)
