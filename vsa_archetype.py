"""
vsa_archetype.py — Arquetipo Vertical Slice Architecture para el backend Quarkus.

Cada funcionalidad es un slice autocontenido en un único paquete plano:

  pe/bcp/<slice>/    Recurso REST, servicio, acceso a datos, DTOs y excepciones del slice
  pe/bcp/shared/     Solo piezas transversales y estables (errores HTTP, correlación, auditoría)
  src/test/java/pe/bcp/<slice>/   Pruebas del slice
  db/<slice>/        SQL propio del slice

Reglas: un slice nunca importa a otro slice y shared nunca importa a un slice.
Agregar una funcionalidad crea un slice nuevo; no obliga a editar los existentes.

Proporciona:
  - slice_name(title)               : nombre de slice válido como paquete Java
  - vsa_prompt(slice)               : bloque de reglas para inyectar en los prompts
  - resolve_java(name, code, slice) : destino y código normalizado de un archivo Java
  - validate(backend_dir)           : verifica aislamiento y forma plana de los slices
"""
import re
import unicodedata
from pathlib import Path

BASE_PACKAGE = "pe.bcp"
SHARED = "shared"
BASE_DIR = "backend-quarkus"

_STOPWORDS = {
    "a", "al", "con", "de", "del", "el", "en", "entre", "la", "las", "los", "para", "por",
    "un", "una", "y", "o", "the", "of", "to", "and", "for", "in", "on", "with", "an",
}
_PACKAGE_RE = re.compile(r"^[ \t]*package\s+([\w.]+)\s*;", re.MULTILINE)
_IMPORT_RE = re.compile(r"^\s*import\s+(?:static\s+)?pe\.bcp\.(\w+)", re.MULTILINE)
_TEST_FILE_RE = re.compile(r"(?:Tests?|IT)\.java$")


def _words(text: str) -> list[str]:
    ascii_text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return re.findall(r"[a-z0-9]+", ascii_text.lower())


def slice_name(title: str, override: str | None = None) -> str:
    """Nombre de slice: minúsculas, sin separadores, usable como paquete Java."""
    if override and override.strip():
        words = _words(override)
    else:
        words = [w for w in _words(title) if w not in _STOPWORDS][:2]
    name = "".join(words)[:30] or "feature"
    if name[0].isdigit():
        name = "f" + name
    return name + "feature" if name == SHARED else name


def slice_package(slice_: str) -> str:
    return f"{BASE_PACKAGE}.{slice_}"


def vsa_prompt(slice_: str) -> str:
    pkg = slice_package(slice_)
    return f"""
=== VERTICAL SLICE ARCHITECTURE (backend Quarkus) ===
Slice de esta funcionalidad: `{slice_}` → paquete `{pkg}`.
1. Todo el código de la funcionalidad vive en UN paquete plano `{pkg}`: recurso REST,
   servicio o caso de uso, acceso a datos, DTOs y excepciones propias. Sin subpaquetes por
   capa (nada de model/, service/, repository/) y sin interfaces creadas solo para abstraer.
2. Un slice NUNCA importa clases de otro slice (`{BASE_PACKAGE}.<otro>`). Si dos funcionalidades
   se necesitan, se comunican por API o eventos, no por imports.
3. `{BASE_PACKAGE}.{SHARED}` solo recibe piezas transversales y estables (errores HTTP, correlación,
   auditoría, configuración). Nunca lógica de negocio de un slice, y no importa ningún slice.
4. Cada slice es dueño de sus datos: SQL en `db/{slice_}/`, tablas con prefijo `{slice_}_`, claves de
   configuración `bcp.{slice_}.*`, sin claves foráneas ni consultas a tablas de otro slice.
5. Las pruebas van en `src/test/java/pe/bcp/{slice_}/`.
6. Cada archivo Java empieza con `// Nombre.java` y declara `package {pkg};`
   (o `package {BASE_PACKAGE}.{SHARED};` si es transversal).
7. Evolucionar es agregar slices; cambiar este slice no debe obligar a tocar otros.
=====================================================
"""


def resolve_java(filename: str, code: str, slice_: str) -> tuple[str, str]:
    """Devuelve (ruta relativa a output/, código) con paquete e imports aplanados al slice."""
    slice_pkg = slice_package(slice_)
    shared_pkg = f"{BASE_PACKAGE}.{SHARED}"

    declared = _PACKAGE_RE.search(code)
    package = slice_pkg
    if declared and (declared.group(1) == shared_pkg or declared.group(1).startswith(shared_pkg + ".")):
        package = shared_pkg

    package_line = f"package {package};"
    if declared:
        code = _PACKAGE_RE.sub(lambda _: package_line, code, count=1)
    else:
        code = package_line + "\n\n" + code

    for root in (slice_pkg, shared_pkg):
        code = re.sub(
            rf"(\bimport\s+(?:static\s+)?){re.escape(root)}(?:\.[a-z]\w*)+\.(?=[A-Z*])",
            lambda m, root=root: f"{m.group(1)}{root}.",
            code,
        )

    source_set = "test" if _TEST_FILE_RE.search(filename) or "@Test" in code else "main"
    path = f"{BASE_DIR}/src/{source_set}/java/{package.replace('.', '/')}/{filename}"
    return path, code


def _java_files(directory: Path):
    return sorted(f for f in directory.rglob("*.java") if f.is_file())


def validate(backend_dir: Path | str) -> dict:
    """Verifica que los slices sean planos y no dependan unos de otros."""
    root = Path(backend_dir)
    violations: list[str] = []
    slices: list[str] = []

    for source_set in ("main", "test"):
        base = root / "src" / source_set / "java" / "pe" / "bcp"
        if not base.is_dir():
            continue
        for slice_dir in sorted(d for d in base.iterdir() if d.is_dir()):
            owner = slice_dir.name
            if owner != SHARED and source_set == "main" and owner not in slices:
                slices.append(owner)
            for sub in (d for d in slice_dir.rglob("*") if d.is_dir()):
                violations.append(
                    f"{source_set}/{owner}: subpaquete '{sub.relative_to(slice_dir).as_posix()}' (el slice debe ser plano)"
                )
            for java in _java_files(slice_dir):
                text = java.read_text(encoding="utf-8", errors="ignore")
                imported = {m.group(1) for m in _IMPORT_RE.finditer(text)}
                allowed = {owner} if owner == SHARED else {owner, SHARED}
                for other in sorted(imported - allowed):
                    who = "shared importa slice" if owner == SHARED else "importa slice"
                    violations.append(f"{source_set}/{owner}/{java.name}: {who} '{other}'")

    passed = bool(slices) and not violations
    lines = ["[vsa_archetype] Validación de Vertical Slice Architecture:"]
    lines.append(f"  Slices: {', '.join(slices) if slices else 'ninguno'}")
    lines.append(f"  {'OK' if not violations else 'XX'} slices planos y sin imports entre slices")
    lines.extend(f"    !! {v}" for v in violations)
    if not slices:
        lines.append("    !! No hay código en src/main/java/pe/bcp/<slice>/")
    lines.append(f"  RESULTADO: {'APROBADO' if passed else 'RECHAZADO'}")
    summary = "\n".join(lines)
    return {"slices": slices, "violations": violations, "passed": passed, "summary": summary}
