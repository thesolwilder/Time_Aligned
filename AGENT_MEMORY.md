# Agent Memory - What Works and What Doesn't

**Purpose**: This file tracks all approaches tried when making changes to the codebase, emphasizing what worked and documenting what failed to avoid repeating mistakes.

**Instructions for AI Agent**:

- Read this file BEFORE starting any code changes
- Update this file AFTER completing any changes
- Be specific about what worked and what didn't
- Include the WHY for both successes and failures

---

## ⚠️ CRITICAL RULES - NEVER VIOLATE THESE

### TDD Red Phase Rule (MANDATORY)

**When running tests in TDD red phase:**

1. Run tests and check output
2. **IF output shows ANY errors (E), STOP IMMEDIATELY**
3. **DO NOT proceed to implementation**
4. **Fix test scaffolding first** (add minimal stubs/attributes)
5. Re-run tests - should now show FAILURES (F), not ERRORS (E)
6. **ONLY after achieving red phase with FAILURES (no ERRORS), proceed to implementation**

**Example of test output analysis:**

```
FAILED (failures=2, errors=4)  ❌ STOP! Fix tests first
FAILED (failures=6, errors=0)  ✅ OK! Proceed to implementation
```

**Why this matters:**

- ERRORS (E) = Tests have bugs (AttributeError, ImportError, etc.)
- FAILURES (F) = Tests work but assertions fail (correct red phase)
- Source: DEVELOPMENT.md "CRITICAL: Red Phase Must Be a FAILURE, Not an ERROR"

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

### [2026-02-01] - Removed pytest from Project

**Change Requested**: Remove pytest-related files after discovering pytest is 35% slower than unittest for this codebase

**What Was Done**: ✅

- Removed `tests/run_tests_fast.py` (pytest runner)
- Removed `tests/conftest.py` (pytest configuration)
- Removed pytest and pytest-xdist from `requirements.txt`
- Updated documentation to reflect unittest-only approach

**Why This Works Better**:

- unittest is 35% faster (160s vs 215s for full suite)
- Tkinter GUI tests don't benefit from pytest features
- Simpler dependency chain
- Standard library (no external dependencies)

**Testing Workflow Going Forward**:

1. **During Development**: Run only affected tests
   - `python -m unittest tests.test_<module>` (5-30 seconds)
   - Example: `python -m unittest tests.test_analysis_timeline.TestAnalysisFrameProjectRadioButtons`

2. **Before Commits**: Run full suite with coverage
   - `python -W ignore -m coverage run tests/run_all_tests.py; python -m coverage report`

**Key Learning**: Don't assume pytest is always better - measure and verify for your specific codebase!

---

### [2026-02-01] - Analysis Frame Sphere Filter Radio Buttons (TDD Implementation)

**Change Requested**: Add radio buttons to analysis frame for filtering spheres by Active/All/Archived status

**User Requirements**:

- Put radio buttons on the same row as sphere dropdown (follow settings frame pattern)
- Timeline should default to active spheres/projects
- Allow selection of all spheres (both active and archived) or archived only
- Follow TDD workflow

**Approaches Tried**:

1. **TDD Approach: Write tests first, then implement** - ✅ **WORKED**
   - Details: Created comprehensive tests in `test_analysis_timeline.py` first
   - Tests covered: variable existence, radio button creation, active/all/archived filtering, default behavior
   - All tests failed initially (proper TDD red phase - FAILURES not ERRORS)
   - Implemented feature to make tests pass (green phase)
   - Result: All 25 tests in test_analysis_timeline.py pass

**What Worked**: ✅

- **Following TDD workflow strictly**: Write failing tests → implement → verify passing
- **Following existing patterns**: Used settings_frame.py as reference for radio button layout
- **StringVar for filter state**: `self.sphere_status_filter = tk.StringVar(value="active")`
- **Radio buttons on same row**: Created `radio_frame` within `filter_frame` for proper layout
- **Separation of concerns**:
  - `get_filtered_spheres()` - filters spheres based on status
  - `refresh_sphere_dropdown()` - updates dropdown and handles state changes
