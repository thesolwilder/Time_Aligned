"""
Verification script to check if Google Sheets dependencies are installed
Run this after: pip install -r requirements.txt
"""


def check_google_dependencies():
    """Check if all Google API dependencies are installed"""
    dependencies = [
        ("google.auth", "google-auth"),
        ("google_auth_oauthlib", "google-auth-oauthlib"),
        ("google.auth.transport", "google-auth-httplib2"),
        ("googleapiclient", "google-api-python-client"),
    ]

    missing = []
    installed = []

    for module, package in dependencies:
        try:
            __import__(module)
            installed.append(package)
            print(f"✓ {package} is installed")
        except ImportError:
            missing.append(package)
            print(f"✗ {package} is NOT installed")

    print("\n" + "=" * 50)
    if missing:
        print(f"\nMissing {len(missing)} package(s):")
        for pkg in missing:
            print(f"  - {pkg}")
        print(f"\nTo install missing packages, run:")
        print(f"  pip install {' '.join(missing)}")
        print("\nOr install all requirements:")
        print("  pip install -r requirements.txt")
        return False
    else:
        print("\n✓ All Google Sheets dependencies are installed!")
        print("You can now configure Google Sheets integration in Settings.")
        return True


if __name__ == "__main__":
    print("Checking Google Sheets Integration Dependencies...")
    print("=" * 50 + "\n")

    success = check_google_dependencies()

    if success:
        print("\n" + "=" * 50)
        print("Next steps:")
        print("1. Follow GOOGLE_SHEETS_SETUP.md to get credentials")
        print("2. Configure in Settings > Google Sheets Integration")
        print("3. Test connection and start tracking!")
