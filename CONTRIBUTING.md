# Contributing to Time Aligned

Thank you for your interest in contributing! This document outlines how to get started.

## Getting Started

```powershell
git clone https://github.com/thesolwilder/Time_Aligned.git
cd Time_Aligned
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
pip install -r requirements-dev.txt
python time_tracker.py
```

## Running the Tests

```powershell
python tests/run_all_tests.py
```

To run with coverage:

```powershell
python -W ignore -m coverage run tests/run_all_tests.py
python -m coverage report
```

The one test that signs in to the real Google API is skipped unless you set `RUN_REAL_GOOGLE_API_TESTS=1`.

The test suite has **83% coverage** across the core application. All contributions must include appropriate tests.

## Development Standards

This project follows **Test-Driven Development (TDD)**:

1. Import test → 2. Unit tests → 3. Integration tests → 4. E2E tests

See [DEVELOPMENT.md](DEVELOPMENT.md) for full coding standards, patterns, and testing procedures.

## Submitting Changes

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature-name`
3. Write tests first, then implementation
4. Ensure all tests pass: `python tests/run_all_tests.py`
5. Commit with a clear message: `git commit -m "feat: describe your change"`
6. Open a pull request against `main`

## Reporting Issues

Open a [GitHub Issue](https://github.com/thesolwilder/Time_Aligned/issues) with:

- A clear description of the problem
- Steps to reproduce
- Expected vs actual behaviour
- Your Windows version

## License

By contributing, you agree that your contributions will be licensed under the same
[CC BY-NC 4.0](LICENSE) license as the project.
