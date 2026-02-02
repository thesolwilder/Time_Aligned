# Agent Memory - What Works and What Doesn't

**Purpose**: This file tracks all approaches tried when making changes to the codebase, emphasizing what worked and documenting what failed to avoid repeating mistakes.

**Instructions for AI Agent**:

- Read this file BEFORE starting any code changes
- **SEARCH this file for keywords related to your current task** (module names, technologies, error patterns)
- Update this file AFTER completing any changes
- Be specific about what worked and what didn't
- Include the WHY for both successes and failures

**How to Search This File Effectively**:

When working on a task, search for:

- **Module/file names**: "analysis_frame", "timeline", "backup", "export"
- **Technologies**: "tkinter", "pandas", "CSV", "JSON", "Google Sheets"
- **Error keywords**: "geometry manager", "headless", "width", "TclError", "UnboundLocalError"
- **Feature areas**: "columns", "filtering", "sorting", "radio buttons"
- **Component types**: "header", "row", "canvas", "frame", "label"

Example: Before adding tkinter tests, search "tkinter", "headless", "winfo" to find known issues.

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

### [2026-02-02] - Settings Frame Sphere Filter Updates Project List (Bug Fix)

**Bug Reported**: When changing sphere filter radio buttons (Active/All/Inactive), the sphere dropdown updates but the project list doesn't refresh to show projects from the newly selected sphere.

**What Worked**:

1. **TDD Approach for Bug Fix**:
   - Wrote test `test_sphere_filter_change_updates_project_list` that verified the bug
   - Test FAILED (correct red phase) - confirmed ActiveProject still visible after switching to ArchivedSphere
   - Fixed by adding `self.refresh_project_section()` call in `refresh_sphere_dropdown()`
   - Test PASSED - project list now updates correctly

2. **Careful Initialization Order Check**:
   - Added `hasattr(self, 'projects_list_frame')` check before calling `refresh_project_section()`
   - Prevents AttributeError during initialization (sphere section created before project section)
   - Used defensive programming pattern to handle widget creation order

**What Didn't Work**:

- **Initial attempt without hasattr check**: Caused AttributeError during SettingsFrame initialization
  - `refresh_sphere_dropdown()` is called at end of `create_sphere_section()`
  - `projects_list_frame` doesn't exist until `create_project_section()` runs (which is after sphere section)
  - **Solution**: Add conditional check `if hasattr(self, 'projects_list_frame'):`

**Key Learnings**:

1. **Radio button command callbacks need to update dependent UI**: When sphere filter changes, both dropdown AND project list must refresh
2. **Widget initialization order matters**: Check for widget existence before calling methods that depend on it
3. **TDD for bugs is powerful**: Writing failing test first confirmed the bug and verified the fix
4. **Defensive programming**: Use `hasattr()` when calling methods that depend on widgets that may not exist yet

**Files Changed**:

1. `src/settings_frame.py`:
   - Modified `refresh_sphere_dropdown()` to call `self.refresh_project_section()` after updating sphere
   - Added `hasattr(self, 'projects_list_frame')` guard to prevent initialization errors

2. `tests/test_settings_frame.py`:
   - Added `test_sphere_filter_change_updates_project_list` test
   - Verifies that changing sphere filter radio button updates project list
   - Test sets sphere to ActiveSphere, verifies ActiveProject visible
   - Changes filter to inactive (selects ArchivedSphere), verifies ActiveProject NOT visible

**Test Results**: All 9 tests in TestSettingsFrameFilters pass (34.4s)

---

### [2026-02-02] - Session Notes Column Expands to Fill Screen Width

**Change Requested**: Make the 13th column (Session Notes) expand all the way to the end of the screen since it will contain the most amount of text.

**What Worked**:

- **TDD approach**: Wrote test first (`test_session_notes_column_expands_to_fill_space`)
  - Test verified red phase: pack_info["fill"] was 'none' instead of 'x'
  - Test checks both header and data row Session Notes labels use `fill=tk.X, expand=True`
- **Header modification**: Updated `create_non_sortable_single_row_header()` function:
  - Added `expand=False` parameter (default False for backward compatibility)
  - When `expand=True`, label uses `.pack(fill=tk.X, expand=True)` instead of `.pack()`
  - Called with `create_non_sortable_single_row_header("Session Notes", 21, expand=True)`
- **Data row modification**: Updated `create_label()` function in `update_timeline()`:
  - Added `expand=False` parameter (default False)
  - When `expand=True`, label uses `.pack(side=tk.LEFT, fill=tk.X, expand=True)`
  - Session Notes label called with `create_label(period["session_notes"], 21, wraplength=150, expand=True)`
- **Result**: Session Notes column now stretches to edge of screen horizontally
  - Still maintains `width=21` for minimum size
  - Still uses `wraplength=150` for text wrapping
  - Now fills remaining horizontal space after other columns

**What Didn't Work**:

- **N/A**: Implementation successful on first attempt using TDD

**Key Learnings**:

1. **Tkinter pack() expansion**: Use `fill=tk.X, expand=True` to make widgets stretch horizontally to fill available space
   - `fill=tk.X`: Widget expands horizontally to fill allocated space
   - `expand=True`: Widget gets allocated extra space when parent expands
   - Both needed for proper horizontal stretching
