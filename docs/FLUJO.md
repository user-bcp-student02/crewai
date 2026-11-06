# Flujo de orquestación de agentes

Recorrido completo de `python main.py`: backlog por MCP → agentes con aprobación humana → publicación de la fuente en un PR.

## 1. Flujo general

```mermaid
flowchart TD
    A([python main.py]) --> B[MCP Proyectos :8081<br/>tools/list + autenticación]
    B --> C[list_projects: elegir proyecto]
    C --> D[list_project_items: elegir feature del backlog]
    D --> E[get_feature_from_item<br/>título, descripción, criterios de aceptación]
    E --> F{¿Checkpoint en<br/>output/.checkpoint.json?}
    F -- otro feature --> F1{¿Empezar de cero?}
    F1 -- no --> X([Fin])
    F1 -- sí --> G
    F -- mismo feature o ninguno --> G[Cargar pasos aprobados<br/>+ ensure_scaffolding]
    G --> H[Enriquecer Arquitecto con<br/>HEX_PROMPT_PREFIX + brief del feature]
    H --> S1

    subgraph LOOP [Un mini-Crew por agente, en secuencia]
        direction TB
        S1[1. Arquitecto] --> S1D{{Datos y persistencia<br/>solo si CREWAI_INCLUDE_DATA=true}}
        S1D --> S2[2. Backend Quarkus]
        S2 --> S3[3. Frontend Angular]
        S3 --> S4[4. Pruebas]
        S4 --> S5[5. Seguridad]
        S5 --> S6[6. Chapter<br/>revisor final]
    end

    S6 --> V[Veredicto del Chapter]
    V --> Q{¿PUBLISH_ENABLED<br/>y hay archivos?}
    Q -- no --> Z([Fin])
    Q -- sí --> R{¿Crear rama y PR? s/n}
    R -- n --> Z
    R -- s --> W[Agente Publicador<br/>redacta título y cuerpo del PR]
    W --> W1{¿Chapter APROBADO?}
    W1 -- sí --> Y[draft = false]
    W1 -- no --> Y2[draft = true]
    Y --> G1
    Y2 --> G1
    G1[git clone temporal de<br/>GITHUB_OWNER/GITHUB_REPO] --> G2[checkout -b crewai/feature-fecha<br/>copiar output/ a source/<br/>commit + push]
    G2 --> M[MCP local :8081<br/>manage_prs action=create<br/>head=rama nueva, base=main]
    M --> PR([PR abierto en ai-labs])
```

## 2. Detalle de cada paso de agente (HITL + checkpoint)

```mermaid
flowchart TD
    P0{¿Paso ya aprobado<br/>en el checkpoint?} -- sí --> P0a[Omitir y re-extraer código]
    P0 -- no --> P1[build_task + contexto de<br/>pasos aprobados anteriores]
    P1 --> P2[run_step: Crew de 1 agente<br/>LLM Copilot]
    P2 --> P3{Revisión humana<br/>preview del output}
    P3 -- r reintentar<br/>con feedback opcional --> P1
    P3 -- n rechazar --> P4[Checkpoint: rejected]
    P4 --> P4a([Abortar])
    P3 -- s aprobar --> P5[save_spec a output/specs<br/>extract_and_save_code: .java .ts .sql]
    P5 --> P6[Checkpoint: approved]
    P6 --> P7([Siguiente agente])
    P0a --> P7
```

## 3. Secuencia entre componentes

```mermaid
sequenceDiagram
    actor U as Usuario
    participant M as main.py
    participant MCP as MCP local :8081
    participant A as Agentes CrewAI
    participant FS as output/
    participant GIT as git
    participant GH as GitHub ai-labs

    U->>M: python main.py
    M->>MCP: list_projects / list_project_items
    MCP-->>M: backlog y feature
    loop Por cada agente
        M->>A: run_step(agente, tarea + contexto)
        A-->>M: output
        M->>U: preview y decisión s / n / r
        U-->>M: s (aprobar)
        M->>FS: specs, código y checkpoint
    end
    M->>U: ¿Crear rama y PR? s/n
    U-->>M: s
    M->>A: Publicador redacta título y cuerpo
    M->>GIT: clone, rama crewai/feature-fecha, copiar a source/, push
    GIT->>GH: push de la rama
    M->>MCP: manage_prs create (head rama, base main)
    MCP->>GH: crea el PR
    GH-->>U: URL del PR
```

## Referencias

| Pieza | Archivo |
|---|---|
| Orquestación y HITL | [main.py](../main.py) |
| Orden de agentes | [crew/workflow.py](../crew/workflow.py) |
| Cliente MCP de proyectos | [mcp_projects.py](../mcp_projects.py) |
| Agente Publicador | [agents/publisher.py](../agents/publisher.py) |
| Rama, push y PR | [publish.py](../publish.py) |
