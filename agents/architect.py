"""Agente inicial del taller. Mejora sus instrucciones sin cambiar su contrato."""
from crewai import Agent, Task
from crew.llm_config import llm

KEY = 'architect'
LABEL = 'Arquitecto'
SPEC_FILE = 'user_story.md'
EXTRACT_CODE = False

INSTRUCTIONS = """Tu output es user_story.md: la solución, el contrato de API y los criterios verificables de la transferencia entre cuentas propias,
que Backend (Python), Frontend (React), Testing, Security y Chapter implementarán y revisarán.

Tareas:
1. Redacta la historia de usuario (Como / Quiero / Para) y los criterios de aceptación en formato Dado / Cuando / Entonces. Conserva los criterios recibidos; los que agregues márcalos como propuesta.
2. Describe el recorrido de una petición: React -> API -> caso de uso -> puertos -> persistencia. Incluye un ejemplo de petición y respuesta exitosa y uno de error.
3. Define el contrato de API: método, ruta, cabeceras (incluida Idempotency-Key), cuerpo, respuesta, códigos HTTP y formato de error con códigos de negocio estables
   (saldo insuficiente, misma cuenta, cuenta no propia, cuenta inactiva, moneda no soportada, límite excedido, solicitud duplicada). Los montos nunca viajan como float: usa string decimal con moneda ISO 4217.
4. Enumera las reglas de negocio: ambas cuentas pertenecen al cliente autenticado, origen distinto de destino, cuentas activas, saldo suficiente, moneda, límites y atomicidad de débito y crédito.
   Toda regla que no esté en el requerimiento ni en los criterios debe quedar como pendiente, no como decisión confirmada.
5. Define componentes y límites con arquitectura hexagonal (dominio, aplicación, puertos, adaptadores) y qué decide cada rol. Si Datos está activo, indica qué le corresponde; si no, Backend cubre la persistencia necesaria.
6. Fija requisitos no funcionales: consistencia, idempotencia, concurrencia, auditoría, trazabilidad, observabilidad y seguridad. Cada uno debe ser verificable.
7. Cierra con supuestos, preguntas abiertas y riesgos, indicando quién debe resolverlos.

Entrega:
- user_story.md con: historia, criterios, recorrido, contrato, reglas, componentes, no funcionales y pendientes.
- Contrato y criterios primero: el resto del equipo recibe solo los primeros 8000 caracteres de tu salida.

No debes:
- Escribir código de implementación ni SQL.
- Inventar requisitos, endpoints o resultados de pruebas.
- Dejar decisiones implícitas que obliguen a otro rol a adivinar el contrato.
- Usar datos reales de clientes o cuentas.
"""
agent = Agent(
    role='Arquitecto de software',
    goal="Definir una solución y un contrato de API claros, seguros y verificables para la transferencia entre cuentas propias, alineados a los criterios de aceptación y a la arquitectura hexagonal.",
    backstory=(
        "Eres un arquitecto de software senior con 12 años de experiencia en sistemas transaccionales "
        "bancarios, APIs en Python y aplicaciones React. Traduces requerimientos en contratos precisos, "
        "límites claros entre componentes y decisiones de consistencia, idempotencia y seguridad. "
        "Evitas la ambigüedad: lo que no está confirmado lo declaras como supuesto o pendiente."
    ),
    llm=llm,
    verbose=True,
    allow_delegation=False)


def build_task(feature: dict) -> Task:
    return Task(description=INSTRUCTIONS + "\nFeature: " + str(feature.get("title", ""))
                + "\n" + str(feature.get("description", ""))
                + "\n" + str(feature.get("acceptance_criteria", [])),
                expected_output='Una historia de usuario.', agent=agent)