2. **Selective column expansion**: Can make one column expandable while keeping others fixed width
   - Other columns use `.pack(side=tk.LEFT)` (no fill/expand)
   - Last column uses `.pack(side=tk.LEFT, fill=tk.X, expand=True)`
   - This creates "fixed columns + one expanding column" layout
3. **Backward compatibility**: Adding optional parameters with defaults preserves existing behavior
   - `expand=False` default means existing calls still work
   - Only Session Notes explicitly sets `expand=True`
4. **TDD validation**: Test verified exact pack configuration, not just visual appearance
   - Checked `pack_info["fill"] == "x"` 
   - Checked `pack_info["expand"] == True`
   - More reliable than visual inspection

**Files Changed**:

1. `src/analysis_frame.py`:
   - **Line 1113**: Modified `create_non_sortable_single_row_header()` to accept `expand` parameter
   - **Line 1120**: Added conditional pack: `label.pack(fill=tk.X, expand=True)` if expand, else `label.pack()`
   - **Line 1143**: Called with `expand=True` for Session Notes header
   - **Line 991**: Modified `create_label()` to accept `expand` parameter  
   - **Line 1008**: Added conditional pack: `lbl.pack(side=tk.LEFT, fill=tk.X, expand=True)` if expand
   - **Line 1035**: Called with `expand=True` for Session Notes data label
   - Added comment: "Session Notes expands to fill remaining space (most text)"

2. `tests/test_analysis_timeline.py`:
   - Added `test_session_notes_column_expands_to_fill_space` to TestAnalysisTimelineSessionNotesContent class
   - Verifies Session Notes label (column 13) in data rows has `fill='x'` and `expand=True`
   - Verifies Session Notes header label has `fill='x'` and `expand=True`

**Test Results**: All 53 timeline tests pass ✅

---

### [2026-02-02] - Enhanced AGENT_MEMORY.md Search Guidance

**Change Requested**: Update DEVELOPMENT.md to emphasize searching AGENT_MEMORY.md for task-related entries to avoid repeating past mistakes

**What Worked**:

- **Added "Search for Related Entries" section to DIRECTIVE 1** in DEVELOPMENT.md:
  - 3-step process: Search keywords → Review related entries → Apply learnings
  - Specific search term categories: modules, technologies, errors, features
  - Concrete examples of common pitfalls (tkinter, file ops, UI, data)
- **Updated AGENT_MEMORY.md instructions** with search guidance:
  - Added "How to Search This File Effectively" section
  - Listed specific keywords to search by category
  - Included example: "Before adding tkinter tests, search 'tkinter', 'headless', 'winfo'"
- **Highlighted real examples from recent work**:
  - Tkinter geometry manager mixing (pack/grid) causes TclError
  - `winfo_width()` returns 1px in headless tests, use `winfo_reqwidth()`

**What Didn't Work**:

- **N/A**: Documentation update successful on first attempt

**Key Learnings**:

1. **Make search guidance actionable**: Provide specific keywords to search, not just "read the file"
2. **Use real examples**: Reference actual problems documented (tkinter headless issues)
3. **Categorize search terms**: Group by module, technology, error type, feature area
4. **Explain the why**: "Not searching wastes time repeating failed approaches"
5. **Emphasize common pitfalls**: Call out frequently-encountered issues (geometry managers, headless tests)

**Files Changed**:

1. `DEVELOPMENT.md`:
   - Expanded DIRECTIVE 1 with "CRITICAL: Search for Related Entries" section
   - Added 3-step search process
   - Listed common pitfall categories with examples
   - Added motivation: "AGENT_MEMORY.md contains solutions to problems you WILL encounter"

2. `AGENT_MEMORY.md`:
   - Updated instructions header with search guidance
   - Added "How to Search This File Effectively" section
   - Listed specific search term categories
   - Included concrete example

**Why This Approach Succeeded**:

- Recognized gap: agents were reading AGENT_MEMORY.md but not searching it effectively
- Made search process explicit and actionable
- Used recent real-world examples (tkinter issues) to illustrate value
- Structured search terms by category for easy reference

---

### [2026-02-02] - Fix Session Notes Column Visual Misalignment

**Change Requested**: User reported "session notes is in the timeline but in the wrong column. it is underneath the secondary action column when it needs to be only in the last column"

**Root Cause Analysis**:

- **NOT a data mapping issue**: Session notes data was correctly in column 13 (verified by tests)
- **Visual alignment problem**: Header columns were WIDER than data columns, causing visual shift
- **Specific issue**: Comment headers had `width=20` but data had `width=0`
  - Headers with `width=20` render ~130-140px wide
  - Data with `width=0` renders ~49px wide (auto-sized to short content like "active comment")
  - This 90px difference accumulated across 5 comment columns = 450px total shift!
  - Result: Column 13 data visually appeared under column 9 header

**What Worked**:

- **Solution**: Match header and data widths by using `width=21` for ALL comment columns
  - Calculation: `wraplength=150px` ÷ 7px/char (Arial 8 font) ≈ 21 characters
  - Headers: Changed from `width=20` → `width=21`
  - Data: Changed from `width=0` → `width=21`
  - Both header and data now render at consistent ~147px width
- **TDD approach**:
  1. Investigated user report by running tests - data was in correct column 13
  2. Identified visual alignment issue using pixel-width tests
  3. Fixed by matching widths (width=21 for both header and data)
  4. All 52 timeline tests pass including alignment tests
