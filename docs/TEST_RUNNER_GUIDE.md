# Test Runner Quick Reference

## ❌ IMPORTANT: pytest is NOT faster for this codebase

**TESTED AND VERIFIED:**

- **unittest (run_all_tests.py)**: 160 seconds (2.7 min) ✅
- **pytest (run_tests_fast.py)**: 215 seconds (3.6 min) ❌ **35% SLOWER!**

**Why pytest doesn't help:**

- Tkinter GUI tests don't benefit from pytest optimizations
- pytest has MORE overhead for test discovery and collection
- Parallel execution (`-n 4`) causes Tkinter threading conflicts
- The bottleneck is `time.sleep()` and GUI operations, not the framework

---

## How to Run Tests

### Full Test Suite (Before Commits)

**Location**: `tests/run_all_tests.py`  
**Speed**: ~2.7 minutes (160 seconds) - **This is reasonable for 362 GUI tests**  
**Engine**: Python unittest

```powershell
# Run all tests
python tests/run_all_tests.py

# With coverage (as DEVELOPMENT.md requires)
python -W ignore -m coverage run tests/run_all_tests.py
python -m coverage report
```

**Use when**:

- Before committing changes
- Before pushing to main branch
- Following DEVELOPMENT.md directive for full test suite

---

### Specific Tests (During Development - RECOMMENDED ✅)

**Speed**: ~5-30 seconds  
**Engine**: Python unittest

```powershell
# One module (fastest way to test your changes)
python -m unittest tests.test_csv_export

# One test class (even faster)
python -m unittest tests.test_csv_export.TestCSVExportButton

# One specific test (fastest - 1-3 seconds)
python -m unittest tests.test_csv_export.TestCSVExportButton.test_button_exists
```

**Use when**:

- Actively developing a feature
- Debugging a specific test
- Want fast feedback during coding (**This is the real optimization!**)

---

## Recommended Workflow

```powershell
# 1. During active development (every few changes)
python -m unittest tests.test_myfeature  # ~5-30 seconds

# 2. Before committing (test affected modules)
python -m unittest tests.test_myfeature tests.test_related  # ~30-60s

# 3. Before pushing (full suite as per DEVELOPMENT.md)
python tests/run_all_tests.py  # ~2.7 minutes
# OR with coverage:
python -W ignore -m coverage run tests/run_all_tests.py
python -m coverage report
```

## Quick Command Reference

| Task                    | Command                                                   | Time    |
| ----------------------- | --------------------------------------------------------- | ------- |
| **Fastest feedback** ✅ | `python -m unittest tests.test_X`                         | ~5-30s  |
| Specific class          | `python -m unittest tests.test_X.TestClass`               | ~2-10s  |
| Single test             | `python -m unittest tests.test_X.TestClass.test_method`   | ~1-3s   |
| **Full suite**          | `python tests/run_all_tests.py`                           | ~2.7min |
| With coverage           | `python -W ignore -m coverage run tests/run_all_tests.py` | ~2.7min |

## Reality Check

**2.7 minutes is REASONABLE** for 362 comprehensive GUI tests. The bottleneck is:

- 100+ `time.sleep()` calls in tests
- Tkinter window creation and GUI operations
- Actual test logic, not the framework

**Best practice**: Don't run the full suite every time during development. Run specific tests for what you're working on, then run the full suite before commits.

## Files in This Project

- ✅ **`tests/run_all_tests.py`** - Use this (standard unittest runner)
- ❌ **`tests/run_tests_fast.py`** - Don't use (pytest wrapper, actually slower)
- ❌ **`tests/conftest.py`** - Not needed (pytest configuration)

These pytest-related files can be removed if desired, as they don't provide the expected performance benefit.
