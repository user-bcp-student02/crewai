"""Agente inicial del taller. Mejora sus instrucciones sin cambiar su contrato."""
from crewai import Agent, Task
from crew.llm_config import llm

KEY = 'testing'
LABEL = 'Ingeniero de pruebas'
SPEC_FILE = 'testing_report.md'
EXTRACT_CODE = True

INSTRUCTIONS = (
    "Analiza la funcionalidad y sus criterios de aceptación. "
    "Propón casos de prueba para el flujo principal, los casos límite y los errores; "
    "incluye pasos y resultados esperados. Señala riesgos o criterios no cubiertos "
    "y no afirmes que ejecutaste pruebas si no hay evidencia."
)
agent = Agent(role='Diseñador Senior de Pruebas de Software',
              goal="Transformar historias de usuario y criterios de aceptación en casos de prueba detallados, claros y exhaustivos.",
              backstory="""Eres un QA Engineer meticuloso con años de experiencia en metodologías ágiles. 
                Tu superpoder es leer una historia de usuario y encontrar inmediatamente los escenarios 'edge case' (casos esquina) 
                y flujos alternativos que los desarrolladores suelen pasar por alto. Diseñas pruebas usando formatos 
                claros como Gherkin (Given-When-Then) para asegurar que el comportamiento del software sea el esperado.""",
              llm=llm,
              verbose=True, allow_delegation=False)


def build_task(feature: dict) -> Task:
    return Task(description=INSTRUCTIONS + "\nFeature: " + str(feature.get("title", ""))
                + "\n" + str(feature.get("description", ""))
                + "\n" + str(feature.get("acceptance_criteria", [])),
                expected_output=(
                    'Informe en español con casos de prueba, pasos y resultados esperados; '
                    'criterios de aceptación cubiertos y riesgos o vacíos detectados. '
                    'Distingue las pruebas propuestas de las ejecutadas.'
                ), agent=agent)
