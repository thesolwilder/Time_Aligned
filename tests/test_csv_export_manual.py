"""
Manual test script to demonstrate CSV export with secondary project/action fields
Run this to generate a sample CSV file to inspect the output
"""

import json
import os
import sys
import tempfile
import csv

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

def create_sample_data_with_secondary():
    """Create sample data that includes secondary projects and actions"""
    return {
        "2026-01-28_1000000000": {
            "sphere": "Coding",
            "date": "2026-01-28",
            "start_time": "10:00:00",
            "start_timestamp": 1000000000.0,
            "breaks": [
                {
                    "start": "11:00:00",
                    "start_timestamp": 1000003600.0,
                    "duration": 600,
                    "actions": [
                        {
                            "name": "bathroom",
                            "action_primary": True,
                            "comment": "Quick break",
                            "percentage": 60
                        },
                        {
                            "name": "stretching",
                            "action_primary": False,
                            "comment": "Some stretching exercises",
                            "percentage": 40
                        }
                    ]
                }
            ],
            "active": [
                {
                    "start": "10:00:00",
                    "start_timestamp": 1000000000.0,
                    "end": "11:00:00",
                    "end_timestamp": 1000003600.0,
                    "duration": 3600,
                    "projects": [
                        {
                            "name": "learning_to_code",
                            "project_primary": True,
                            "comment": "Working on Python skills",
                            "percentage": 70
                        },
                        {
                            "name": "documentation",
                            "project_primary": False,
                            "comment": "Writing docs for the project",
                            "percentage": 30
                        }
                    ]
                }
            ],
            "idle_periods": [],
            "end_time": "11:10:00",
            "end_timestamp": 1000004200.0,
            "total_duration": 4200.0,
            "active_duration": 3600,
            "break_duration": 600,
            "session_comments": {
                "active_notes": "Very productive session",
                "break_notes": "Needed the stretch",
                "idle_notes": "",
                "session_notes": "Good progress on the Python project",
            },
        },
        "2026-01-28_2000000000": {
            "sphere": "Personal",
            "date": "2026-01-28",
            "start_time": "14:00:00",
            "start_timestamp": 2000000000.0,
            "breaks": [
                {
                    "start": "15:00:00",
                    "start_timestamp": 2000003600.0,
                    "duration": 300,
                    "action": "snack",  # Single action (old format)
                    "comment": "Quick snack break"
                }
            ],
            "active": [
                {
                    "start": "14:00:00",
                    "start_timestamp": 2000000000.0,
                    "end": "15:00:00",
                    "end_timestamp": 2000003600.0,
                    "duration": 3600,
                    "project": "reading",  # Single project (old format)
                    "comment": "Reading a novel"
                }
            ],
            "idle_periods": [],
            "end_time": "15:05:00",
            "end_timestamp": 2000003900.0,
            "total_duration": 3900.0,
            "active_duration": 3600,
            "break_duration": 300,
            "session_comments": {
                "active_notes": "",
                "break_notes": "",
                "idle_notes": "",
                "session_notes": "Relaxing afternoon",
            },
        }
    }

