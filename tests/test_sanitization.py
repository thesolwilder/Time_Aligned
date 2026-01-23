"""
Tests for Input Sanitization

Verifies that user inputs are properly sanitized to prevent security issues.
"""

import unittest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.ui_helpers import sanitize_name, escape_for_sheets, validate_folder_path


class TestSanitizeName(unittest.TestCase):
    """Test sanitization of names (spheres, projects, break actions)"""

    def test_valid_names_unchanged(self):
        """Test that valid names are not modified"""
        valid_names = [
            "Work",
            "Personal Projects",
            "Health-Wellness",
            "Learning_2024",
            "Side Project 123",
        ]

        for name in valid_names:
            sanitized = sanitize_name(name)
            self.assertEqual(sanitized, name)

    def test_dangerous_chars_removed(self):
        """Test that dangerous characters are replaced with underscores"""
        dangerous_inputs = [
            ("../../../etc/passwd", "______etc_passwd"),  # .. becomes _
            ("Project/With/Slashes", "Project_With_Slashes"),
            ("Project\\With\\Backslashes", "Project_With_Backslashes"),
            ("Project:With:Colons", "Project_With_Colons"),
            ("Project*With?Wildcards", "Project_With_Wildcards"),
            ('Project"With"Quotes', "Project_With_Quotes"),
            ("Project<With>Brackets", "Project_With_Brackets"),
            ("Project|With|Pipes", "Project_With_Pipes"),
            ("Project{With}Braces", "Project_With_Braces"),
        ]

        for malicious, expected in dangerous_inputs:
            sanitized = sanitize_name(malicious)
            self.assertEqual(sanitized, expected, f"Failed for: {malicious}")

    def test_max_length_enforced(self):
        """Test that maximum length is enforced"""
        long_name = "A" * 100
        sanitized = sanitize_name(long_name, max_length=50)
        self.assertEqual(len(sanitized), 50)

        # Default max length
        sanitized_default = sanitize_name(long_name)
        self.assertEqual(len(sanitized_default), 50)

    def test_whitespace_trimmed(self):
        """Test that leading/trailing whitespace is removed"""
        self.assertEqual(sanitize_name("  Work  "), "Work")
        self.assertEqual(sanitize_name("\tProject\t"), "Project")
        self.assertEqual(sanitize_name("\nSphere\n"), "Sphere")

    def test_empty_input_returns_empty(self):
        """Test that empty or None input returns empty string"""
        self.assertEqual(sanitize_name(""), "")
        self.assertEqual(sanitize_name(None), "")
        self.assertEqual(sanitize_name("   "), "")

    def test_newlines_and_tabs_removed(self):
        """Test that newlines and tabs are replaced"""
        self.assertEqual(
            sanitize_name("Project\nWith\nNewlines"), "Project_With_Newlines"
        )
        self.assertEqual(sanitize_name("Project\tWith\tTabs"), "Project_With_Tabs")
        self.assertEqual(
            sanitize_name("Project\r\nWith\r\nCRLF"), "Project__With__CRLF"
        )


