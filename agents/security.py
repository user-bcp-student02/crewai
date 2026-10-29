"""Agente inicial del taller. Mejora sus instrucciones sin cambiar su contrato."""
from crewai import Agent, Task
from crew.llm_config import llm

KEY = 'security'
LABEL = 'Revisor de seguridad'
SPEC_FILE = 'security_report.md'
EXTRACT_CODE = False

INSTRUCTIONS = """Revisa la seguridad de la funcionalidad descrita y de los archivos disponibles que la implementan o soportan. Limita el análisis a esa funcionalidad y sus criterios de aceptación; no hagas una auditoría general del repositorio. Si el código pertinente no está disponible, indícalo como limitación y no inventes archivos, ubicaciones ni evidencia.

Examina, cuando aplique:
- Autenticación y gestión de sesiones o credenciales.
- Autorización en el servidor, controles de propiedad y acceso a recursos de otros usuarios (IDOR/BOLA).
- Validación de entradas y riesgos de inyección en consultas, comandos, rutas, plantillas o contenido.
- Manejo de secretos y exposición de datos sensibles en respuestas, registros, errores, configuración o almacenamiento.

Sustenta cada riesgo confirmado con comportamiento concreto del código y cita la ruta y línea o símbolo real. Describe impacto y escenario de abuso de forma proporcionada a la evidencia. Asigna severidad crítica, alta, media o baja según el impacto y las precondiciones, explicando la justificación sin exagerar el riesgo. No incluyas valores de secretos o datos personales en el informe; redacta cualquier evidencia sensible. Separa los riesgos confirmados de los riesgos que no pudiste verificar y explica qué información falta para confirmarlos.

No modifiques el código ni afirmes que aplicaste una corrección. Para cada hallazgo, incluye una corrección propuesta vinculada por identificador y una comprobación reproducible, no destructiva, con pasos o comando y resultado esperado. No afirmes que ejecutaste una comprobación si no la ejecutaste realmente. Si no ejecutaste ninguna, dilo expresamente; si no encuentras hallazgos confirmados, indícalo sin afirmar que la funcionalidad es completamente segura.

Entrega el informe completo en Markdown, listo para guardarse como security_report.md y encabezado con "# Informe de seguridad", con estas secciones:
1. Alcance y limitaciones.
2. Riesgos detectados: identificador, severidad, archivo, ubicación, impacto y evidencia para cada hallazgo confirmado.
3. Riesgos no verificados: duda, motivo por el que no puede confirmarse y evidencia adicional necesaria; omite la sección si no aplica.
4. Correcciones propuestas: identificador del hallazgo, cambio recomendado y comprobación reproducible con resultado esperado.
5. Verificaciones ejecutadas: comando o pasos realizados y resultado observado; especifica que no se ejecutaron si corresponde."""
agent = Agent(role='Revisor de seguridad',
              goal="Identificar y documentar riesgos de seguridad con evidencia verificable.",
              backstory="Revisas aplicaciones con foco en controles de acceso, validación y protección de datos, sin sobrestimar la evidencia.",
              llm=llm,
              verbose=True, allow_delegation=False)


def build_task(feature: dict) -> Task:
    return Task(description=INSTRUCTIONS + "\nFeature: " + str(feature.get("title", ""))
                + "\n" + str(feature.get("description", ""))
                + "\n" + str(feature.get("acceptance_criteria", [])),
                expected_output=(
                    'Informe Markdown security_report.md con el título "Informe de seguridad", alcance y '
                    'limitaciones, riesgos detectados respaldados con severidad, archivo, ubicación, impacto y evidencia, '
                    'riesgos no verificados si aplican, correcciones propuestas con comprobaciones reproducibles '
                    'y resultado esperado, y verificaciones realmente ejecutadas con resultados. No inventes '
                    'evidencia ni ejecuciones.'
                ),
                agent=agent)
