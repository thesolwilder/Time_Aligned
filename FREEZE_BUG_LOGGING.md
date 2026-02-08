# Freeze Bug - Detailed Logging Added

## Updated Bug Description

**User Reports:**

- Can't scroll after CSV export → navigation → back to analysis → show timeline
- Widgets break when clicking different timeline cards
- Application appears to freeze

**Root Cause Hypothesis**: ScrollableFrame canvas loses mousewheel bindings or gets destroyed during frame recreation.

## What Was Added

Comprehensive logging has been added to trace the exact data flow during the freeze bug scenario.

## Files Modified

### 1. `src/analysis_frame.py`

#### `export_to_csv()` (Line ~1267)

**Logs Added:**

- Instance ID of AnalysisFrame
- Whether timeline_frame exists and its ID
- Size of timeline_data_all
- Selected card and date range
- Number of sessions loaded from file
- Number of periods collected for export
- Save file path
- **After export completes:**
  - Instance ID (to confirm it's the same instance)
  - timeline_frame ID
  - timeline_data_all size
  - periods_loaded count
  - Timeline frame children count

#### `select_card()` (Line ~346)

**Logs Added:**

- Card index and range name
- Instance ID of AnalysisFrame
- Whether timeline_frame exists and its ID
- **NEW: ScrollableFrame state before update:**
  - timeline_scroll exists and valid
  - Canvas exists and valid
  - Canvas scrollregion
  - Canvas bindings (should include MouseWheel)
- timeline_frame.winfo_exists() status
- timeline_frame.master reference
- Timeline frame children count
- **NEW: ScrollableFrame state after update:**
  - timeline_scroll still valid
  - Canvas bindings still present
  - Canvas scrollregion updated
- Errors accessing timeline_frame or scrollable frame state

#### `update_timeline()` (Line ~1033)

**Logs Added:**

- Instance ID of AnalysisFrame
- **NEW: ScrollableFrame state BEFORE frame destruction:**
  - timeline_scroll exists and valid
  - Canvas exists and valid
  - Canvas scrollregion
  - Canvas bindings
- Whether timeline_frame attribute exists
- Whether timeline_frame is None
- timeline_frame.winfo_exists() check
- Parent frame reference before destroy
- Parent type (to verify it's the scrollable frame's content frame)
- New timeline_frame ID after recreation
- Parent still exists after recreation (validates parent wasn't destroyed)
- Date range being loaded
- Number of periods loaded
- Sort column and reverse status
- First page load progress
- Timeline header update completion
- **NEW: ScrollableFrame state AFTER complete update:**
  - timeline_scroll still valid
  - Canvas still valid
  - Canvas scrollregion updated
  - Canvas bindings still present
  - Canvas bbox (content area) with dimensions

### 3. `src/ui_helpers.py` (ScrollableFrame)

#### `_setup_mousewheel()` and `on_mousewheel()` (Line ~155)

**Logs Added:**

- Canvas existence validation before scrolling
- TclError during mousewheel events (canvas destroyed/invalid)
- Unexpected errors with full stack trace
- Root window binding success/failure
- All mousewheel binding errors

**Why This Matters**: If canvas gets destroyed but bindings remain, mousewheel events will trigger errors and scrolling will break.

## How to Use

### 2. `time_tracker.py`

#### `open_analysis()` (Line ~1022)

**Logs Added:**

- Whether analysis_frame already exists
- Old AnalysisFrame instance ID (if exists)
- Old timeline_frame ID (if exists)
- Destruction of old frame
- Creation of new AnalysisFrame instance
- New instance ID
- New timeline_frame ID
- Grid placement confirmation
- Any errors during process

#### `open_session_view()` (Line ~1159)

**Logs Added:**

- from_analysis flag value
- analysis_frame instance ID (when coming from analysis)
- analysis_frame.timeline_frame ID
- Which frame is being hidden
- Session view container creation
- CompletionFrame creation

#### `close_session_view()` (Line ~1200)

**Logs Added:**

- came_from_analysis flag value
- Destruction of session view container
- Old analysis_frame instance ID (if returning to analysis)
- Old timeline_frame ID
- Destruction of old analysis frame
- Call to open_analysis()
- Which frame is being shown

## How to Use

### Option 1: Run Debug Script

```powershell
python debug_freeze_bug.py
```

Follow the on-screen instructions to reproduce the bug. The script will guide you through the exact steps.

### Option 2: Run Normally

```powershell
python time_tracker.py
```

Then follow these steps:

1. Click "Analysis" button
2. Select "All Spheres" and "All Time" card
3. Click "Export CSV"
4. Save the file
5. Click "Latest Session" to open completion frame
6. Click "Back" to return to analysis
7. Click on any card (e.g., "All Time")
8. **Try to SCROLL using mouse wheel**
9. **Click different cards and try scrolling each time**

## What to Look For

### During CSV Export

Look for the section marked:

```
================================================================================
CSV EXPORT STARTED
================================================================================
```

**Key Data Points:**

- `timeline_data_all size`: How many periods are in memory BEFORE export
- `Loaded X sessions from file`: How much data is being processed
- `Collected X periods to export`: How many rows will be in CSV
- After export: `timeline_data_all size`: Should be the SAME as before

### During Navigation

Look for:

```
================================================================================
OPEN_SESSION_VIEW CALLED
================================================================================
```

and

```
================================================================================
CLOSE_SESSION_VIEW CALLED
================================================================================
```

**Key Data Points:**

- Instance IDs should CHANGE when returning from session view
- Old frame should be destroyed before new one is created
- No errors accessing destroyed widgets

### During "Show Timeline" Click

Look for:

```
================================================================================
SELECT_CARD CALLED
================================================================================
```

followed by:

```
--------------------------------------------------------------------------------
UPDATE_TIMELINE CALLED
--------------------------------------------------------------------------------
```

**Key Data Points:**

- `timeline_frame.winfo_exists()`: Should be `True`
- **NEW: `timeline_scroll.winfo_exists()`**: Should be `True` before AND after update
- **NEW: `Canvas exists and valid`**: Should be `True` before AND after update
- **NEW: `Canvas bindings`**: Should include `<MouseWheel>` before AND after update
- **NEW: `Canvas scrollregion`**: Should be valid dimensions like `('0', '0', '800', '5000')`
- **NEW: `Canvas bbox`**: Should show content area dimensions
- `Loaded X periods`: Should match what you expect based on filters
- `Loading first page (50 periods)...`: Should complete without freezing
- No `ERROR` messages

### NEW: During Scroll Attempt

Look for:

```
[SCROLL ERROR] Canvas doesn't exist in on_mousewheel
```

or

```
[SCROLL ERROR] TclError in on_mousewheel: ...
```

**If you see these**: The canvas is getting destroyed but mousewheel events are still firing.

## What Might Cause the Bug

### Hypothesis 1: ScrollableFrame Canvas Gets Destroyed

- Check if `Canvas exists and valid` becomes `False` after update_timeline
- Check if `Canvas bindings` list becomes empty `[]`
- Check if scroll errors appear when trying to use mouse wheel

### Hypothesis 2: Canvas Bindings Are Lost

- Check if `Canvas bindings` shows `<MouseWheel>` before update but not after
- Check if `[SCROLL SETUP] Successfully bound mousewheel` appears on fresh instance
- Check if scrolling worked before navigation but not after

### Hypothesis 3: ScrollableFrame Reference Is Lost

- Check if `timeline_scroll` exists before update but causes errors after
- Check if `timeline_scroll.winfo_exists()` is `True` before but `False` after
- Check if parent frame is getting destroyed accidentally

### Hypothesis 4: Data Loading Inconsistency

- Check if `Loaded X periods` differs between instances for same filter
- First instance loaded 263 periods, second loaded only 88 periods (from your debug output)
- This suggests filter state is different between instances

## Expected Behavior (No Bug)

With all the fixes in place, you should see:

1. CSV export completes with all data preserved
2. Navigation to session view hides (grid_forget) analysis frame
3. Return from session view DESTROYS old frame and creates NEW one
4. New AnalysisFrame has fresh timeline_frame
5. **NEW: ScrollableFrame canvas remains valid throughout**
6. **NEW: Canvas bindings include `<MouseWheel>` before AND after update**
7. **NEW: Canvas scrollregion is set correctly with content dimensions**
8. **NEW: Mouse wheel scrolling works smoothly**
9. Clicking card triggers update_timeline successfully
10. Timeline loads and displays without freezing
11. **NEW: Clicking different cards updates correctly with working scroll**

## If Bug Still Exists

The logs will show you EXACTLY which hypothesis is correct:

- **Canvas destroyed?** → `Canvas exists and valid: False` or scroll errors
- **Bindings lost?** → `Canvas bindings: []` or missing `<MouseWheel>`
- **ScrollableFrame broken?** → `timeline_scroll.winfo_exists(): 0`
- **Data inconsistency?** → Different `Loaded X periods` for same filter
- **Parent destroyed?** → `Parent still exists after recreate: 0`

## What to Report Back

Please provide:

1. **Can you scroll after step 8?** (Yes/No)
2. **Do widgets break when clicking different cards?** (Yes/No / Which cards?)
3. **Console output** - specifically:
   - Any lines with `[SCROLL ERROR]`
   - Canvas bindings before and after update
   - Canvas scrollregion values
   - Any `[UPDATE ERROR]` or `[SELECT ERROR]` messages
4. **Screenshot or description** of what "widgets break" looks like