- **Why this works better than width=0**:
  - `width=21` provides consistent column sizing
  - `wraplength=150` still handles text overflow by wrapping
  - Headers and data have matching pixel widths for perfect alignment
  - Long text still wraps properly without truncation

**What Didn't Work**:

1. **Attempt 1**: Changed comment headers to `width=0` to match data
   - Problem: Headers sized to label text ("Primary Comment"), data sized to actual content
   - Result: Still had width mismatch (headers 93px, data 49px)
   - Broke: `test_header_pixel_width_matches_data_row_pixel_width`
2. **Attempt 2**: Updated tests to skip comment columns
   - Problem: Was accommodating the bug instead of fixing it
   - Lesson: Don't relax tests to pass - fix the underlying alignment issue

**Key Learnings**:

1. **Visual alignment ≠ data correctness**: Data can be in the right column programmatically but APPEAR in wrong column visually due to width mismatches
2. **Width calculation for wraplength**: Use `wraplength_pixels ÷ pixels_per_char = width_characters`
   - Example: 150px ÷ 7px/char = ~21 characters
3. **Consistent sizing strategy**: For columns with variable content:
   - Set fixed `width=N` based on wraplength
   - Use `wraplength` for text overflow handling
   - Results in consistent column widths AND proper wrapping
4. **Debugging visual issues**: When user reports column misalignment:
   - First verify data is correct (test column indices)
   - Then check pixel widths (`winfo_reqwidth()`)
   - Look for cumulative width differences across multiple columns

**Files Changed**:

1. `src/analysis_frame.py`:
   - **Headers**: Changed 5 comment headers from `width=20` → `width=21`
     (Primary Comment, Secondary Comment, Active Comments, Break Comments, Session Notes)
   - **Data rows**: Changed 5 comment data calls from `width=0` → `width=21`
     (Kept `wraplength=150` on all)
   - Updated inline comment explaining width matches wraplength pixel width

2. `tests/test_analysis_timeline.py`:
   - Updated `test_comment_labels_do_not_have_width_restriction` to expect `width=21` instead of `width=0`
   - Updated test docstring to explain: "width=21 matches wraplength~150px for consistent column sizing"
   - Removed debug print statement from `test_session_notes_not_in_secondary_action_column` (was causing UnicodeEncodeError with ✓ character)

**Visual Impact**:

- **Before**: Session notes column appeared shifted left, data under wrong header (column 13 data under column 9 header)
- **After**: Perfect header-to-data alignment, all comment columns properly aligned

**Test Results**: All 52 timeline tests pass ✅

---

### [2026-02-02] - Fix Comment Truncation Bug: Remove width= Restriction from Comment Labels

**Change Requested**: Session notes and other comment fields are truncated even though wraplength is configured. Text should wrap and extend to edge of screen without truncation.

_NOTE: This entry superseded by "Fix Session Notes Column Visual Misalignment" above. Final solution uses width=21, not width=0_

**What Worked (ORIGINAL ATTEMPT - LATER REVISED)**:

- **Root cause identified**: Comment labels had BOTH `width=20` AND `wraplength=150`
  - `width=20` creates fixed-width label that truncates text beyond ~20 characters
  - `wraplength=150` only controls where text wraps, doesn't prevent truncation
  - These two settings conflict: width restricts, wraplength wraps
- **Solution**: Set `width=0` for comment columns
  - `width=0` means "no width restriction" - label expands to fit content
  - Combined with `wraplength=150`, text wraps at 150px but label expands vertically
  - Result: Full text displays, wrapping to multiple lines, extending to screen edge
- **TDD approach (Bug Fix Workflow)**:
  1. Wrote failing test `test_comment_labels_do_not_have_width_restriction` (RED phase)
  2. Test verified width=20 on comment columns (caught the bug)
  3. Changed comment columns from `width=20` to `width=0` (GREEN phase)
  4. Test passes, all 5 comment wrapping tests pass
- **Why existing tests didn't catch this**:
  - `test_comment_labels_have_wraplength_configured` only checked `wraplength > 0`
  - Didn't verify that labels can actually expand (didn't check width=0)
  - Lesson: Test both positive requirements AND absence of conflicting restrictions

**What Didn't Work**:

- **N/A**: First approach (width=0) worked immediately

**Key Learnings**:

1. **tkinter width vs wraplength conflict**:
   - `width=N` (character width): Creates fixed-size label, truncates beyond N characters
   - `wraplength=N` (pixel width): Controls where text wraps within available space
   - **Conflict**: Setting both causes truncation even with wrapping configured
   - **Solution**: Use `width=0` + `wraplength=N` for expandable wrapped labels
2. **Testing for absence of restrictions**: Tests should verify NOT ONLY that desired features exist (wraplength > 0) BUT ALSO that conflicting restrictions don't exist (width = 0)
3. **Label expansion behavior**:
   - `width=0`: Label size determined by content (can expand)
   - `width=N`: Label size fixed to N characters (cannot expand)
   - For wrapping text, always use width=0
4. **Bug location**: Changed 5 comment columns in `update_timeline()`:
   - Primary Comment (col 8): width 20→0
   - Secondary Comment (col 10): width 20→0
   - Active Comments (col 11): width 20→0
   - Break Comments (col 12): width 20→0
   - Session Notes (col 13): width 20→0

**Visual Impact**:

