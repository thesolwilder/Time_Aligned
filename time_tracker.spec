# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec file for Time Aligned — --onedir distribution
#
# Build command:
#   pyinstaller time_tracker.spec
#
# Output:
#   dist/TimeAligned/TimeAligned.exe  (plus support files in same folder)
#
# To install PyInstaller if needed:
#   pip install pyinstaller

block_cipher = None

a = Analysis(
    ["time_tracker.py"],
    pathex=[],
    binaries=[],
    datas=[
        # Bundle src/ package (Python modules are not auto-detected as data)
        ("src/", "src/"),
        # Bundle assets/ (icon and future resources)
        ("assets/", "assets/"),
    ],
    hiddenimports=[
        # pystray backend — Windows uses win32 backend
        "pystray._win32",
        # pynput backends — Windows
        "pynput.mouse._win32",
        "pynput.keyboard._win32",
        # Pillow — tkinter integration sometimes missed by analysis
        "PIL._tkinter_finder",
        # Google API stack — discovery-based imports missed by static analysis
        "google.auth.transport.requests",
        "google.oauth2.credentials",
        "google_auth_oauthlib.flow",
        "googleapiclient.discovery",
        "googleapiclient.errors",
        # pywin32 — Windows system tray and shell integration
        "win32api",
        "win32con",
        "win32gui",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Note: unittest must NOT be excluded — googleapiclient.discovery imports it at runtime
        "pytest",
        "coverage",
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="TimeAligned",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # No console window — GUI app only
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon="assets/icon.ico",
    # Embeds Windows version info (ProductName = "Time Aligned", FileDescription, etc.)
    # Visible in Task Manager → Details and File → Properties → Details.
    version="version_info.txt",
)

# COLLECT produces the --onedir output folder: dist/TimeAligned/
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="TimeAligned",
)
