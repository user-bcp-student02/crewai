"""Publicación de output/ sin red: MCP simulado y push real contra un remoto git local."""

from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import publish


class PublishTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.out = Path(self.tmp.name) / "output"
        (self.out / "specs").mkdir(parents=True)
        (self.out / "specs" / "a.md").write_text("hola", encoding="utf-8")
        (self.out / ".checkpoint.json").write_text("{}", encoding="utf-8")
        (self.out / "node_modules").mkdir()
        (self.out / "node_modules" / "x.js").write_text("x", encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def test_collect_files_skips_noise(self):
        self.assertEqual([p.as_posix() for p in publish.collect_files(self.out)], ["specs/a.md"])

    def test_target_repo_requires_env(self):
        with patch.dict("os.environ", {"GITHUB_OWNER": "", "GITHUB_REPO": ""}):
            with self.assertRaises(RuntimeError):
                publish.target_repo()

    def test_publish_pushes_branch_then_opens_pr_with_mcp(self):
        env = {"GITHUB_OWNER": "o", "GITHUB_REPO": "r", "PUBLISH_BASE_BRANCH": "main", "PUBLISH_TARGET_DIR": "source"}
        with patch.dict("os.environ", env), \
             patch.object(publish, "push_branch", return_value=1) as push, \
             patch.object(publish.mcp_projects, "call_tool", return_value={"url": "https://x/pull/1"}) as call:
            url = publish.publish_source(self.out, "Mi feature", "t", "b", draft=True)
        self.assertEqual(url, "https://x/pull/1")
        branch = push.call_args.args[5]
        self.assertTrue(branch.startswith("crewai/mi-feature-"))
        call.assert_called_once_with("manage_prs", {
            "action": "create", "title": "t", "body": "b", "head": branch, "base": "main", "draft": True})

    def test_push_branch_copies_files_under_target_in_a_git_remote(self):
        remote = Path(self.tmp.name) / "r.git"
        remote.mkdir()
        seed = Path(self.tmp.name) / "seed"
        seed.mkdir()

        def run(cwd, *args):
            subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True)

        run(remote, "init", "--bare", "-b", "main")
        run(seed, "init", "-b", "main")
        (seed / "README.md").write_text("x", encoding="utf-8")
        run(seed, "add", ".")
        run(seed, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-m", "init")
        run(seed, "push", str(remote), "main")

        real_git = publish._git

        def local_git(cwd, *args):
            if args[0] == "clone":
                args = (*args[:-2], str(remote), args[-1])
            return real_git(cwd, *args)

        with patch.object(publish, "_git", side_effect=local_git):
            count = publish.push_branch(self.out, "o", "r", "main", "source", "crewai/t", "msg")
        self.assertEqual(count, 1)
        listing = subprocess.run(["git", f"--git-dir={remote}", "ls-tree", "-r", "--name-only", "crewai/t"],
                                 capture_output=True, text=True).stdout.split()
        self.assertEqual(sorted(listing), ["README.md", "source/specs/a.md"])

    def test_publish_rejects_empty_output(self):
        empty = Path(self.tmp.name) / "empty"
        empty.mkdir()
        with self.assertRaises(RuntimeError):
            publish.push_branch(empty, "o", "r", "main", "source", "b", "m")


if __name__ == "__main__":
    unittest.main()
