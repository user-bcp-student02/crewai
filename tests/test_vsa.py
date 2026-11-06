"""Reglas de Vertical Slice Architecture: nombres, destino de archivos y validación."""

from pathlib import Path
import tempfile
import unittest

import vsa_archetype as vsa

JAVA = "backend-quarkus/src/{}/java/pe/bcp/{}/{}"


class SliceNameTests(unittest.TestCase):
    def test_names_are_valid_java_packages(self):
        self.assertEqual(vsa.slice_name("Transfer funds"), "transferfunds")
        self.assertEqual(vsa.slice_name("Transferencia entre cuentas propias"), "transferenciacuentas")
        self.assertEqual(vsa.slice_name("¡Pago QR!"), "pagoqr")
        self.assertEqual(vsa.slice_name("123 login"), "f123login")
        self.assertEqual(vsa.slice_name("???"), "feature")
        self.assertEqual(vsa.slice_name("Shared"), "sharedfeature")

    def test_override_wins(self):
        self.assertEqual(vsa.slice_name("Cualquier título", "Wallet Auth"), "walletauth")


class ResolveJavaTests(unittest.TestCase):
    def test_flattens_package_and_imports_into_the_slice(self):
        code = (
            "package pe.bcp.login.service;\n"
            "import pe.bcp.login.model.User;\n"
            "import pe.bcp.shared.error.ApiError;\n"
            "public class AuthService {}\n"
        )
        path, out = vsa.resolve_java("AuthService.java", code, "login")
        self.assertEqual(path, JAVA.format("main", "login", "AuthService.java"))
        self.assertIn("package pe.bcp.login;", out)
        self.assertIn("import pe.bcp.login.User;", out)
        self.assertIn("import pe.bcp.shared.ApiError;", out)

    def test_foreign_package_is_moved_into_the_slice(self):
        path, out = vsa.resolve_java("X.java", "package pe.bcp.billing;\nclass X {}", "login")
        self.assertEqual(path, JAVA.format("main", "login", "X.java"))
        self.assertIn("package pe.bcp.login;", out)

    def test_missing_package_is_added(self):
        _, out = vsa.resolve_java("X.java", "class X {}", "login")
        self.assertTrue(out.startswith("package pe.bcp.login;"))

    def test_shared_and_tests(self):
        path, _ = vsa.resolve_java("ApiError.java", "package pe.bcp.shared;\nclass ApiError {}", "login")
        self.assertEqual(path, JAVA.format("main", "shared", "ApiError.java"))
        path, _ = vsa.resolve_java("LoginServiceTest.java", "class LoginServiceTest {}", "login")
        self.assertEqual(path, JAVA.format("test", "login", "LoginServiceTest.java"))
        path, _ = vsa.resolve_java("Checks.java", "class Checks { @Test void a() {} }", "login")
        self.assertEqual(path, JAVA.format("test", "login", "Checks.java"))


class ValidateTests(unittest.TestCase):
    def write(self, root: Path, source_set: str, package: str, name: str, body: str):
        folder = root / "src" / source_set / "java" / package.replace(".", "/")
        folder.mkdir(parents=True, exist_ok=True)
        (folder / name).write_text(f"package {package};\n{body}\nclass {name[:-5]} {{}}", encoding="utf-8")

    def test_isolated_slices_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write(root, "main", "pe.bcp.login", "A.java", "import pe.bcp.shared.E;")
            self.write(root, "main", "pe.bcp.transfers", "B.java", "")
            self.write(root, "main", "pe.bcp.shared", "E.java", "")
            self.write(root, "test", "pe.bcp.login", "ATest.java", "")
            result = vsa.validate(root)
            self.assertTrue(result["passed"], result["summary"])
            self.assertEqual(result["slices"], ["login", "transfers"])

    def test_cross_slice_import_and_shared_dependency_fail(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write(root, "main", "pe.bcp.login", "A.java", "import pe.bcp.transfers.B;")
            self.write(root, "main", "pe.bcp.transfers", "B.java", "")
            self.write(root, "main", "pe.bcp.shared", "E.java", "import pe.bcp.login.A;")
            result = vsa.validate(root)
            self.assertFalse(result["passed"])
            self.assertEqual(len(result["violations"]), 2)

    def test_layered_subpackages_fail(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write(root, "main", "pe.bcp.login.service", "A.java", "")
            result = vsa.validate(root)
            self.assertFalse(result["passed"])
            self.assertIn("subpaquete", result["violations"][0])

    def test_empty_backend_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertFalse(vsa.validate(tmp)["passed"])


if __name__ == "__main__":
    unittest.main()
