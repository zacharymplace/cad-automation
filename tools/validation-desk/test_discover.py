import subprocess
import tempfile
import unittest
from pathlib import Path

from discover import discover


class DiscoveryTests(unittest.TestCase):
    def test_states_limits_and_no_index_write(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            repo = root / "repo"
            repo.mkdir()

            def git(*args):
                return subprocess.run(["git", "-C", str(repo), *args], check=True,
                                      capture_output=True)

            git("init")
            (repo / "file").write_text("initial")
            git("add", "file")
            git("-c", "user.name=Test", "-c", "user.email=test@example.invalid",
                "commit", "-m", "fixture")
            index = repo / ".git/index"
            before = (index.read_bytes(), index.stat().st_mtime_ns)
            row = discover(root)["repositories"][0]
            self.assertFalse(row["dirty"])
            self.assertEqual(before, (index.read_bytes(), index.stat().st_mtime_ns))
            (repo / "untracked").write_text("new")
            self.assertTrue(discover(root)["repositories"][0]["dirty"])
            git("checkout", "--detach")
            self.assertIsNone(discover(root)["repositories"][0]["branch"])
            (root / "link").symlink_to(repo, target_is_directory=True)
            self.assertTrue(discover(root)["issues"])
            self.assertEqual(discover(root, 0)["repositories"], [])
            self.assertTrue(discover(root, max_directories=1)["issues"])
            worktree = root / "worktree"
            git("worktree", "add", "--detach", str(worktree))
            self.assertEqual(len(discover(root)["repositories"]), 2)

    def test_missing_and_unborn(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.assertTrue(discover(root / "missing")["issues"])
            subprocess.run(["git", "init", str(root)], check=True, capture_output=True)
            self.assertEqual(discover(root)["repositories"][0]["status"], "ERROR")


if __name__ == "__main__":
    unittest.main()