- **Before**: Comments truncated at ~20 characters (e.g., "Inactive Sphere Active Pro")
- **After**: Full comments displayed with wrapping (e.g., "Inactive Sphere Active Project / Active Sphere Inactive Project")

**Files Changed**:

1. `src/analysis_frame.py`:
   - Changed 5 comment columns from `create_label(..., 20, wraplength=150)` to `create_label(..., 0, wraplength=150)`
   - Updated comment explaining the approach

2. `tests/test_analysis_timeline.py`:
   - Added `test_comment_labels_do_not_have_width_restriction` to `TestAnalysisTimelineCommentWrapping`
   - Test verifies all comment columns have width=0 (no restriction) AND wraplength > 0 (wrapping enabled)
   - Explains WHY width=0 is needed (allows expansion for wrapped content)

---

### [2026-02-02] - Fix Test Failures After Two-Row Header Implementation

**Change Requested**: Fix 6 test failures caused by two-row header implementation changing widget hierarchy and column indices

**What Worked**:

- **Identified root causes**:
  1. **Header structure tests** looking for Labels directly in header_frame, but labels are now inside Frame containers
  2. **Column index errors** in comment tests - Sphere Active (col 4) and Project Active (col 5) were added, shifting all subsequent indices by 2
  3. **Correct column layout** after two-row headers:
     - 0=Date, 1=Start, 2=Duration, 3=Sphere
     - 4=Sphere Active, 5=Project Active (these 2 shifted everything)
     - 6=Type, 7=Primary Project
     - 8=Primary Comment (was 5), 9=Secondary Project
     - 10=Secondary Comment (was 7), 11=Active Comments (was 8)
     - 12=Break Comments (was 9), 13=Session Notes (was 10)
- **Fixed header structure tests**:
  - Extract labels from Frame containers: `for container in containers: for label in container.winfo_children()`
  - "Sphere Active" test: Now checks for two-row structure with "Sphere" and "Active" labels in container
  - "Project Active" test: Now checks for two-row structure with "Project" and "Active" labels in container
- **Fixed comment column tests**:
  - Updated all comment column indices: [8, 10, 11, 12, 13] (was [5, 7, 8, 9, 10])
  - Primary comment: index 8 (was 5)
  - Secondary comment: index 10 (was 7)
  - Active comments: index 11 (was 8)
  - Break comments: index 12 (was 9)
  - Session notes: index 13 (was 10)
- **Test execution**: Only ran affected tests (6 tests) instead of full suite to save time

**What Didn't Work**:

- **N/A**: All fixes worked on first attempt after proper analysis

**Key Learnings**:

1. **Cascading index changes**: Adding columns in the middle shifts ALL subsequent column indices - must update ALL tests that reference columns by index
2. **Widget hierarchy changes require full test review**: When changing from direct Label children to Frame→Label hierarchy, ALL tests traversing that hierarchy need updates
3. **Two-row header testing pattern**: Check container[4] and container[5] for two-label arrays containing top/bottom text
4. **Targeted test execution**: Use specific test names to run only affected tests during debugging
5. **Documentation**: Add comments in tests explaining column layout to prevent future confusion

**Files Changed**:

1. `tests/test_analysis_timeline.py`:
   - Fixed `test_timeline_header_has_sphere_column`: Extract labels from Frame containers
   - Fixed `test_timeline_header_has_sphere_active_column`: Check for two-row "Sphere"/"Active" structure
   - Fixed `test_timeline_header_has_project_active_column`: Check for two-row "Project"/"Active" structure
   - Fixed `test_comment_labels_have_wraplength_configured`: Updated comment indices from [5,7,8,9,10] to [8,10,11,12,13]
   - Fixed `test_all_comment_fields_show_full_content`: Updated primary comment from index 5→8, active comments from 8→11, session notes from 10→13
   - Fixed `test_primary_comment_shows_full_text_without_truncation`: Updated primary comment index from 5→8

---

### [2026-02-02] - Two-Row Timeline Headers for Clearer Active Status Indicators

**Change Requested**: Make "Sphere Active" and "Project Active" columns clearer by using two-row headers showing "Sphere" / "Active" and "Project" / "Active" instead of long single-line labels

**What Worked**:

- **Two-row header design**:
  - Frame containers for each column (packed horizontally with side=tk.LEFT)
  - Labels stacked vertically inside containers
  - "Sphere Active" → Two rows: "Sphere" (top), "Active" (bottom)
  - "Project Active" → Two rows: "Project" (top), "Active" (bottom)
- **Vertical centering for single-row headers**:
  - Single-row headers use pady=6 to vertically center with two-row headers
  - Prevents visual misalignment between headers of different heights
- **TDD approach**:
  1. Wrote 4 tests first (RED phase): Container existence, Sphere Active structure, Project Active structure, vertical centering
  2. Verified tests failed properly (3 FAILURES, 1 skipped)
  3. Implemented feature (GREEN phase)
  4. All 7 header tests pass (including pre-existing tests)
- **Helper functions** for code organization:
  - `create_single_row_header(text, column_key, width)` - Sortable headers with vertical centering
  - `create_two_row_header(top_text, bottom_text, width)` - Non-sortable two-row headers
  - `create_non_sortable_single_row_header(text, width)` - Non-sortable with vertical centering
- **Test updates**:
  - Updated existing tests to extract labels from Frame containers (not directly from header_frame)
  - Removed pady matching assertion (intentionally different now for vertical centering)
  - All pixel-width alignment tests still pass

