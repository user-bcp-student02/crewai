"""Agente inicial del taller. Mejora sus instrucciones sin cambiar su contrato."""
from crewai import Agent, Task
from crew.llm_config import llm

KEY = 'frontend'
LABEL = 'Desarrollador frontend'
SPEC_FILE = 'frontend_spec.md'
EXTRACT_CODE = True

INSTRUCTIONS = "Realiza la tarea de tu rol."
agent = Agent(role="Desarrollador frontend de medios de pago", goal="Implementar el recorrido del usuario según el contrato de API aprobado. Definir campos, validaciones, acciones y mensajes. Cubrir estados de carga, vacío, éxito y error, y evita envíos duplicados. Conservar etiquetas accesibles, navegación por teclado y foco visible. Incluir cómo comprobar el recorrido y sus errores. Entregar frontend_spec.md y código Angular con el formato de extracción que ya exige build_task.",
              backstory="Eres un integrante del equipo, con formación como fullstack, pero con reciente experiencia de 5 años en la especialidad de frontend", llm=llm,
              verbose=True, allow_delegation=False)


def build_task(feature: dict) -> Task:
    return Task(description=INSTRUCTIONS + "\nFeature: " + str(feature.get("title", ""))
                + "\n" + str(feature.get("description", ""))
                + "\n" + str(feature.get("acceptance_criteria", [])),
                expected_output='Código en bloques markdown; primera línea con // nombre.service.ts.', agent=agent)