- **Default to active**: Initializing with `value="active"` ensures only active spheres show by default

**Implementation Details**:

Files modified:

- `src/analysis_frame.py`:
  - Added `self.sphere_status_filter = tk.StringVar(value="active")` in `__init__`
  - Created radio buttons frame with Active/All/Archived options
  - Added `get_filtered_spheres()` method to filter by active status
  - Added `refresh_sphere_dropdown()` method to update dropdown values
  - Radio buttons call `refresh_sphere_dropdown` on change

- `tests/test_analysis_timeline.py`:
  - Added `TestAnalysisFrameSphereRadioButtons` class with 6 tests
  - Tests verify filter variable, radio buttons, and filtering behavior

**Key Patterns**:

```python
# Radio buttons layout (following settings_frame pattern)
radio_frame = ttk.Frame(filter_frame)
radio_frame.pack(side=tk.LEFT, padx=5)

ttk.Radiobutton(
    radio_frame,
    text="Active",
    variable=self.sphere_status_filter,
    value="active",
    command=self.refresh_sphere_dropdown,
).pack(side=tk.LEFT, padx=2)

# Filtering logic
for sphere, data in self.tracker.settings.get("spheres", {}).items():
    is_active = data.get("active", True)

    if filter_status == "active" and is_active:
        spheres.append(sphere)
    elif filter_status == "archived" and not is_active:
        spheres.append(sphere)
    elif filter_status == "all":
        spheres.append(sphere)
```

**What Didn't Work**: ❌

- **Initial string escaping error**: Accidentally used `\"` instead of `"` in docstrings/strings
  - Fixed immediately when syntax error appeared
  - Lesson: Be careful with string formatting in replacements

- **⚠️ CRITICAL VIOLATION: Proceeded with ERRORS in TDD Red Phase** ❌❌❌
  - **MISTAKE**: First test run showed `FAILED (failures=2, errors=4)`
  - **WHAT I DID WRONG**: Continued to implementation despite 4 ERRORS
  - **WHAT I SHOULD HAVE DONE**: Fixed tests FIRST to produce FAILURES, not ERRORS
  - **Why it matters**: ERRORS mean the tests themselves have bugs (AttributeError, etc.)
  - **The rule**: Red phase MUST show FAILURES (F), NOT ERRORS (E)
  - **Violation of**: DEVELOPMENT.md "CRITICAL: Red Phase Must Be a FAILURE, Not an ERROR"

**How to Prevent This Violation in Future**:

**MANDATORY TDD RED PHASE CHECKLIST** (MUST follow EVERY time):

1. ✅ Write tests first
2. ✅ Run tests to get red phase
3. ⚠️ **STOP AND CHECK**: Are there ANY errors (E)?
   - **IF YES**: Do NOT proceed to implementation!
   - **Action**: Fix test scaffolding first
   - **Add minimal stubs**: e.g., `self.sphere_status_filter = None`
   - **Re-run tests**: Should now show FAILURES (F), not ERRORS (E)
4. ✅ Verify red phase shows ONLY failures (F), ZERO errors (E)
5. ✅ Only NOW proceed to implementation
6. ✅ Run tests for green phase

**Example of proper scaffolding**:

```python
# BAD: Tests immediately ERROR with AttributeError
# GOOD: Add stub first so tests FAIL with assertion errors
def __init__(self):
    self.sphere_status_filter = None  # Stub - makes tests FAIL not ERROR
```

**Key Learnings**:

1. **TDD workflow prevents errors**: Writing tests first ensures proper API design
2. **Follow existing patterns**: Settings frame radio button layout works perfectly for analysis frame
3. **⚠️ ERRORS vs FAILURES is CRITICAL**: MUST fix test scaffolding before implementing
4. **Default filtering improves UX**: Starting with "active" filter reduces clutter for most users
5. **Modular methods are testable**: Separate `get_filtered_spheres()` can be tested independently
6. **User correction is valuable**: Catching TDD violations helps build institutional knowledge