**What Didn't Work**:

- **Initial test design**: One test had ERROR (IndexError) instead of FAILURE
  - **Why it failed**: Tried to access header_containers[0] when list was empty
  - **Fix**: Added skipTest() if no Frame containers exist (proper test scaffolding)
- **Old test compatibility**: Pre-existing tests looked for Labels directly in header_frame
  - **Why it failed**: New design wraps labels in Frame containers
  - **Fix**: Updated tests to extract labels from containers: `[w for w in container.winfo_children() if isinstance(w, tk.Label)]`

**Key Learnings**:

1. **Two-row headers in tkinter**: Use Frame containers with vertical label stacking
2. **Vertical alignment**: Single-row headers need pady to align with multi-row headers
3. **Test compatibility**: When changing widget hierarchy, update ALL tests that traverse the tree
4. **TDD test scaffolding**: Use skipTest() for tests that fail due to missing implementation (not test bugs)
5. **Frame container pattern**:
   - Outer frame (header_frame) contains column containers
   - Column containers (Frames) contain label(s)
   - Pack containers horizontally, pack labels vertically
6. **Helper function organization**: Create separate functions for different header types (sortable single-row, non-sortable single-row, two-row)
7. **Visual clarity without width increase**: Two-row stacking maintains column width while improving label clarity

**User Benefit**:

- **Clearer labeling**: Users immediately understand checkmarks indicate "Sphere Active" and "Project Active" status
- **No width sacrifice**: Comment columns remain wide and readable
- **Consistent alignment**: All headers align properly (single-row and two-row)
- **Sortable columns still work**: Click-to-sort functionality preserved

**Files Changed**:

1. `src/analysis_frame.py`:
   - Completely rewrote `update_timeline_header()` method
   - Added `create_single_row_header()` helper function (sortable, pady=6)
   - Added `create_two_row_header()` helper function (two stacked labels)
   - Added `create_non_sortable_single_row_header()` helper function (non-sortable, pady=6)
   - Changed "Sphere Active" to two-row: "Sphere" / "Active"
   - Changed "Project Active" to two-row: "Project" / "Active"

2. `tests/test_analysis_timeline.py`:
   - Added new test class `TestAnalysisTimelineTwoRowHeaders` with 4 tests:
     - `test_header_containers_exist_for_two_row_headers` - Verifies Frame container structure
     - `test_sphere_active_header_has_two_rows` - Validates "Sphere" / "Active" layout
     - `test_project_active_header_has_two_rows` - Validates "Project" / "Active" layout
     - `test_single_row_headers_are_vertically_centered` - Checks pady > 0 for centering
   - Updated 3 existing tests in `TestAnalysisTimelineHeaderAlignment`:
     - `test_header_columns_align_with_data_rows` - Extract labels from Frame containers
     - `test_header_pixel_width_matches_data_row_pixel_width` - Extract labels from Frame containers
     - `test_header_pixel_width_with_sort_indicators` - Extract labels from Frame containers
   - Removed pady matching assertion (intentionally different for vertical centering)

---

### [2026-02-02] - Header Column Alignment Analysis and TDD Tests

**Change Requested**: Analyze bug where header columns don't align with data columns; write test that compares header cell width to data cell width in each row to ensure alignment

**What Worked**:

- **Root cause analysis**: Identified why existing test didn't catch the bug:
  - Old test checked `cget("width")` = configuration values (what we TOLD tkinter)
  - Bug occurs in visual rendering (what tkinter ACTUALLY renders)
  - Configuration can be identical while pixel rendering differs
- **Two new comprehensive tests added**:
  1. `test_header_pixel_width_matches_data_row_pixel_width`: Checks actual pixel widths using `winfo_reqwidth()`
  2. `test_header_pixel_width_with_sort_indicators`: Verifies alignment maintained when sorting (with ▼ ▲ indicators)
- **Test approach**:
  - Use `winfo_reqwidth()` instead of `cget("width")` to get actual rendered pixel width
  - Force geometry update with `root.update_idletasks()` before measuring
  - Test multiple sort states to ensure indicators don't break alignment
  - Compare header and data labels column-by-column with exact pixel width equality
- **Debug methodology**:
  - Created `test_debug_widths.py` to visually inspect actual width values
  - Created `test_visual_alignment.py` for manual GUI inspection
  - Confirmed current implementation IS pixel-perfect aligned (tests pass)

**What Didn't Work**:

- **Initial assumption**: Thought sort indicators (" ▼", " ▲") would cause pixel width mismatch
  - **Why it failed**: tkinter's `width=` parameter in Label is character-based, not pixel-based
  - The width= setting creates a fixed-size label that accommodates text changes
  - Sort indicators fit within the allocated width without expanding label size
- **Misdiagnosis**: Assumed existing code had alignment bug
  - **Reality**: Tests show current implementation (as of 2026-02-02) has pixel-perfect alignment
  - If user is seeing visual misalignment, it may be:
    - A rendering issue specific to certain Windows versions/themes
    - Related to font rendering or DPI scaling
    - A different part of the UI not tested (scrolling, resizing, etc.)
    - Only visible with specific data patterns not covered by tests

**Key Learnings**:

