# Time Track Timer

## Main Frame

```python
import tkinter as tk
import time
import os
import threading

session_name = None
session_active = False
break_active = False
break_start = None
break_session = []
session_idle = False
last_user_input = None
settings_file = "settings.json"
data_file = "data.json"
```

### Core Functions

#### get_settings()

Set default settings and load from file if exists.

**Default Settings:**

- `idle_threshold`: 60 seconds
- `idle_break_threshold`: 300 seconds

Uses EAFP (Easier to Ask for Forgiveness than Permission) philosophy.

#### start_session(sphere=default)

Starts a new tracking session for a given sphere (e.g., "coding").

**Creates session data:**

- Session start time
- Sphere name
- Date and timestamp
- Unique session identifier

#### end_session()

Store timestamp locally and in JSON

#### start_break()

Store timestamp locally and in JSON

#### end_break()

Store timestamp locally and in JSON

#### session_idle(settings)

Tracks keyboard and mouse input, sets timestamp to last action.

**Behavior:**

- Monitors user input continuously
- Triggers idle state after `idle_threshold`
- Automatically starts break after `idle_break_threshold`

#### idle_data(session_idle, start_idle_input, end_idle_input=None)

Wrapper function to package idle tracking **data**.

---

## Settings Frame

**Features to implement:**

- Goal setting for spheres (session names)
- Goal setting for actions by sphere
- Add/manage spheres, projects, active-actions, break-actions
- Default session sphere
- Default time estimates for actions

---

## Evaluate Frame

**Analysis features:**

- Agent API(s) for analysis
- Default customizable questionnaire per session
- User questionnaire data collection
- Side-by-side comparison: self-analysis vs. agent summaries
- Consensus summary with dissenting opinions
- Filterable reports (all, session, date, actions)
- Field editing capability

---

## Completed Frame

Opens automatically when `end_session()` is called.

**Displays:**

- Session summary with all time data:
  - Working time
  - Break time
  - Idle time
- Time periods with associated spheres/projects/actions
- Default settings populated from file

**Functionality:**

- Add new spheres, projects, or actions
- Saves to settings file
- Auto-populate action times/percentages
- Divvy up active work and break time
- Text boxes for action justification
- "Was this necessary?" checkbox with elaboration field

---

## Thoughts and Questions

### Architecture

**Class vs Functions?**

- Session logic might benefit from class structure
- Avoids passing variables between functions
- How to handle multiple break sessions? → Store in list with abstraction

### Scalability

**Deployment Options:**

- Currently: Local Python application
- Future considerations:
  - Browser-based version (minimal changes?)
  - Mobile app conversion?
  - Which is more practical for user testing?

**Technology Choice:**

- Using Python for familiarity
- Want .exe for Windows taskbar visibility
- Does this limit scalability?

### Value Proposition

**Core Questions:**

- Does this make a meaningful difference?
- Is the time investment worth it?
- **Time alignment concept:**
  - Is activity moving toward goals for this sphere?
  - Reveals blindspots in time usage

### Data Storage

**Why NoSQL/JSON?**

- Rarely altering saved data
- Primarily read operations
- Single JSON file seems sufficient

**Concerns:**

- JSON file size limits?
- Should data be split into separate files periodically?

---

## Implementation Notes

### Threading

- `session_idle_thread` runs continuously during active sessions
- Daemon thread for background monitoring
- Joins with 1.0s timeout when idle ends

### Auto-save

- Save to JSON on every function call
- Automatic backup every 5 minutes

### Dashboard

- Display average time by sphere
- Show actions and breaks per:
  - Last week
  - Last two weeks
  - Work week

---

## Known Issues / TODO

**Code Syntax Issues:**

- Missing colons after `with open()` statements
- `os.input.time.perf_counter()` syntax needs correction
- Missing `import json`
- `if __main__ == "__name__"` should be `if __name__ == "__main__"`
- Thread `arg=` should be `args=`
- `daemon=true` should be `daemon=True`
- Missing colon after `if session_active`
