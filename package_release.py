"""
package_release.py — Prepare and zip the dist/TimeAligned folder for distribution.

Usage:
    python package_release.py [--version X.Y.Z]

Steps:
  1. Removes runtime-generated files from dist/TimeAligned that should NOT ship:
       session data, settings, backups/, screenshots/ and Google credentials
  2. Zips the clean dist/TimeAligned/ folder into dist/TimeAligned-vX.Y.Z.zip
"""

import argparse
import shutil
import sys
import zipfile
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DIST_DIR = Path("dist") / "TimeAligned"

# Files / folders inside DIST_DIR that are created at runtime and must NOT ship
# (glob patterns, matched against DIST_DIR)
RUNTIME_ARTIFACTS = [
    "data.json",
    "data.json.unreadable_*",
    ".*.tmp",  # temp files left by an interrupted save (src/file_safety.py)
    "settings.json",
    "credentials.json",
    "token.pickle",
    "sheets_upload_log.json",
    "backups",
    "screenshots",
]


def clean_runtime_artifacts(dist_dir: Path) -> None:
    """Remove runtime-generated files / folders from the dist directory."""
    removed = []
    for pattern in RUNTIME_ARTIFACTS:
        for target in dist_dir.glob(pattern):
            if target.is_dir():
                shutil.rmtree(target)
            else:
                target.unlink()
            removed.append(target.name)

    if removed:
        print(f"  Removed runtime artifacts: {', '.join(removed)}")
    else:
        print("  No runtime artifacts found — folder is already clean.")


def zip_dist(dist_dir: Path, version: str) -> Path:
    """Zip the entire dist/TimeAligned folder into dist/TimeAligned-vX.Y.Z.zip."""
    zip_path = dist_dir.parent / f"TimeAligned-v{version}.zip"

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for file in sorted(dist_dir.rglob("*")):
            if file.is_file():
                arcname = file.relative_to(dist_dir.parent)
                zf.write(file, arcname)

    size_mb = zip_path.stat().st_size / (1024 * 1024)
    print(f"  Created: {zip_path}  ({size_mb:.1f} MB)")
    return zip_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Package TimeAligned for release.")
    parser.add_argument(
        "--version",
        default="0.1.0",
        help="Version string to embed in the zip filename (default: 0.1.0)",
    )
    args = parser.parse_args()

    if not DIST_DIR.exists():
        print(
            f"ERROR: {DIST_DIR} does not exist. Run 'pyinstaller time_tracker.spec' first."
        )
        sys.exit(1)

    print(f"\n=== Packaging TimeAligned v{args.version} ===\n")

    print("Step 1 — Cleaning runtime artifacts …")
    clean_runtime_artifacts(DIST_DIR)

    print("\nStep 2 — Zipping dist/TimeAligned …")
    zip_path = zip_dist(DIST_DIR, args.version)

    print(f"\n[OK] Release package ready: {zip_path}\n")


if __name__ == "__main__":
    main()
