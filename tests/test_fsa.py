"""Aislamiento backend/frontend: cada lado depende solo del issue y del contrato."""

import contextlib
import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import frontend_archetype as fsa
import main as app
from crew.workflow import context_sources

OUTPUTS = {
    "architect": "CONTRATO",
    "data": "SQL-DATOS",
    "backend": "CODIGO-JAVA",
    "frontend": "CODIGO-ANGULAR",
}

FRONT_BLOCK = "```typescript\n// {name}\n{body}\n```\n"


class ContextIsolationTests(unittest.TestCase):
    def test_backend_never_sees_frontend_and_vice_versa(self):
        backend_ctx = app.build_context_note(OUTPUTS, "backend")
        frontend_ctx = app.build_context_note(OUTPUTS, "frontend")
        self.assertIn("CONTRATO", backend_ctx)
        self.assertIn("SQL-DATOS", backend_ctx)
        self.assertNotIn("CODIGO-ANGULAR", backend_ctx)
        self.assertIn("CONTRATO", frontend_ctx)
        for hidden in ("CODIGO-JAVA", "SQL-DATOS"):
            self.assertNotIn(hidden, frontend_ctx)

    def test_review_roles_see_everything(self):
        self.assertIsNone(context_sources("chapter"))
        note = app.build_context_note(OUTPUTS, "chapter")
        for text in OUTPUTS.values():
            self.assertIn(text, note)


class ExtractionScopeTests(unittest.TestCase):
    def extract(self, text, step, slice_="reportes"):
        with tempfile.TemporaryDirectory() as tmp, contextlib.redirect_stdout(io.StringIO()):
            with patch.object(app, "OUTPUT_DIR", Path(tmp)):
                saved = app.extract_and_save_code(text, slice_, step)
            files = sorted(p.relative_to(tmp).as_posix() for p in Path(tmp).rglob("*") if p.is_file())
        return saved, files

    def test_frontend_step_only_writes_inside_its_slice(self):
        text = (
            FRONT_BLOCK.format(name="reportes.service.ts", body="export class ReportesService {}")
            + FRONT_BLOCK.format(name="app.routes.ts", body="export const routes = [];")
            + "```java\n// Foo.java\npackage pe.bcp.reportes;\npublic class Foo {}\n```\n"
        )
        saved, _ = self.extract(text, "frontend")
        self.assertEqual(saved, ["frontend-angular/src/app/reportes/reportes.service.ts"])

    def test_backend_step_cannot_write_angular(self):
        text = (
            FRONT_BLOCK.format(name="reportes.service.ts", body="export class ReportesService {}")
            + "```java\n// Foo.java\npackage pe.bcp.reportes;\npublic class Foo {}\n```\n"
        )
        saved, _ = self.extract(text, "backend")
        self.assertEqual(saved, ["backend-quarkus/src/main/java/pe/bcp/reportes/Foo.java"])

    def test_unnamed_angular_code_uses_slice_name_not_auth(self):
        text = "```typescript\n@Component({selector: 'x'})\nexport class XComponent {}\n```\n"
        saved, _ = self.extract(text, "frontend")
        self.assertEqual(saved, ["frontend-angular/src/app/reportes/reportes.component.ts"])

    def test_two_features_do_not_overwrite_each_other(self):
        first, _ = self.extract(FRONT_BLOCK.format(name="main.service.ts", body="export class A {}"), "frontend", "alpha")
        second, _ = self.extract(FRONT_BLOCK.format(name="main.service.ts", body="export class B {}"), "frontend", "beta")
        self.assertNotEqual(first, second)


class FrontendArchetypeTests(unittest.TestCase):
    def write(self, root, rel, text):
        path = Path(root) / "src" / "app" / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def test_routes_are_registered_lazily_per_slice(self):
        with tempfile.TemporaryDirectory() as tmp:
            front = Path(tmp) / fsa.FRONT_DIR
            self.write(front, "alpha/alpha.routes.ts", "export const routes = [];")
            self.write(front, "beta/beta.service.ts", "export class B {}")
            self.write(front, "gamma/gamma.routes.ts", "export const routes = [];")
            self.assertEqual(fsa.sync_routes(tmp), ["alpha", "gamma"])
            routes = (front / "src/app/app.routes.ts").read_text()
            self.assertIn("./alpha/alpha.routes", routes)
            self.assertIn("./gamma/gamma.routes", routes)
            self.assertNotIn("beta", routes)

    def test_validate_flags_cross_slice_imports(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.write(tmp, "alpha/a.service.ts", "import { B } from '../beta/b.service';")
            self.write(tmp, "beta/b.service.ts", "import { S } from '../shared/s';\nimport { X } from './x';")
            result = fsa.validate(tmp)
            self.assertFalse(result["passed"])
            self.assertEqual(len(result["violations"]), 1)
            self.assertIn("alpha/a.service.ts", result["violations"][0])

    def test_validate_passes_for_isolated_slices(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.write(tmp, "alpha/a.service.ts", "import { M } from './a.models';")
            self.assertTrue(fsa.validate(tmp)["passed"])


if __name__ == "__main__":
    unittest.main()