class TestEscapeForSheets(unittest.TestCase):
    """Test escaping for Google Sheets upload"""

    def test_normal_text_unchanged(self):
        """Test that normal text is not modified"""
        normal_texts = [
            "Regular text",
            "Project notes",
            "Meeting at 2pm",
            "Completed task",
        ]

        for text in normal_texts:
            escaped = escape_for_sheets(text)
            self.assertEqual(escaped, text)

    def test_formula_injection_prevented(self):
        """Test that formula injection is prevented"""
        dangerous_formulas = [
            ("=cmd|'/c calc'!A1", "'=cmd|'/c calc'!A1"),
            ("+1+1", "'+1+1"),
            ("-1-1", "'-1-1"),
            ("@SUM(A1:A10)", "'@SUM(A1:A10)"),
            ("|command", "'|command"),
        ]

        for malicious, expected in dangerous_formulas:
            escaped = escape_for_sheets(malicious)
            self.assertEqual(escaped, expected)

    def test_xss_prevented(self):
        """Test that XSS is prevented"""
        xss_attacks = [
            (
                "<script>alert('xss')</script>",
                "&lt;script&gt;alert('xss')&lt;/script&gt;",
            ),
            ("<img src=x onerror=alert(1)>", "&lt;img src=x onerror=alert(1)&gt;"),
            ("<a href='javascript:alert(1)'>", "&lt;a href='javascript:alert(1)'&gt;"),
        ]

        for malicious, expected in xss_attacks:
            escaped = escape_for_sheets(malicious)
            self.assertEqual(escaped, expected)

    def test_combined_attacks_prevented(self):
        """Test that combined attacks are prevented"""
        # Formula injection + XSS
        malicious = "=<script>alert('xss')</script>"
        escaped = escape_for_sheets(malicious)
        # Should prefix with ' and escape < >
        self.assertTrue(escaped.startswith("'="))
        self.assertIn("&lt;", escaped)
        self.assertIn("&gt;", escaped)

    def test_empty_input_returns_empty(self):
        """Test that empty or None input returns empty string"""
        self.assertEqual(escape_for_sheets(""), "")
        self.assertEqual(escape_for_sheets(None), "")


class TestValidateFolderPath(unittest.TestCase):
    """Test folder path validation"""

    def test_safe_paths_accepted(self):
        """Test that safe relative paths are accepted"""
        safe_paths = [
            "screenshots/session_123",
            "data/backups",
            "logs/2024-01-20",
        ]

        for path in safe_paths:
            self.assertTrue(validate_folder_path(path))

    def test_path_traversal_rejected(self):
        """Test that path traversal is rejected"""
        dangerous_paths = [
            "../../../etc/passwd",
            "..\\..\\Windows\\System32",
            "~/sensitive/data",
            "/etc/shadow",
            "C:\\Windows\\System32",
            "%APPDATA%/secrets",
            "${HOME}/secrets",
            "$env:USERPROFILE/secrets",
            "/root/.ssh",
        ]

        for path in dangerous_paths:
            self.assertFalse(validate_folder_path(path))

    def test_empty_path_rejected(self):
        """Test that empty path is rejected"""
        self.assertFalse(validate_folder_path(""))
        self.assertFalse(validate_folder_path(None))


class TestIntegrationSanitization(unittest.TestCase):
    """Test integration of sanitization in actual use cases"""

    def test_sphere_name_sanitization(self):
        """Test sanitization prevents malicious sphere names"""
        malicious_sphere = "../../../etc/passwd"
        sanitized = sanitize_name(malicious_sphere)

        # Should be safe to use in file paths
        self.assertNotIn("..", sanitized)
        self.assertNotIn("/", sanitized)
        self.assertNotIn("\\", sanitized)

    def test_project_name_sanitization(self):
        """Test sanitization prevents malicious project names"""
        malicious_project = "<script>alert('xss')</script>"
        sanitized = sanitize_name(malicious_project)

        # Should be safe for display and storage
        self.assertNotIn("<", sanitized)
        self.assertNotIn(">", sanitized)

    def test_comment_escaping_for_sheets(self):
        """Test that comments are escaped before Google Sheets upload"""
        malicious_comment = "=cmd|'/c calc'!A1"
        escaped = escape_for_sheets(malicious_comment)

        # Should prevent formula execution
        self.assertTrue(escaped.startswith("'"))

    def test_round_trip_sanitization(self):
        """Test that sanitized data can be stored and retrieved"""
        original = "Work/Life Balance"
        sanitized = sanitize_name(original)

        # Should be valid and usable
        self.assertIsInstance(sanitized, str)
        self.assertGreater(len(sanitized), 0)
        self.assertEqual(sanitized, "Work_Life Balance")


if __name__ == "__main__":
    unittest.main()
