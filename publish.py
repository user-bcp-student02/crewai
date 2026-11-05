"""Publica output/ en `source/` del repo de GITHUB_OWNER/GITHUB_REPO y abre el PR por el MCP local.

El MCP local (PROJECTS_MCP_URL) no puede crear ramas ni subir archivos, así que la rama y el
commit se hacen con `git` sobre un clon temporal; el PR se abre con la tool `manage_prs` del MCP.

Variables de entorno:
    GITHUB_OWNER / GITHUB_REPO   Repo destino (el mismo que resuelve el MCP local)
    PUBLISH_BASE_BRANCH          Rama base del PR (default: main)
    PUBLISH_TARGET_DIR           Carpeta destino dentro del repo (default: source)
"""
import os
import re
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

import mcp_projects

EXCLUDED_NAMES = {".checkpoint.json", "node_modules", "dist", "target", "__pycache__", ".angular"}


def target_repo() -> tuple[str, str]:
    owner, repo = os.getenv("GITHUB_OWNER", "").strip(), os.getenv("GITHUB_REPO", "").strip()
    if not owner or not repo:
        raise RuntimeError("Define GITHUB_OWNER y GITHUB_REPO en .env (repo destino de la fuente).")
    return owner, repo


def collect_files(output_dir: Path) -> list[Path]:
    """Rutas relativas a output_dir de los archivos publicables."""
    return [p.relative_to(output_dir) for p in sorted(output_dir.rglob("*"))
            if p.is_file() and not any(part in EXCLUDED_NAMES for part in p.relative_to(output_dir).parts)]


def branch_name(feature_title: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", str(feature_title).lower()).strip("-")[:40] or "feature"
    return f"crewai/{slug}-{time.strftime('%Y%m%d-%H%M%S')}"


def _git(cwd: Path, *args: str) -> str:
    done = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)
    if done.returncode != 0:
        raise RuntimeError(f"git {args[0]} falló: {(done.stderr or done.stdout).strip()[:400]}")
    return done.stdout.strip()


def push_branch(output_dir: Path, owner: str, repo: str, base: str, target: str,
                branch: str, message: str) -> int:
    """Clona el repo, copia output_dir a <target>/ en `branch` y la sube. Retorna nº de archivos."""
    files = collect_files(output_dir)
    if not files:
        raise RuntimeError(f"No hay archivos que publicar en {output_dir}")
    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp) / repo
        _git(Path(tmp), "clone", "--depth", "1", "--branch", base,
             f"https://github.com/{owner}/{repo}.git", str(work))
        _git(work, "checkout", "-b", branch)
        for rel in files:
            dest = work / target / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(output_dir / rel, dest)
        _git(work, "add", "--", target)
        if not _git(work, "status", "--porcelain"):
            raise RuntimeError(f"{target}/ ya está idéntico a {base}: no hay cambios que publicar.")
        identity = []
        if not subprocess.run(["git", "config", "user.email"], cwd=work, capture_output=True, text=True).stdout.strip():
            identity = ["-c", "user.name=crewai-publisher", "-c", "user.email=crewai-publisher@users.noreply.github.com"]
        _git(work, *identity, "commit", "-m", message)
        _git(work, "push", "-u", "origin", branch)
    return len(files)


def open_pull_request(branch: str, base: str, title: str, body: str, draft: bool = False) -> str:
    """Abre el PR con la tool manage_prs del MCP local. Retorna la URL."""
    pr = mcp_projects.call_tool("manage_prs", {
        "action": "create", "title": title, "body": body,
        "head": branch, "base": base, "draft": draft,
    })
    return str(pr.get("url") or pr.get("html_url") or pr.get("raw") or pr)


def publish_source(output_dir: Path, feature_title: str, pr_title: str, pr_body: str,
                   draft: bool = False) -> str:
    owner, repo = target_repo()
    base = os.getenv("PUBLISH_BASE_BRANCH", "main")
    target = os.getenv("PUBLISH_TARGET_DIR", "source").strip("/")
    branch = branch_name(feature_title)
    push_branch(output_dir, owner, repo, base, target, branch, f"feat({target}): {feature_title}")
    return open_pull_request(branch, base, pr_title, pr_body, draft)
