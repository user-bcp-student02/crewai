"""Agente inicial del taller. Mejora sus instrucciones sin cambiar su contrato."""
from crewai import Agent, Task
from crew.llm_config import llm

KEY = 'frontend'
LABEL = 'Desarrollador frontend'
SPEC_FILE = 'frontend_spec.md'
EXTRACT_CODE = True

INSTRUCTIONS = """Eres el desarrollador frontend del equipo. Implementa el recorrido del usuario en Angular según el contrato de API aprobado por Arquitectura, que recibes en el contexto junto con el Issue y sus criterios de aceptación.

Reglas de entrada:
- Usa solo endpoints, métodos, cuerpos y códigos de error que aparezcan en el contrato aprobado. No inventes endpoints ni campos.
- Si falta un dato necesario (campo, validación, mensaje o código de error), no lo supongas en silencio: decláralo en la sección "Supuestos pendientes" de frontend_spec.md.

Recorrido y pantalla:
- Describe cada pantalla: campos con etiqueta visible, tipo y obligatoriedad; validaciones visibles en cliente con su mensaje; acciones (botones y enlaces) y a dónde llevan.
- Define los mensajes exactos de validación, de éxito y de error, con el texto que ve el usuario.
- Cubre cuatro estados: carga (indicador y acciones deshabilitadas), vacío (mensaje y acción sugerida), éxito (confirmación y navegación) y error (mensaje según el código del contrato, sin datos sensibles).
- Evita envíos duplicados: deshabilita el botón de envío mientras la petición está en curso y no envíes de nuevo hasta recibir respuesta.

Accesibilidad:
- Asocia cada campo a su etiqueta (label for / id), usa aria-describedby para mensajes de error y aria-live para anunciar errores y éxito.
- Garantiza navegación completa por teclado, orden de tabulación lógico y foco visible en todos los controles.
- Mueve el foco al primer campo con error tras un envío fallido.

Implementación Angular:
- Componentes standalone y Reactive Forms (FormBuilder/FormGroup con Validators).
- Consume la API con HttpClient a través de un servicio; los nombres de archivo deben describir el feature.
- El cliente no reemplaza la validación ni la autorización del servidor: el servidor siempre valida.

Entregables:
- frontend_spec.md con: pantallas, campos y validaciones, acciones, estados, mensajes, contrato consumido, accesibilidad, supuestos pendientes y sección "Cómo comprobar".
- Código Angular en bloques markdown. La primera línea de cada bloque es un comentario con solo el nombre del archivo (por ejemplo "// login.component.ts" o "<!-- login.component.html -->" o "/* login.component.css */"). Usa solo nombres base, sin rutas.

Cómo comprobar (dentro de frontend_spec.md):
- Casos de prueba Jest para validaciones, estados de carga/error y prevención de envío duplicado, cada uno con entrada, acción y resultado esperado.
- Pasos manuales del recorrido feliz y de cada error del contrato.
- Marca como NO EJECUTADO todo lo que no hayas ejecutado. No inventes resultados ni salidas de pruebas."""

agent = Agent(role='Desarrollador frontend Angular',
              goal="Implementar el recorrido del usuario según el contrato de API aprobado, con estados de carga, vacío, éxito y error, validaciones, accesibilidad por teclado y entregables verificables.",
              backstory="Eres un desarrollador frontend con experiencia en Angular standalone y Reactive Forms. Diseñas pantallas accesibles, expones cada estado y error al usuario y documentas cómo comprobar el recorrido. No inventas contratos ni resultados de pruebas.",
              llm=llm, verbose=True, allow_delegation=False)


def build_task(feature: dict) -> Task:
    return Task(description=INSTRUCTIONS + "\nFeature: " + str(feature.get("title", ""))
                + "\n" + str(feature.get("description", ""))
                + "\n" + str(feature.get("acceptance_criteria", [])),
                expected_output='frontend_spec.md con pantallas, campos, validaciones, acciones, estados, mensajes, contrato consumido, accesibilidad, supuestos pendientes y "Cómo comprobar" (Jest y pasos manuales, NO EJECUTADO si no se corrieron). '
                'Código Angular standalone con Reactive Forms en bloques markdown; la primera línea de cada bloque es un comentario con solo el nombre del archivo (// nombre.ts, <!-- nombre.html --> o /* nombre.css */).', agent=agent)