**Test Coverage**:

- 6 new tests for sphere filtering radio buttons
- All 25 tests in test_analysis_timeline.py passing
- No regressions in existing functionality
- ⚠️ BUT violated TDD red phase rule by proceeding with ERRORS

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

- Use unittest for all tests (pytest is slower for this codebase)
- Run only tests affected by code changes during development: `python -m unittest tests.test_<module>`
- Run full test suite before commits: `python -W ignore -m coverage run tests/run_all_tests.py; python -m coverage report`
- Test files mirror source structure in tests/ directory
- Coverage reports generated in htmlcov/

### Key Technologies

- Python with tkinter for UI
- Google Sheets integration
- Screenshot capture functionality
- System tray integration

---

### [2026-02-02] - Analysis Frame Project Filter Radio Buttons (TDD Implementation)

**Change Requested**: Add radio buttons to analysis frame for filtering projects by Active/All/Archived status (matching the sphere filter pattern)

**User Requirements**:

- Add radio buttons next to project dropdown in analysis frame
- Default to showing only active projects
- Allow selection of all projects or archived only
- Follow TDD workflow (write tests first)
- Fix current bug: analysis frame showing active projects when it should respect status filter

**Approaches Tried**:

1. **Proper TDD Red Phase Management** - ✅ **WORKED**
   - Details: Followed TDD red phase checklist from AGENT_MEMORY.md
   - First test run: `FAILED (failures=2, errors=4)` - STOPPED immediately ✅
   - Added minimal stub: `self.project_status_filter = tk.StringVar(value="active")`
   - Re-ran tests: `FAILED (failures=2, errors=0)` - Proper red phase achieved ✅
   - **Did NOT violate the TDD red phase rule this time!**
   - Proceeded to implementation only after achieving proper red phase

**What Worked**: ✅

- **Following TDD red phase checklist**: Stopped at ERRORS, added stub, verified FAILURES before implementing
- **Following existing patterns**: Used sphere filter implementation as reference
- **Matching UI pattern**: Radio buttons next to dropdown (consistent UX)
- **StringVar for filter state**: `self.project_status_filter = tk.StringVar(value="active")`
- **Separation of concerns**:
  - `update_project_filter()` - filters projects based on sphere AND status
  - `refresh_project_dropdown()` - updates dropdown when radio buttons change
- **Default to active**: Shows only active projects initially, reducing clutter

**Implementation Details**:

Files modified:

- `src/analysis_frame.py`:
  - Added `self.project_status_filter = tk.StringVar(value="active")` in `__init__` (stub first, then full implementation)
  - Created project radio buttons frame with Active/All/Archived options
  - Modified `update_project_filter()` to respect `project_status_filter`:
    ```python
    filter_status = self.project_status_filter.get()
    # ...
    if filter_status == "active" and is_active:
        projects.append(proj)
    elif filter_status == "archived" and not is_active:
        projects.append(proj)
    elif filter_status == "all":
        projects.append(proj)
    ```
  - Added `refresh_project_dropdown()` method to update dropdown on filter change

- `tests/test_analysis_timeline.py`:
  - Added `TestAnalysisFrameProjectRadioButtons` class with 6 tests
  - Tests verify: filter variable, radio buttons, active/all/archived filtering, default behavior
  - All tests follow proper TDD pattern

**Radio Buttons Layout Pattern** (consistent with sphere filters):

```python
# Radio buttons on same row as dropdown
project_radio_frame = ttk.Frame(filter_frame)
project_radio_frame.pack(side=tk.LEFT, padx=5)

ttk.Radiobutton(
    project_radio_frame,
    text="Active",
    variable=self.project_status_filter,
    value="active",
    command=self.refresh_project_dropdown,
).pack(side=tk.LEFT, padx=2)
# ... All and Archived buttons follow same pattern
```

