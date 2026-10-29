"""Agente inicial del taller. Mejora sus instrucciones sin cambiar su contrato."""
from crewai import Agent, Task
from crew.llm_config import llm

KEY = 'backend'
LABEL = 'Desarrollador backend'
SPEC_FILE = 'backend_spec.md'
EXTRACT_CODE = True

INSTRUCTIONS = ("Implementa los endpoints y servicios respetando el contrato de API. "
                "Valida las entradas y devuelve errores coherentes. Define el acceso a datos y las "
                "transacciones necesarias. En equipos de seis, cubre también el esquema y las "
                "migraciones; si existe un rol de Datos, consume su contrato de persistencia sin "
                "duplicar sus migraciones. Incluye un caso válido, un caso de error y los comandos "
                "para comprobar ambos. Entrega backend_spec.md y el código Java con el formato de "
                "extracción solicitado.")
agent = Agent(role='Desarrollador backend Java Senior',
              goal="Implementar servicios y endpoints fiables que cumplan el contrato de API.",
              backstory="Eres responsable del backend Java. Coordinas la implementación con Arquitectura y Datos, "
              "respetas sus contratos y documentas decisiones de persistencia, validación y manejo de errores.", llm=llm,
              verbose=True, allow_delegation=False)


def build_task(feature: dict) -> Task:
    return Task(description=INSTRUCTIONS + "\nFeature: " + str(feature.get("title", ""))
                + "\n" + str(feature.get("description", ""))
                + "\n" + str(feature.get("acceptance_criteria", [])),
                expected_output='Entrega backend_spec.md con el diseño de endpoints, validaciones, errores, acceso a datos y transacciones. '
                'Incluye un caso válido, un caso de error y comandos reproducibles para comprobarlos. '
                'Entrega el código Java en bloques markdown; cada bloque debe empezar con // Nombre.java y declarar '
                'package pe.bcp.login.service. En equipos de seis incluye esquema y migraciones; con un rol de Datos, '
                'consume su contrato sin duplicar migraciones.', agent=agent)