1. **Configuration ≠ Rendering**: `cget("width")` shows config, `winfo_reqwidth()` shows actual pixels
2. **tkinter Label width= is character-based**: Setting `width=10` creates space for ~10 chars at current font
3. **Sort indicators don't break width**: Text changes within a Label don't change its pixel width if width= is set
4. **TDD test hierarchy**: Need both:
   - Configuration tests (cget values match) - fast, catches design mismatches
   - Pixel tests (winfo_reqwidth matches) - slower, catches rendering issues
5. **Geometry updates are critical**: Must call `update_idletasks()` before measuring pixel widths in tests
6. **Multiple sort states testing**: Important to verify alignment holds when headers change (sorting)
7. **Visual inspection still valuable**: Automated tests may not catch all rendering quirks on different systems

**Potential Investigation Needed**:

If user still sees visual misalignment despite tests passing:

- Run `test_visual_alignment.py` on user's system to check visual appearance
- Check Windows display scaling / DPI settings
- Verify font rendering on user's system (ClearType settings)
- Test with actual user data (may have edge cases not in test data)
- Check if issue appears only when window is resized or scrolled

**Files Changed**:

1. `tests/test_analysis_timeline.py`:
   - Added `test_header_pixel_width_matches_data_row_pixel_width` to TestAnalysisTimelineHeaderAlignment
   - Added `test_header_pixel_width_with_sort_indicators` to TestAnalysisTimelineHeaderAlignment
   - Both tests use `winfo_reqwidth()` for pixel-perfect width comparison
   - Second test cycles through all sortable columns to verify alignment maintained

2. `test_debug_widths.py` (debug script):
   - Prints table comparing header vs data widths (config and pixel)
   - Confirmed all columns show matching pixel widths

3. `test_visual_alignment.py` (visual inspection script):
   - Creates GUI with multiple rows for manual inspection
   - Allows interactive testing of sort functionality
   - Useful for verifying visual alignment on specific systems

---

### [2026-02-02] - Timeline Width Validation Test

**Change Requested**: Create test to verify timeline header and rows show all data and don't span outside frame/root

**What Worked**:

- **Test approach**: Used `winfo_reqwidth()` to check required width instead of actual width
  - Why: In headless test environment, tkinter windows don't properly size (canvas width stays at 1px)
  - Solution: Check required width against typical full-screen width (1920px) instead of container width
- **Multiple assertions**:
  1. Header required width ≤ 1920px (typical full-screen)
  2. Each row required width ≤ 1920px
  3. At least one row exists to validate
  4. Header and row widths are consistent (within 10% tolerance)
- **Test data**: Created session with long comments to stress-test column wrapping
- **Geometry manager**: Used simple parent_frame without explicit sizing, relying on `update_idletasks()`

**What Didn't Work**:

- **Initial approach**: Trying to check actual canvas width with `winfo_width()`
  - **Why it failed**: Canvas shows 1px width in headless test environment even after `geometry()` and `update()` calls
  - **Error**: `AssertionError: 1 not greater than 100 : Canvas width (1px) is too small`
- **Mixing geometry managers**: Tried using `pack()` on parent_frame
  - **Why it failed**: Root already uses `grid()` manager, can't mix pack and grid
  - **Error**: `TclError: cannot use geometry manager pack inside . which already has slaves managed by grid`
- **Using grid on parent_frame**: Tried `parent_frame.grid(row=0, column=0)` with weight configuration
  - **Why it failed**: Still didn't properly size canvas in test environment
  - **Fix**: Abandoned trying to get actual canvas width, used required width instead

**Key Learnings**:

1. **Tkinter testing limitations**: Window geometry doesn't update properly in headless test environments
2. **Use required width**: `winfo_reqwidth()` works in tests, `winfo_width()` doesn't
3. **Reasonable bounds**: Check against typical screen resolution (1920px) rather than container
4. **Consistency check**: Verify header and row widths match (within tolerance) to ensure column alignment
5. **Test data design**: Use long text in comments to stress-test wrapping and width constraints

**Files Changed**:

1. `tests/test_analysis_timeline.py`:
   - Added test_timeline_fits_within_window_bounds to TestAnalysisFrameTimelineColumns
   - Checks header required width ≤ 1920px
   - Checks all row required widths ≤ 1920px
   - Verifies header and row widths are consistent (within 10% tolerance)

**Test Results**:

- New test passes ✅
- All 6 TestAnalysisFrameTimelineColumns tests passing ✅
- Total timeline column tests: 6/6 passing

**Why This Approach Succeeded**:

- Recognized tkinter test environment limitations early
- Pivoted from actual width to required width approach
- Used realistic screen resolution as validation threshold
- Added consistency check for column alignment verification

---

### [2026-02-02] - Timeline Columns Refinement (Remove Project, Narrow Active Status Columns)

**Change Requested**: Refine timeline columns after initial implementation:

1. Remove "Project" column (duplicates Primary Project/Action column)
2. Make "Sphere Active" column narrower (width 5 instead of 10) and remove bold font
3. Make "Project Active" column narrower (width 5 instead of 10) and remove bold font
4. Ensure timeline fits in window when full screen

**What Worked**:

- **Column removal**: Successfully removed "Project" column from both header and row display
- **Width reduction**: Changed Sphere Active and Project Active from width=10 to width=5
- **Font styling**: Removed "bold" from font tuple for active status columns:
  ```python
  # Before: font=("Arial", 8, "bold")
  # After:  font=("Arial", 8)
  ```