**What Didn't Work**: ❌

- Nothing! Implementation went smoothly by following established patterns and TDD checklist

**Key Learnings**:

1. ✅ **TDD Red Phase Checklist Works**: Following the checklist prevented violations
2. **Consistency is key**: Using same pattern as sphere filters made implementation obvious
3. **Separation of concerns**: Having `update_project_filter()` and `refresh_project_dropdown()` as separate methods keeps code testable
4. **Default values matter**: Starting with "active" provides better UX for most users
5. **Test scaffolding is critical**: Adding minimal stub first ensures RED phase shows FAILURES not ERRORS
6. **Pattern reuse accelerates development**: Sphere filter implementation provided exact blueprint

**Test Coverage**:

- 6 new tests for project filtering radio buttons
- All 6 tests passing (GREEN phase)
- Tests cover: variable existence, radio button creation, active/all/archived filtering, default state
- No regressions in existing functionality

**TDD Workflow Summary** (PROPER execution this time):

1. ✅ Wrote 6 tests first
2. ✅ Ran tests → Got `FAILED (failures=2, errors=4)` → STOPPED
3. ✅ Added minimal stub to eliminate ERRORS
4. ✅ Re-ran tests → Got `FAILED (failures=2, errors=0)` → Proper RED phase
5. ✅ Implemented feature (radio buttons + filtering logic)
6. ✅ Ran tests → `Ran 6 tests in 5.121s OK` → GREEN phase achieved

**Success Metrics**:

- ✅ Followed TDD red phase rule correctly (no violations)
- ✅ All 6 new tests pass
- ✅ UI consistent with existing sphere filter pattern
- ✅ Bug fixed: Projects now filter correctly by status
- ✅ Code is clean, maintainable, and follows existing patterns

---

### [2026-02-02] - Analysis Frame Radio Button Layout Reorganization

**Change Requested**: Reorganize radio buttons in analysis frame to appear at the end of the row, after both dropdowns

**User Requirements**:

- Layout should be: `Sphere: [dropdown] Project: [dropdown] [radio buttons]`
- Previously: Radio buttons were between labels and dropdowns
- Follow settings frame pattern (but adapted for this use case)

**What Worked**: ✅

- **Simple layout reorganization**: Moved radio button frames to pack AFTER both dropdowns
- **No functional changes needed**: Tests all still pass (12/12)
- **Cleaner visual hierarchy**: Labels and dropdowns first, then filters

**Implementation Details**:

File modified: `src/analysis_frame.py`

**New layout order**:

1. Sphere label
2. Sphere dropdown
3. Project label
4. Project dropdown
5. Sphere radio buttons (Active/All/Archived)
6. Project radio buttons (Active/All/Archived)

All packed with `side=tk.LEFT` to create single horizontal row.

**Code Pattern**:

```python
# Labels and dropdowns first
ttk.Label(filter_frame, text="Sphere:").pack(side=tk.LEFT, padx=5)
self.sphere_filter = ttk.Combobox(...).pack(side=tk.LEFT, padx=5)
ttk.Label(filter_frame, text="Project:").pack(side=tk.LEFT, padx=5)
self.project_filter = ttk.Combobox(...).pack(side=tk.LEFT, padx=5)

# Radio buttons last
radio_frame = ttk.Frame(filter_frame)
radio_frame.pack(side=tk.LEFT, padx=5)
# ... sphere radio buttons

project_radio_frame = ttk.Frame(filter_frame)
project_radio_frame.pack(side=tk.LEFT, padx=5)
# ... project radio buttons
```

**What Didn't Work**: ❌

- Nothing! This was a straightforward layout change with no issues

**Key Learnings**:

1. **tkinter pack order matters**: Elements pack in the order they're called
2. **Layout changes don't affect functionality**: All 12 radio button tests still pass
3. **Visual hierarchy improves UX**: Grouping labels+dropdowns, then filters makes UI more intuitive
4. **Simple reorganization preferred**: No need to change frame structure or packing method