def export_to_csv_manual(data, file_path):
    """Export data to CSV (simulating the actual export function)"""
    csv_rows = []

    for session_id, session_data in data.items():
        # Get session-level data
        sphere = session_data.get("sphere", "")
        date = session_data.get("date", "")
        start_time = session_data.get("start_time", "")
        end_time = session_data.get("end_time", "")
        total_duration = session_data.get("total_duration", 0)
        active_duration = session_data.get("active_duration", 0)
        break_duration = session_data.get("break_duration", 0)

        # Get session comments
        session_comments = session_data.get("session_comments", {})
        active_notes = session_comments.get("active_notes", "")
        break_notes = session_comments.get("break_notes", "")
        idle_notes = session_comments.get("idle_notes", "")
        session_notes = session_comments.get("session_notes", "")

        # Process active periods
        active_periods = session_data.get("active", [])
        breaks = session_data.get("breaks", [])
        idle_periods = session_data.get("idle_periods", [])

        # Process active periods
        if active_periods:
            for active in active_periods:
                # Extract primary and secondary project information
                primary_project = ""
                secondary_project = ""
                secondary_comment = ""
                secondary_percentage = ""
                
                if active.get("project"):
                    # Single project case
                    primary_project = active.get("project", "")
                else:
                    # Multiple projects case
                    for project_item in active.get("projects", []):
                        if project_item.get("project_primary", True):
                            primary_project = project_item.get("name", "")
                        else:
                            secondary_project = project_item.get("name", "")
                            secondary_comment = project_item.get("comment", "")
                            secondary_percentage = project_item.get("percentage", "")
                
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
                    "project": primary_project,
                    "secondary_project": secondary_project,
                    "secondary_comment": secondary_comment,
                    "secondary_percentage": secondary_percentage,
                    "activity_start": active.get("start", ""),
                    "activity_end": active.get("end", ""),
                    "activity_duration": active.get("duration", 0),
                    "activity_comment": active.get("comment", ""),
                    "break_action": "",
                    "secondary_action": "",
                    "active_notes": active_notes,
                    "break_notes": break_notes,
                    "idle_notes": idle_notes,
                    "session_notes": session_notes,
                }
                csv_rows.append(row)

        # Process breaks
        if breaks:
            for brk in breaks:
                # Extract primary and secondary action information
                primary_action = ""
                secondary_action = ""
                secondary_comment = ""
                secondary_percentage = ""
                
                if brk.get("action"):
                    # Single action case
                    primary_action = brk.get("action", "")
                else:
                    # Multiple actions case
                    for action_item in brk.get("actions", []):
                        if action_item.get("action_primary", True):
                            primary_action = action_item.get("name", "")
                        else:
                            secondary_action = action_item.get("name", "")
                            secondary_comment = action_item.get("comment", "")
                            secondary_percentage = action_item.get("percentage", "")
                
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
                    "secondary_project": "",
                    "secondary_comment": secondary_comment,
                    "secondary_percentage": secondary_percentage,
                    "activity_start": brk.get("start", ""),
                    "activity_end": "",
                    "activity_duration": brk.get("duration", 0),
                    "activity_comment": brk.get("comment", ""),
                    "break_action": primary_action,
                    "secondary_action": secondary_action,
                    "active_notes": active_notes,
                    "break_notes": break_notes,
                    "idle_notes": idle_notes,
                    "session_notes": session_notes,
                }
                csv_rows.append(row)

    # Write to CSV file
    if csv_rows:
        with open(file_path, "w", newline="", encoding="utf-8") as f:
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
                "secondary_project",
                "secondary_comment",
                "secondary_percentage",
                "activity_start",
                "activity_end",
                "activity_duration",
                "activity_comment",
                "break_action",
                "secondary_action",
                "active_notes",
                "break_notes",
                "idle_notes",
                "session_notes",
            ]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(csv_rows)
        
        return len(csv_rows)
    return 0

def main():
    """Run the manual test"""
    print("=== CSV Export with Secondary Project/Action - Manual Test ===\n")
    
    # Create sample data
    data = create_sample_data_with_secondary()
    
    # Export to temporary CSV
    output_file = os.path.join(os.path.dirname(__file__), "sample_export_with_secondary.csv")
    
    num_rows = export_to_csv_manual(data, output_file)
    
    print(f"✓ Exported {num_rows} rows to CSV")
    print(f"✓ File location: {output_file}\n")
    
    # Display the CSV content
    print("=== CSV Content ===\n")
    with open(output_file, "r", encoding="utf-8") as f:
        content = f.read()
        print(content)
    
    print("\n=== Verification ===\n")
    
    # Verify specific fields
    with open(output_file, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        
        # Check active row with secondary project
        active_row = [r for r in rows if r["type"] == "active" and r["secondary_project"]][0]
        print(f"✓ Active period with secondary project:")
        print(f"  - Primary project: {active_row['project']}")
        print(f"  - Secondary project: {active_row['secondary_project']}")
        print(f"  - Secondary comment: {active_row['secondary_comment']}")
        print(f"  - Secondary percentage: {active_row['secondary_percentage']}%\n")
        
        # Check break with secondary action
        break_row = [r for r in rows if r["type"] == "break" and r["secondary_action"]][0]
        print(f"✓ Break period with secondary action:")
        print(f"  - Primary action: {break_row['break_action']}")
        print(f"  - Secondary action: {break_row['secondary_action']}")
        print(f"  - Secondary comment: {break_row['secondary_comment']}")
        print(f"  - Secondary percentage: {break_row['secondary_percentage']}%\n")
        
        # Check backwards compatibility (single project/action)
        single_project_row = [r for r in rows if r["project"] == "reading"][0]
        print(f"✓ Backwards compatibility (single project):")
        print(f"  - Project: {single_project_row['project']}")
        print(f"  - Secondary project: '{single_project_row['secondary_project']}' (empty as expected)\n")
    
    print("=== Test Complete ===")
    print(f"\nCSV file saved at: {output_file}")
    print("You can open this file in Excel or any CSV viewer to inspect the output.")

if __name__ == "__main__":
    main()