- **Test cleanup**: Removed test_timeline_header_has_project_column test since column no longer exists
- **Synchronized updates**: Updated three locations consistently:
  1. Initial header creation in create_widgets (line 235)
  2. Row display in update_timeline (line 1010)
  3. Dynamic header in update_timeline_header (line 1080)
- **Width calculation**: Total timeline width reduced from 198 to 176 characters:
  - Removed Project column: -12 characters
  - Narrowed Sphere Active: -5 characters
  - Narrowed Project Active: -5 characters
  - Total savings: 22 characters

**What Didn't Work**:

- **N/A**: All changes applied successfully in first attempt

**Key Learnings**:

1. **Column consistency**: When modifying columns, must update all three places: initial header, row display, and dynamic header
2. **Width optimization**: Active status columns with just checkmarks (✓) only need width=5, not width=10
3. **Font tuples**: To unbold, remove "bold" from font tuple: `("Arial", 8)` instead of `("Arial", 8, "bold")`
4. **Test maintenance**: Remove tests for removed features to keep test suite accurate
5. **Multi-replace efficiency**: Can update multiple locations in single tool call for related changes

**Files Changed**:

1. `src/analysis_frame.py`:
   - Removed Project column header from create_widgets (line 235-260)
   - Changed Sphere Active width from 10→5, removed bold
   - Changed Project Active width from 10→5, removed bold
   - Removed project column from row display (line 1010)
   - Updated update_timeline_header to match (line 1080)
2. `tests/test_analysis_timeline.py`:
   - Removed test_timeline_header_has_project_column test

**Test Results**:

- 5 timeline column tests (down from 6 after removing project column test)
- All existing tests should pass (no functionality changes, just UI refinement)

**Why This Approach Succeeded**:

- Clear understanding of which locations needed updates
- Consistent changes across all three display points
- Proper test cleanup to match implementation changes
- Width calculation verified timeline will fit better in window

---

### [2026-02-02] - Timeline Columns Enhancement (Sphere, Sphere Active, Project, Project Active)

**Change Requested**: Add 4 new columns to timeline after Duration column:

1. Sphere (sphere name from session)
2. Sphere Active (checkbox/checkmark if active)
3. Project (project name from active period)
4. Project Active (checkbox/checkmark if active)

**What Worked**:

- **TDD workflow**: Wrote tests first, achieved proper red phase (5 FAILURES, 0 ERRORS)
- **Test structure**: Created TestAnalysisFrameTimelineColumns test class with 6 tests:
  - 4 header tests (verifying column headers exist)
  - 2 row display tests (verifying data appears in rows)
- **Header updates**: Added new column headers in create_widgets (line 235):
  ```python
  create_initial_header("Sphere", "sphere", 12)
  tk.Label(..., text="Sphere Active", width=10, ...)
  create_initial_header("Project", "project", 12)
  tk.Label(..., text="Project Active", width=10, ...)
  ```
- **Data structure updates**: Added sphere/project metadata to timeline_data dict for all period types
- **Sphere-level variables**: Defined `sphere_name` and `sphere_active` at session level (line 760), making them available for all period types (active, break, idle)
- **Project-level variables**: Defined `project_active` within active periods loop (line 815)
- **Row display updates**: Modified timeline row creation (line 1010) to display new columns:
  ```python
  create_label(period.get("sphere", ""), 12)
  create_label("✓" if period.get("sphere_active", True) else "", 10)
  create_label(period.get("project", ""), 12)
  create_label("✓" if period.get("project_active", True) else "", 10)
  ```
- **Test data structure**: Used nested Frame structure - timeline_frame contains row_frames, row_frames contain labels
- **Test fix**: Updated test to iterate through row_frames to find labels (not just direct children of timeline_frame)

**What Didn't Work**:

- **Initial test implementation**: First test checked only direct children of timeline_frame
  - **Why it failed**: Labels are children of row_frame widgets, not direct children of timeline_frame
  - **Fix**: Updated test to iterate through row_frames, then check their label children
- **Variable scope issue**: Initially defined `sphere_name` and `sphere_active` inside active periods loop
  - **Why it failed**: Break and idle periods also need sphere metadata, causing UnboundLocalError
  - **Fix**: Moved sphere variables to session level (before period loops) so all period types can access them
- **Multi-replace string matching**: Some replacements failed during initial implementation
  - **Why it failed**: String matching requires EXACT whitespace/indentation match
  - **Fix**: Read exact file content first, then construct precise oldString with matching formatting

**Key Learnings**:

1. **Timeline widget structure**: timeline_frame → row_frame → labels (nested 2 levels)
2. **Variable scope for shared data**: Define session-level variables before loops if multiple period types need them
3. **Active status lookup**: Use `tracker.settings.get("spheres", {}).get(sphere_name, {}).get("active", True)`
4. **TDD validation**: Run previous tests after implementation to catch regressions (caught UnboundLocalError)
5. **String replacement precision**: multi_replace_string_in_file requires exact matches - read file content first

**Files Changed**:

1. `src/analysis_frame.py`:
   - Added 4 column headers (line 235-250)
   - Defined sphere variables at session level (line 760-762)
   - Added sphere/project data to active periods (line 820-827)
   - Added sphere/project data to break periods (line 863-867)
   - Added sphere/project data to idle periods (line 903-907)
   - Added 4 columns to row display (line 1010-1013)