**Test Results**:

- ✅ All 12 radio button tests pass (6 sphere + 6 project)
- ✅ No regressions
- ✅ No functional changes required

**Success Metrics**:

- ✅ Layout matches user requirements
- ✅ All tests pass
- ✅ Clean, maintainable code
- ✅ Consistent with user's vision for the UI

---

### [2026-02-02] - Unified Status Filter for Analysis Frame (Single Set of Radio Buttons)

**Change Requested**: Consolidate two sets of radio buttons (sphere and project) into one unified set of 3 radio buttons (Active, All, Archived) that controls both dropdowns

**User Requirements**:

- Only ONE set of radio buttons (3 buttons total: Active, All, Archived)
- Active should be the default
- Radio buttons control BOTH sphere and project filtering simultaneously

**What Worked**: ✅

- **Unified StringVar**: Replaced `sphere_status_filter` and `project_status_filter` with single `status_filter`
- **Single set of radio buttons**: Created one radio frame instead of two
- **Unified refresh method**: Combined `refresh_sphere_dropdown()` and `refresh_project_dropdown()` into `refresh_dropdowns()`
- **Consistent filtering logic**: Both `get_filtered_spheres()` and `update_project_filter()` use same `status_filter.get()`
- **Test updates**: Automated replacement of old variable names in tests using PowerShell

**Implementation Details**:

Files modified:

- `src/analysis_frame.py`:
  - Replaced two StringVars with one: `self.status_filter = tk.StringVar(value="active")`
  - Created single radio button frame (removed `project_radio_frame`)
  - Replaced two refresh methods with unified `refresh_dropdowns()` method
  - Updated `get_filtered_spheres()` to use `self.status_filter.get()`
  - Updated `update_project_filter()` to use `self.status_filter.get()`

- `tests/test_analysis_timeline.py`:
  - Replaced all `sphere_status_filter` → `status_filter`
  - Replaced all `project_status_filter` → `status_filter`
  - Replaced all `refresh_sphere_dropdown()` → `refresh_dropdowns()`
  - Replaced all `refresh_project_dropdown()` → `refresh_dropdowns()`

**Code Pattern**:

```python
# Single unified filter variable
self.status_filter = tk.StringVar(value="active")

# Single set of radio buttons
radio_frame = ttk.Frame(filter_frame)
radio_frame.pack(side=tk.LEFT, padx=5)

ttk.Radiobutton(
    radio_frame,
    text="Active",
    variable=self.status_filter,  # Same variable for all filtering
    value="active",
    command=self.refresh_dropdowns,  # Unified refresh method
).pack(side=tk.LEFT, padx=2)
# ... All and Archived buttons

# Both filtering methods use same status_filter
def get_filtered_spheres(self):
    filter_status = self.status_filter.get()  # ✅

def update_project_filter(self, set_default=False):
    filter_status = self.status_filter.get()  # ✅
```

**What Didn't Work**: ❌

- Nothing! Implementation was straightforward once the pattern was clear

**Key Learnings**:

1. **Unified state is simpler**: One variable instead of two reduces complexity
2. **Consistent UX**: Both filters responding to same buttons is more intuitive
3. **PowerShell text replacement**: Efficient for bulk test updates (`-replace` operator)
4. **Tests catch breaking changes**: Tests failed immediately when variable names changed
5. **Proper naming matters**: `status_filter` is clearer than separate sphere/project filters

**Test Results**:

- ✅ All 12 tests pass (6 sphere + 6 project)
- ✅ Tests now verify unified `status_filter` instead of separate variables
- ✅ No regressions in filtering logic

**UI Layout** (final):

```
Sphere: [dropdown] Project: [dropdown] [Active] [All] [Archived]
```

**Success Metrics**:

- ✅ Only 3 radio buttons (not 6)
- ✅ Active is default
- ✅ Both dropdowns filter correctly
- ✅ All tests pass
- ✅ Cleaner, more intuitive UI

---
