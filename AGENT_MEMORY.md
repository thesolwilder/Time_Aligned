# Agent Memory - What Works and What Doesn't

**Purpose**: This file tracks all approaches tried when making changes to the codebase, emphasizing what worked and documenting what failed to avoid repeating mistakes.

**Instructions for AI Agent**:

- Read this file BEFORE starting any code changes
- Update this file AFTER completing any changes
- Be specific about what worked and what didn't
- Include the WHY for both successes and failures

---

## Memory Log

### [2026-01-31] - Agent Memory System Initialization

**Change Requested**: Create agent memory system to track what works/doesn't work

**What Worked**:

- Created AGENT_MEMORY.md as a persistent learning file
- Added clear structure with date-stamped entries
- Updated DEVELOPMENT.md with prominent directives to read and update this file

**Key Learning**:

- Maintaining persistent memory across AI sessions helps avoid repeating failed approaches
- Structured documentation of successes and failures improves development efficiency

---

## Template for New Entries

```markdown
### [YYYY-MM-DD] - Brief Description

**Change Requested**: What was the user asking for?

**Approaches Tried**:

1. First approach - [WORKED/FAILED]
   - Details: ...
   - Why: ...
2. Second approach - [WORKED/FAILED]
   - Details: ...
   - Why: ...

**What Worked**: ✅

- Specific solution that succeeded
- Why it worked
- Key implementation details

**What Didn't Work**: ❌

- Approach that failed
- Why it failed
- What to avoid in the future

**Key Learnings**:

- Important insights
- Patterns to remember
- Best practices discovered
```

---

### [2026-02-01] - Test Suite Performance Optimization Investigation

**Change Requested**: Speed up test suite execution time (currently ~3 minutes)

**Approaches Tried**:

1. **pytest with parallel execution** - ❌ **FAILED**
   - Details: Installed pytest and pytest-xdist, tried running tests in parallel (`-n 4`)
   - Why it failed: Tkinter GUI tests have threading conflicts when run in parallel
   - Result: Tests crashed with "invalid command name" and "RuntimeError: main thread is not in main loop"

2. **pytest sequential execution** - ❌ **FAILED (SLOWER!)**
   - Details: Ran pytest without parallelization to avoid threading issues
   - Measured results:
     - unittest (run_all_tests.py): 160 seconds (2.7 min) ✅
     - pytest (run_tests_fast.py): 215 seconds (3.6 min) ❌
   - Why it failed: pytest has MORE overhead for test discovery/collection, doesn't optimize GUI tests
   - **35% SLOWER than unittest!**

**What Worked**: ✅

- **Running specific test modules during development**
  - `python -m unittest tests.test_myfeature` (~5-30 seconds)
  - This is the industry-standard approach for large test suites
  - Full suite (160s) is only needed before commits, not during active development

**What Didn't Work**: ❌

- pytest optimization: Actually slower for Tkinter GUI tests
- Parallel execution: Causes threading conflicts with Tkinter
- Trying to optimize the test framework: The bottleneck is the tests themselves (100+ `time.sleep()` calls, GUI operations)

**Key Learnings**:

1. **2.7 minutes is REASONABLE** for 362 comprehensive GUI tests
2. **The framework is NOT the bottleneck** - unittest is already well-optimized
3. **pytest doesn't help all codebases** - GUI tests with Tkinter don't benefit from pytest
4. **Best practice: Run specific tests during development** - Full suite only before commits
5. **Don't optimize the wrong thing** - The real bottleneck is `time.sleep()` calls and GUI operations, not the test runner

**Files Updated**:

- `docs/TEST_OPTIMIZATION_GUIDE.md` - Corrected to show pytest is slower
- `docs/TEST_RUNNER_GUIDE.md` - Replaced with accurate performance data
- `requirements.txt` - Added pytest packages (can be removed)
- `tests/run_tests_fast.py` - Created but doesn't help (can be removed)
- `tests/conftest.py` - Created for pytest imports (can be removed)

**Recommendation**: Remove pytest-related files and focus on running specific tests during development rather than trying to speed up the full suite.

---

## Common Patterns That Work

### Testing

- Always run tests after changes to verify functionality
- Use TDD when implementing new features
- Check test files match production code structure

### File Operations

- Use absolute paths for file operations on Windows
- Multi-replace operations are more efficient than sequential edits
- Read sufficient context before making changes

### Dependencies

- Check requirements.txt for installed packages before suggesting new ones
- Verify imports in affected files after structural changes

---

## Known Issues & Solutions

### Issue: [Describe recurring problem]

- **Failed Approaches**: What didn't work
- **Working Solution**: What actually works
- **Why**: Explanation of root cause

---

## Codebase-Specific Knowledge

### Project Structure

- Main entry point: time_tracker.py
- Tests directory: tests/
- Source code: src/
- Documentation: docs/
- Configuration: settings.json, credentials.json

### Testing Conventions

- Use pytest for all tests
- Test files mirror source structure in tests/ directory
- Coverage reports generated in htmlcov/

### Key Technologies

- Python with tkinter for UI
- Google Sheets integration
- Screenshot capture functionality
- System tray integration

---
