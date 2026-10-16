"""
Tests for packaging configuration.

Verifies that all required packaging artifacts exist and are correctly
configured for PyInstaller --onedir distribution. These are structural
tests — they validate the packaging setup, not runtime behaviour.
"""

import fnmatch
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class TestGitignore(unittest.TestCase):
    """Verify build artifacts are excluded from version control."""

    def setUp(self):
        gitignore_path = os.path.join(ROOT, ".gitignore")
        with open(gitignore_path, "r") as file_handle:
            self.gitignore_content = file_handle.read()

    def test_dist_folder_excluded(self):
        """dist/ output folder must not be committed."""
        self.assertIn("dist/", self.gitignore_content)

    def test_build_folder_excluded(self):
        """build/ PyInstaller temp folder must not be committed."""
        self.assertIn("build/", self.gitignore_content)

    def test_session_data_side_files_excluded(self):
        """Temp files left by an interrupted save, and copies of an unreadable
        data.json, hold session data and must not be committed."""
        patterns = [
            line.strip()
            for line in self.gitignore_content.splitlines()
            if line.strip() and not line.startswith("#")
        ]
        for name in [
            ".data.json.o8r3usrd.tmp",
            ".settings.json.im360yme.tmp",
            "data.json.unreadable_20261008_142500",
        ]:
            with self.subTest(name=name):
                self.assertTrue(
                    any(fnmatch.fnmatch(name, pattern) for pattern in patterns),
                    f"{name} is not matched by any .gitignore pattern",
                )


class TestAssetsDirectory(unittest.TestCase):
    """Verify assets directory and icon exist."""

    def test_assets_directory_exists(self):
        """assets/ directory must exist for icon and future resources."""
        assets_dir = os.path.join(ROOT, "assets")
        self.assertTrue(
            os.path.isdir(assets_dir),
            "assets/ directory does not exist",
        )

    def test_icon_file_exists(self):
        """icon.ico must exist for window title bar and taskbar icon."""
        icon_path = os.path.join(ROOT, "assets", "icon.ico")
        self.assertTrue(
            os.path.isfile(icon_path),
            "assets/icon.ico does not exist — run assets/generate_icon.py",
        )

    def test_icon_file_is_not_empty(self):
        """icon.ico must have content (not a placeholder empty file)."""
        icon_path = os.path.join(ROOT, "assets", "icon.ico")
        self.assertGreater(
            os.path.getsize(icon_path),
            0,
            "assets/icon.ico is empty",
        )

    def test_generate_icon_script_exists(self):
        """generate_icon.py script must exist to allow icon regeneration."""
        script_path = os.path.join(ROOT, "assets", "generate_icon.py")
        self.assertTrue(
            os.path.isfile(script_path),
            "assets/generate_icon.py does not exist",
        )


class TestSpecFile(unittest.TestCase):
    """Verify PyInstaller spec file exists and contains required config."""

    def setUp(self):
        spec_path = os.path.join(ROOT, "time_tracker.spec")
        self.spec_exists = os.path.isfile(spec_path)
        if self.spec_exists:
            with open(spec_path, "r") as file_handle:
                self.spec_content = file_handle.read()
        else:
            self.spec_content = ""

    def test_spec_file_exists(self):
        """time_tracker.spec must exist for reproducible builds."""
        self.assertTrue(self.spec_exists, "time_tracker.spec does not exist")

    def test_spec_references_entry_point(self):
        """Spec must reference the correct entry point."""
        self.assertIn("time_tracker.py", self.spec_content)

    def test_spec_app_name_is_timealigned(self):
        """Bundled app must be named TimeAligned."""
        self.assertIn("TimeAligned", self.spec_content)

    def test_spec_includes_src_datas(self):
        """Spec must bundle the src/ package as data."""
        self.assertIn("src/", self.spec_content)

    def test_spec_includes_assets_datas(self):
        """Spec must bundle the assets/ folder."""
        self.assertIn("assets/", self.spec_content)

    def test_spec_is_windowed_no_console(self):
        """GUI app must not open a console window on launch."""
        self.assertIn("console=False", self.spec_content)

    def test_spec_references_icon(self):
        """Spec must set the .exe icon."""
        self.assertIn("icon.ico", self.spec_content)


class TestResourcePathHelper(unittest.TestCase):
    """Verify get_resource_path resolves paths correctly in dev mode."""

    def test_get_resource_path_returns_string(self):
        """get_resource_path must return a string path."""
        from src.constants import get_resource_path

        result = get_resource_path("assets/icon.ico")
        self.assertIsInstance(result, str)

    def test_get_resource_path_in_dev_mode(self):
        """In dev mode (no _MEIPASS), path resolves relative to project root."""
        from src.constants import get_resource_path

        result = get_resource_path("assets/icon.ico")
        self.assertIn("assets", result)
        self.assertIn("icon.ico", result)

    def test_get_resource_path_icon_resolves_to_existing_file(self):
        """Resolved icon path must point to an existing file."""
        from src.constants import get_resource_path

        icon_path = get_resource_path("assets/icon.ico")
        self.assertTrue(
            os.path.isfile(icon_path),
            f"Icon not found at resolved path: {icon_path}",
        )


class TestReleaseCleanup(unittest.TestCase):
    """Verify package_release.py strips personal runtime files before zipping.

    Running the built exe from dist/TimeAligned writes data and settings next
    to it. Anything the cleanup misses ships inside the public release zip.
    """

    def setUp(self):
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        self.dist_dir = Path(temp_dir.name) / "TimeAligned"
        (self.dist_dir / "_internal").mkdir(parents=True)
        (self.dist_dir / "TimeAligned.exe").write_bytes(b"exe")
        (self.dist_dir / "_internal" / "python3.dll").write_bytes(b"dll")

    def test_personal_runtime_files_are_removed(self):
        """Session data, backups, settings and Google tokens must never ship."""
        from package_release import clean_runtime_artifacts

        runtime_files = [
            "data.json",
            "data.json.unreadable_20261008_142500",
            ".data.json.o8r3usrd.tmp",  # left by a save interrupted by a crash
            ".settings.json.im360yme.tmp",
            "settings.json",
            "credentials.json",
            "token.pickle",
            "sheets_upload_log.json",
        ]
        for name in runtime_files:
            (self.dist_dir / name).write_text("{}")
        for folder in ["backups", "screenshots"]:
            (self.dist_dir / folder).mkdir()
            (self.dist_dir / folder / "data.json.daily_20261008").write_text("{}")

        clean_runtime_artifacts(self.dist_dir)

        remaining = sorted(path.name for path in self.dist_dir.iterdir())
        self.assertEqual(remaining, ["TimeAligned.exe", "_internal"])


if __name__ == "__main__":
    unittest.main()
