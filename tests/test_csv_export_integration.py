"""
Integration Test for CSV Export Feature

This test verifies the complete CSV export functionality end-to-end.
"""

import unittest
import json
import os
import sys
import csv
import tempfile
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from tests.test_helpers import TestDataGenerator, TestFileManager


class TestCSVExportIntegration(unittest.TestCase):
    """Integration test for complete CSV export functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.file_manager = TestFileManager()

        # Create comprehensive test data
        self.test_data = {
            "2026-01-20_1737374400": {
                "sphere": "Coding",
                "date": "2026-01-20",
                "start_time": "12:00:00",
                "start_timestamp": 1737374400.0,
                "breaks": [
                    {
                        "start": "13:00:00",
                        "start_timestamp": 1737378000.0,
                        "duration": 300,
                        "action": "bathroom",
                        "comment": "Quick break",
                    },
                    {
                        "start": "14:30:00",
                        "start_timestamp": 1737383400.0,
                        "duration": 600,
                        "action": "lunch",
                        "comment": "Lunch break",
                    },
                ],
                "active": [
                    {
                        "start": "12:00:00",
                        "start_timestamp": 1737374400.0,
                        "end": "13:00:00",
                        "end_timestamp": 1737378000.0,
                        "duration": 3600,
                        "project": "learning_to_code",
                        "comment": "Work session 1",
                    },
                    {
                        "start": "13:05:00",
                        "start_timestamp": 1737378300.0,
                        "end": "14:30:00",
                        "end_timestamp": 1737383400.0,
                        "duration": 5100,
                        "project": "learning_to_code",
                        "comment": "Work session 2",
                    },
                ],
                "idle_periods": [
                    {
                        "start": "15:40:00",
                        "start_timestamp": 1737387600.0,
                        "end": "15:50:00",
                        "end_timestamp": 1737388200.0,
                        "duration": 600,
                    }
                ],
                "end_time": "15:50:00",
                "end_timestamp": 1737388200.0,
                "total_duration": 13800.0,
                "active_duration": 8700,
                "break_duration": 900,
                "session_comments": {
                    "active_notes": "Productive coding session",
                    "break_notes": "Needed those breaks",
                    "idle_notes": "Got distracted",
                    "session_notes": "Overall good day",
                },
            },
            "2026-01-21_1737460800": {
                "sphere": "General",
                "date": "2026-01-21",
                "start_time": "09:00:00",
                "start_timestamp": 1737460800.0,
                "breaks": [],
                "active": [
                    {
                        "start": "09:00:00",
                        "start_timestamp": 1737460800.0,
                        "end": "10:00:00",
                        "end_timestamp": 1737464400.0,
                        "duration": 3600,
                        "project": "Email",
                        "comment": "Checking emails",
                    }
                ],
                "idle_periods": [],
                "end_time": "10:00:00",
                "end_timestamp": 1737464400.0,
                "total_duration": 3600.0,
                "active_duration": 3600,
                "break_duration": 0,
                "session_comments": {
                    "active_notes": "",
                    "break_notes": "",
                    "idle_notes": "",
                    "session_notes": "Quick morning check-in",
                },
            },
        }

        self.test_data_file = self.file_manager.create_test_file(
            "test_csv_integration_data.json", self.test_data
        )

    def tearDown(self):
        """Clean up"""
        self.file_manager.cleanup()

    def test_full_csv_export_integration(self):
        """Test complete CSV export from JSON to CSV file"""
        # Simulate the export function behavior
        with open(self.test_data_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Create temporary CSV file
        with tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix=".csv", newline="", encoding="utf-8"
        ) as temp_csv:
            csv_file_path = temp_csv.name

        try:
            # Convert data to CSV format (same logic as save_all_data_to_csv)
            csv_rows = []

            for session_id, session_data in data.items():
                sphere = session_data.get("sphere", "")
                date = session_data.get("date", "")
                start_time = session_data.get("start_time", "")
                end_time = session_data.get("end_time", "")
                total_duration = session_data.get("total_duration", 0)
                active_duration = session_data.get("active_duration", 0)
                break_duration = session_data.get("break_duration", 0)

                session_comments = session_data.get("session_comments", {})
                active_notes = session_comments.get("active_notes", "")
                break_notes = session_comments.get("break_notes", "")
                idle_notes = session_comments.get("idle_notes", "")
                session_notes = session_comments.get("session_notes", "")

                # Process active periods
                for active in session_data.get("active", []):
                    row = {
                        "session_id": session_id,
                        "date": date,
                        "sphere": sphere,
                        "session_start_time": start_time,
                        "session_end_time": end_time,
                        "session_total_duration": total_duration,
                        "session_active_duration": active_duration,
                        "session_break_duration": break_duration,
                        "type": "active",
                        "project": active.get("project", ""),
                        "activity_start": active.get("start", ""),
                        "activity_end": active.get("end", ""),
                        "activity_duration": active.get("duration", 0),
                        "activity_comment": active.get("comment", ""),
                        "break_action": "",
                        "active_notes": active_notes,
                        "break_notes": break_notes,
                        "idle_notes": idle_notes,
                        "session_notes": session_notes,
                    }
                    csv_rows.append(row)

                # Process breaks
                for brk in session_data.get("breaks", []):
                    row = {
                        "session_id": session_id,
                        "date": date,
                        "sphere": sphere,
                        "session_start_time": start_time,
                        "session_end_time": end_time,
                        "session_total_duration": total_duration,
                        "session_active_duration": active_duration,
                        "session_break_duration": break_duration,
                        "type": "break",
                        "project": "",
                        "activity_start": brk.get("start", ""),
                        "activity_end": "",
                        "activity_duration": brk.get("duration", 0),
                        "activity_comment": brk.get("comment", ""),
                        "break_action": brk.get("action", ""),
                        "active_notes": active_notes,
                        "break_notes": break_notes,
                        "idle_notes": idle_notes,
                        "session_notes": session_notes,
                    }
                    csv_rows.append(row)

                # Process idle periods
                for idle in session_data.get("idle_periods", []):
                    row = {
                        "session_id": session_id,
                        "date": date,
                        "sphere": sphere,
                        "session_start_time": start_time,
                        "session_end_time": end_time,
                        "session_total_duration": total_duration,
                        "session_active_duration": active_duration,
                        "session_break_duration": break_duration,
                        "type": "idle",
                        "project": "",
                        "activity_start": idle.get("start", ""),
                        "activity_end": idle.get("end", ""),
                        "activity_duration": idle.get("duration", 0),
                        "activity_comment": "",
                        "break_action": "",
                        "active_notes": active_notes,
                        "break_notes": break_notes,
                        "idle_notes": idle_notes,
                        "session_notes": session_notes,
                    }
                    csv_rows.append(row)

            # Write to CSV
            with open(csv_file_path, "w", newline="", encoding="utf-8") as f:
                fieldnames = [
                    "session_id",
                    "date",
                    "sphere",
                    "session_start_time",
                    "session_end_time",
                    "session_total_duration",
                    "session_active_duration",
                    "session_break_duration",
                    "type",
                    "project",
                    "activity_start",
                    "activity_end",
                    "activity_duration",
                    "activity_comment",
                    "break_action",
                    "active_notes",
                    "break_notes",
                    "idle_notes",
                    "session_notes",
                ]
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(csv_rows)

            # Verify CSV file was created
            self.assertTrue(os.path.exists(csv_file_path))
            self.assertTrue(os.path.getsize(csv_file_path) > 0)

            # Read back the CSV and verify content
            with open(csv_file_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                csv_data = list(reader)

            # Verify row count (2 active + 2 breaks + 1 idle = 5 rows for first session, 1 active for second = 6 total)
            expected_row_count = (
                2 + 2 + 1 + 1
            )  # First session: 2 active, 2 breaks, 1 idle; Second session: 1 active
            self.assertEqual(
                len(csv_data),
                expected_row_count,
                f"Expected {expected_row_count} rows, got {len(csv_data)}",
            )

            # Verify data integrity
            active_rows = [row for row in csv_data if row["type"] == "active"]
            break_rows = [row for row in csv_data if row["type"] == "break"]
            idle_rows = [row for row in csv_data if row["type"] == "idle"]

            self.assertEqual(
                len(active_rows), 3
            )  # 2 from first session + 1 from second
            self.assertEqual(len(break_rows), 2)  # 2 from first session
            self.assertEqual(len(idle_rows), 1)  # 1 from first session

            # Verify first active period data
            first_active = active_rows[0]
            self.assertEqual(first_active["sphere"], "Coding")
            self.assertEqual(first_active["project"], "learning_to_code")
            self.assertEqual(first_active["activity_duration"], "3600")
            self.assertEqual(first_active["activity_comment"], "Work session 1")

            # Verify break data
            first_break = break_rows[0]
            self.assertEqual(first_break["break_action"], "bathroom")
            self.assertEqual(first_break["activity_duration"], "300")

            # Verify session comments are preserved
            self.assertEqual(first_active["session_notes"], "Overall good day")
            self.assertEqual(first_active["active_notes"], "Productive coding session")

        finally:
            # Clean up temporary file
            if os.path.exists(csv_file_path):
                os.remove(csv_file_path)


if __name__ == "__main__":
    unittest.main()