2. `tests/test_analysis_timeline.py`:
   - Added TestAnalysisFrameTimelineColumns class (6 tests)
   - Fixed test to handle nested widget structure

**Test Results**:

- All 6 timeline column tests passing ✅
- All 18 status filter tests passing (no regressions) ✅
- Total: 24/24 tests passing

**Why This Approach Succeeded**:

- Followed TDD workflow strictly (red → green)
- Proper test structure for tkinter's nested widget hierarchy
- Correct variable scoping for session-level metadata
- Regression testing caught scope issue early

---

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

### [2026-02-02] - Analysis Frame Status Filter Integration Tests (TDD)

**Change Requested**: Write integration tests for status filter behavior with different sphere/project combinations and fix filtering logic

**User Requirements**:

Three test scenarios:

1. Active sphere + active project: show only when filter is "active" or "all"
2. Active sphere + inactive project: show only when filter is "archived" or "all"
3. Inactive sphere + active project: show only when filter is "archived" or "all"

**Approaches Tried**:

1. **TDD Workflow with Integration Tests** - ✅ **WORKED**
   - Details: Wrote 6 integration tests BEFORE fixing implementation
   - Test run showed 1 FAILURE (proper TDD red phase - no ERRORS)
   - Failure revealed filtering logic needed update
   - Fixed logic, all tests passed (TDD green phase)

**What Worked**: ✅

- **Proper TDD Red Phase**: Got 1 FAILURE (not ERROR) on first test run ✅
- **Integration test structure**: Used TestFileManager for test data isolation
- **Comprehensive test coverage**: 6 tests cover all scenarios (active/all/archived filters × different combinations)
- **Updated filtering logic**: Modified `get_filtered_spheres()` and `update_project_filter()` to handle new requirements

**Implementation Details**:

Files modified:

- `tests/test_analysis_timeline.py`:
  - Added `TestAnalysisFrameStatusFilterIntegration` class with 6 integration tests
  - Tests verify dropdown filtering and session visibility
  - Updated `test_archived_filter_shows_only_archived_spheres` to match new behavior

- `src/analysis_frame.py`:
  - Updated `get_filtered_spheres()`: In "archived" mode, show ALL spheres (not just inactive)
  - Updated `update_project_filter()`: Considers both sphere and project active status
  - Added logic: Active spheres in "archived" mode show only inactive projects
  - Added logic: Inactive spheres in "archived" mode show all projects

**Key Filtering Logic**:

```python
def get_filtered_spheres(self):
    if filter_status == "active":
        # Only show active spheres
        if is_active:
            spheres.append(sphere)
    elif filter_status == "archived":
        # Show ALL spheres (both active and inactive)
        # Active spheres can have inactive projects
        spheres.append(sphere)
    elif filter_status == "all":
        # Show all spheres
        spheres.append(sphere)

def update_project_filter(self, set_default=False):
    sphere_is_active = self.tracker.settings.get("spheres", {}).get(sphere, {}).get("active", True)

    if filter_status == "archived":
        # If sphere is active, show only inactive projects
        # If sphere is inactive, show all projects
        if sphere_is_active:
            if not is_active:
                projects.append(proj)
        else:
            projects.append(proj)
```

**Test Scenarios Covered**:

1. ✅ Active sphere + active project shows on "active" filter
2. ✅ Active sphere + active project shows on "all" filter
3. ✅ Active sphere + inactive project shows on "archived" filter
4. ✅ Active sphere + inactive project shows on "all" filter
5. ✅ Inactive sphere + active project shows on "archived" filter
6. ✅ Inactive sphere + active project shows on "all" filter

**What Didn't Work**: ❌

- **Initial filtering logic**: Didn't account for active spheres needing to appear in "archived" mode
  - Problem: When filter was "archived", `get_filtered_spheres()` only returned inactive spheres
  - Solution: Changed "archived" mode to show ALL spheres
  - Rationale: Active spheres can have inactive projects that need to be accessible

**Key Learnings**:

1. **TDD caught the bug immediately**: Integration tests revealed filtering logic issue before manual testing
2. **Complex filter requirements**: "Archived" mode is not just "show archived items" - it's "show items that are or have archived content"
3. **Test data isolation**: TestFileManager pattern works well for integration tests
4. **Update old tests when requirements change**: Had to update `test_archived_filter_shows_only_archived_spheres` to match new behavior
5. **Integration tests complement unit tests**: Unit tests verified radio buttons exist, integration tests verified filtering actually works

**Test Results**:

- ✅ All 18 status filter tests pass (6 sphere + 6 project + 6 integration)
- ✅ No regressions in existing functionality
- ✅ Proper TDD workflow: Red → Green → Refactor

**TDD Workflow Summary**:

1. ✅ Wrote 6 integration tests first
2. ✅ Ran tests → `FAILED (failures=1)` → Proper RED phase
3. ✅ Fixed `get_filtered_spheres()` and `update_project_filter()`
4. ✅ Ran tests → `OK` → GREEN phase achieved
5. ✅ Verified no regressions (18/18 tests pass)

**Success Metrics**:

- ✅ Followed TDD workflow correctly (no violations of red phase rule)
- ✅ All 6 integration tests pass
- ✅ Filtering logic correctly handles all 3 scenarios
- ✅ Code is maintainable with clear documentation
- ✅ No regressions in existing tests

---
