"""
Crash-safe file helpers for the app's JSON files.

Rewriting a file in place with open(path, "w") empties it before writing, so a
crash or full disk mid-write loses everything in it. That is how data.json was
left as null bytes on May 27, 2026. These helpers write atomically, keep a copy
of a data file that cannot be read before anything replaces it, and keep a
rotating daily backup of data.json.
"""

import json
import os
import shutil
import tempfile
from datetime import date, datetime

DAILY_BACKUP_MARKER = ".daily_"
UNREADABLE_COPY_MARKER = ".unreadable_"


def write_json_atomically(file_path, data):
    """Write data as JSON so file_path always holds either the old or new content.

    The JSON goes to a temp file in the same folder, is flushed to disk, then
    replaces file_path in one step with os.replace. If anything fails, the
    existing file is untouched and the temp file is removed.

    Args:
        file_path: JSON file to write.
        data: JSON-serializable data.

    Raises:
        OSError, TypeError, ValueError: If the data cannot be written. The
            existing file is unchanged.
    """
    folder = os.path.dirname(os.path.abspath(file_path))
    file_descriptor, temp_path = tempfile.mkstemp(
        dir=folder, prefix=f".{os.path.basename(file_path)}.", suffix=".tmp"
    )
    try:
        with os.fdopen(file_descriptor, "w") as temp_file:
            json.dump(data, temp_file, indent=2)
            temp_file.flush()
            os.fsync(temp_file.fileno())
        os.replace(temp_path, file_path)
    except Exception:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise


def preserve_unreadable_file(file_path):
    """Copy a file that could not be read to a timestamped file beside it.

    Called before the file is replaced, so a corrupted data.json is kept for
    recovery instead of being silently overwritten.

    Args:
        file_path: The unreadable file.

    Returns:
        str: Path of the copy, e.g. data.json.unreadable_20261008_142500.

    Raises:
        OSError: If the copy cannot be made. Callers must then leave the
            original in place.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    preserved_path = f"{file_path}{UNREADABLE_COPY_MARKER}{timestamp}"
    shutil.copy2(file_path, preserved_path)
    return preserved_path


def create_daily_backup(data_file, data, backup_folder, retention_count, today=None):
    """Write today's backup of data if there is none yet, then prune old ones.

    Call right after data was saved successfully, so the backup holds
    known-good data. Only the first call each day writes; later calls that day
    return None. Only this data file's daily backups are pruned. Other files in
    backup_folder, such as pre-deletion backups, are never touched.

    Args:
        data_file: Path of the live data file; its name prefixes the backups.
        data: The data that was just saved.
        backup_folder: Folder for the backups (created if missing).
        retention_count: Number of daily backups to keep.
        today: Date stamped on the backup (defaults to today).

    Returns:
        str | None: Path of the backup written, or None if today's exists.

    Raises:
        OSError: If the backup cannot be written or old ones cannot be removed.
    """
    backup_prefix = os.path.basename(data_file) + DAILY_BACKUP_MARKER
    backup_date = today or date.today()
    backup_path = os.path.join(backup_folder, f"{backup_prefix}{backup_date:%Y%m%d}")
    if os.path.exists(backup_path):
        return None

    os.makedirs(backup_folder, exist_ok=True)
    write_json_atomically(backup_path, data)
    _prune_daily_backups(backup_folder, backup_prefix, retention_count)
    return backup_path


def _prune_daily_backups(backup_folder, backup_prefix, retention_count):
    """Delete the oldest daily backups so at most retention_count remain."""
    daily_backups = sorted(
        name for name in os.listdir(backup_folder) if name.startswith(backup_prefix)
    )
    excess_count = max(len(daily_backups) - retention_count, 0)
    for name in daily_backups[:excess_count]:
        os.remove(os.path.join(backup_folder, name))
