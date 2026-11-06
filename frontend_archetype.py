"""
frontend_archetype.py — Arquetipo de feature slice para el frontend Angular.

Espejo de vsa_archetype.py: cada funcionalidad vive en su propia carpeta y no
toca los archivos de otra.

  frontend-angular/src/app/<slice>/   componentes, servicio, modelos, rutas y estilos del slice
  frontend-angular/src/app/shared/    solo piezas transversales y estables
  frontend-angular/src/app/app.routes.ts, app.component.ts, src/main.ts
                                      los genera el andamiaje, nunca el modelo

El nombre del slice se deriva solo del título del issue (vsa_archetype.slice_name),
así backend y frontend comparten nombre sin leerse entre sí.

Proporciona:
  - fsa_prompt(slice)                 : bloque de reglas para inyectar en los prompts
  - resolve_frontend(name, code, slice): destino de un archivo Angular (None si es del andamiaje)
  - sync_routes(output_dir)           : regenera app.routes.ts con una ruta lazy por slice
  - validate(frontend_dir)            : verifica aislamiento entre slices
"""
import posixpath
import re
from pathlib import Path

FRONT_DIR = "frontend-angular"
SHARED = "shared"
SLICE_EXTENSIONS = (".ts", ".html", ".css")
SCAFFOLD_OWNED = ("app.component.ts", "app.routes.ts", "main.ts")

_IMPORT_RE = re.compile(r"""(?:\bfrom\s+|\bimport\s*\(\s*)['"](\.{1,2}/[^'"]+)['"]""")

APP_COMPONENT_TS = """import { Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet],
  template: '<router-outlet />'
})
export class AppComponent {}
"""


def slice_dir(slice_: str) -> str:
    return f"{FRONT_DIR}/src/app/{slice_}"


def fsa_prompt(slice_: str) -> str:
    return f"""
=== FEATURE SLICE (frontend Angular) ===
Slice de esta funcionalidad: `{slice_}` → carpeta `src/app/{slice_}/`.
1. Todo el código de la funcionalidad vive en UNA carpeta plana `src/app/{slice_}/`: componentes
   standalone, servicio HTTP, modelos, estilos y rutas. Sin subcarpetas.
2. El slice NUNCA importa archivos de otro slice (`../<otro>/...`). Solo puede importar de su
   propia carpeta o de `../{SHARED}/` si ya existe.
3. Expón las rutas del slice en `{slice_}.routes.ts` con `export const routes: Routes = [...]`
   (rutas relativas al slice, p. ej. path '' para la pantalla principal). El andamiaje las
   registra de forma lazy en `app.routes.ts`.
4. NO generes `app.component.ts`, `app.routes.ts` ni `main.ts`: pertenecen al andamiaje.
5. Cada archivo empieza con `// nombre.ext` (primera línea) y usa nombres propios del slice.
6. El slice habla con el backend solo por HTTP según el contrato de API aprobado; no importa ni
   asume código Java ni su estructura interna.
========================================
"""


def resolve_frontend(filename: str, code: str, slice_: str) -> tuple[str, str] | None:
    """Devuelve (ruta relativa a output/, código) o None si el archivo es del andamiaje."""
    name = Path(filename.strip()).name
    if name in SCAFFOLD_OWNED or not name.endswith(SLICE_EXTENSIONS):
        return None
    return f"{slice_dir(slice_)}/{name}", code


def _app_dir(output_dir: Path | str) -> Path:
    return Path(output_dir) / FRONT_DIR / "src" / "app"


def _slices(app_dir: Path) -> list[str]:
    if not app_dir.is_dir():
        return []
    return sorted(d.name for d in app_dir.iterdir() if d.is_dir() and d.name != SHARED)


def sync_routes(output_dir: Path | str) -> list[str]:
    """Regenera app.routes.ts: una ruta lazy por slice que exponga <slice>.routes.ts."""
    app_dir = _app_dir(output_dir)
    app_dir.mkdir(parents=True, exist_ok=True)
    routed = [s for s in _slices(app_dir) if (app_dir / s / f"{s}.routes.ts").is_file()]
    entries = "".join(
        f"  {{ path: '{s}', loadChildren: () => import('./{s}/{s}.routes').then(m => m.routes) }},\n"
        for s in routed
    )
    content = f"import {{ Routes }} from '@angular/router';\n\nexport const routes: Routes = [\n{entries}];\n"
    target = app_dir / "app.routes.ts"
    if not target.is_file() or target.read_text(encoding="utf-8") != content:
        target.write_text(content, encoding="utf-8")
    component = app_dir / "app.component.ts"
    if not component.is_file():
        component.write_text(APP_COMPONENT_TS, encoding="utf-8")
    return routed


def validate(frontend_dir: Path | str) -> dict:
    """Verifica que cada slice sea plano y no importe a otro slice."""
    app_dir = Path(frontend_dir) / "src" / "app"
    violations: list[str] = []
    slices = _slices(app_dir)
    for owner in slices:
        slice_path = app_dir / owner
        for sub in (d for d in slice_path.rglob("*") if d.is_dir()):
            violations.append(f"{owner}: subcarpeta '{sub.relative_to(slice_path).as_posix()}' (el slice debe ser plano)")
        for file in sorted(f for f in slice_path.iterdir() if f.is_file() and f.suffix == ".ts"):
            text = file.read_text(encoding="utf-8", errors="ignore")
            for rel in _IMPORT_RE.findall(text):
                target = posixpath.normpath(posixpath.join(owner, rel)).split("/")[0]
                if target != owner and target != SHARED:
                    violations.append(f"{owner}/{file.name}: importa fuera del slice '{rel}'")

    passed = bool(slices) and not violations
    lines = ["[frontend_archetype] Validación de feature slices Angular:"]
    lines.append(f"  Slices: {', '.join(slices) if slices else 'ninguno'}")
    lines.append(f"  {'OK' if not violations else 'XX'} slices planos y sin imports entre slices")
    lines.extend(f"    !! {v}" for v in violations)
    if not slices:
        lines.append("    !! No hay código en src/app/<slice>/")
    lines.append(f"  RESULTADO: {'APROBADO' if passed else 'RECHAZADO'}")
    return {"slices": slices, "violations": violations, "passed": passed, "summary": "\n".join(lines)}
