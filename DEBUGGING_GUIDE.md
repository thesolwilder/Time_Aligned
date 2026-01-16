# Debugging Guide for Python Applications

## 🐛 Bug Found: Missing Last Active Period

### Root Cause

The `end_session()` method in `time_tracker.py` was not saving the final active period before ending the session.

### The Fix

Added code to save the final active period in `end_session()` before stopping the session:

```python
# Save the final active period (if not on break)
if not self.break_active and self.active_period_start_time:
    current_time = time.time()
    all_data = self.load_data()
    if self.session_name in all_data:
        all_data[self.session_name]["active"].append({
            "start": datetime.fromtimestamp(self.active_period_start_time).strftime("%H:%M:%S"),
            "start_timestamp": self.active_period_start_time,
            "end": datetime.fromtimestamp(current_time).strftime("%H:%M:%S"),
            "end_timestamp": current_time,
            "duration": current_time - self.active_period_start_time,
        })
        self.save_data(all_data)
```

---

## 🔍 Debugging Best Practices

### 1. **Reproduce the Bug**

- Create minimal, consistent steps to reproduce
- Document exact conditions (state, inputs, timing)
- Try to reproduce multiple times

### 2. **Narrow Down the Location**

Ask yourself:

- Is it a **data problem** (wrong data saved) or **display problem** (right data, wrong display)?
- Which **component** is responsible? (UI, business logic, data layer)
- What's the **data flow**? (Input → Processing → Storage → Display)

### 3. **Check Data First**

Before diving into code:

- **Inspect data.json** - Is the data being saved correctly?
- **Print data structures** - What does the session object contain?
- **Compare expected vs actual** - What should be there vs what is there?

---

## 🛠️ Debugging Tools & Techniques

### **Option 1: Print Debugging (Fastest for Quick Issues)**

**When to use:**

- Quick issues you can reproduce easily
- Understanding data flow
- Checking variable values

**How to use:**

```python
# Print with context
print(f"=== DEBUG: Function Name ===")
print(f"Variable name: {variable_value}")

# Print data structures
print(f"Session data: {json.dumps(session_data, indent=2)}")

# Print execution flow
print(f"DEBUG: Reached checkpoint A")

# Print types
print(f"Type of data: {type(data)}")
```

**Pros:**

- ✅ Fastest to add
- ✅ Works everywhere
- ✅ Good for data inspection

**Cons:**

- ❌ Clutters output
- ❌ Need to remove later
- ❌ Can't step through code

---

### **Option 2: Python Debugger (pdb) - Built-in**

**When to use:**

- Need to pause execution and inspect
- Step through code line by line
- Check variable values interactively

**How to use:**

```python
import pdb

def my_function():
    x = 10
    pdb.set_trace()  # Execution pauses here
    y = x * 2
    return y
```

**Debugger Commands:**

- `n` (next) - Execute next line
- `s` (step) - Step into function
- `c` (continue) - Continue execution
- `p variable` - Print variable value
- `pp variable` - Pretty print
- `l` (list) - Show current code
- `q` (quit) - Exit debugger

**Pros:**

- ✅ Built-in, no installation
- ✅ Interactive variable inspection
- ✅ Step through execution

**Cons:**

- ❌ Terminal-based interface
- ❌ Less visual than IDE debugger

---

### **Option 3: VS Code Debugger (Most Powerful)**

**When to use:**

- Complex bugs requiring inspection
- Need visual call stack
- Want to watch multiple variables
- Conditional breakpoints

**How to use:**

1. **Set Breakpoint:**

   - Click left of line number (red dot appears)
   - Or press `F9`

2. **Start Debugging:**

   - Press `F5`
   - Select "Python File"

3. **Debug Controls:**

   - `F5` - Continue
   - `F10` - Step Over (next line)
   - `F11` - Step Into (enter function)
   - `Shift+F11` - Step Out (exit function)
   - `Shift+F5` - Stop

4. **Features:**
   - **Variables panel** - See all variables in scope
   - **Watch panel** - Track specific expressions
   - **Call Stack** - See function call chain
   - **Debug Console** - Execute code while paused

**Advanced:**

```python
# Conditional breakpoint (right-click breakpoint → Edit Breakpoint)
# Only breaks when condition is true:
if idx == 5:
    pass  # Breakpoint here

# Logpoint (right-click → Add Logpoint)
# Prints message without stopping:
# "Value of x is {x}"
```

**Pros:**

- ✅ Visual interface
- ✅ See all variables
- ✅ Powerful features
- ✅ Conditional breakpoints

**Cons:**

- ❌ Slower to set up
- ❌ Can be overwhelming

---

### **Option 4: Logging (Production-Ready)**

**When to use:**

- Production code
- Long-running processes
- Need permanent debugging traces

**How to use:**

```python
import logging

# Setup (in main file)
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='app.log'
)

logger = logging.getLogger(__name__)

# Use in code
logger.debug("Detailed debugging information")
logger.info("General information")
logger.warning("Warning message")
logger.error("Error occurred")
logger.critical("Critical error")

# With variables
logger.debug(f"Session name: {self.session_name}, Active: {self.session_active}")
```

**Logging Levels:**

- `DEBUG` - Detailed diagnostic info
- `INFO` - Confirmation things work as expected
- `WARNING` - Something unexpected but code still works
- `ERROR` - Serious problem, function failed
- `CRITICAL` - Program may crash

**Pros:**

- ✅ Stays in production code
- ✅ Can be enabled/disabled
- ✅ Saved to file
- ✅ Different severity levels

**Cons:**

- ❌ More setup required
- ❌ Need to plan what to log

---

### **Option 5: Assert Statements**

**When to use:**

- Validate assumptions
- Catch bugs early
- Document expected state

**How to use:**

```python
def divide(a, b):
    assert b != 0, "Divisor cannot be zero"
    return a / b

# Validate data structure
assert len(all_periods) > 0, "Expected at least one period"
assert isinstance(session_data, dict), "Session data must be a dict"

# Check state
assert self.session_active, "Session must be active"
```

**Pros:**

- ✅ Documents assumptions
- ✅ Fails fast
- ✅ Self-documenting code

**Cons:**

- ❌ Removed in optimized Python (`-O` flag)
- ❌ Stops execution on failure

---

## 📋 Debugging Workflow for Unknown Codebases

### Step 1: Understand the Bug

- What's the **expected behavior**?
- What's the **actual behavior**?
- When does it happen? (specific conditions)

### Step 2: Find the Data Flow

```
User Action → Event Handler → Business Logic → Data Storage → Display
```

For this bug:

```
Click "End" → end_session() → Save to data.json → CompletionFrame reads data → Display timeline
```

### Step 3: Check Each Layer

**Layer 1: Data Storage**

```python
# Check data.json directly
import json
with open('data.json', 'r') as f:
    data = json.load(f)
    print(json.dumps(data['session_name'], indent=2))
```

**Layer 2: Business Logic**

```python
# Add prints in end_session()
print(f"Active period start: {self.active_period_start_time}")
print(f"Break active: {self.break_active}")
```

**Layer 3: Display**

```python
# Add prints in _create_timeline()
print(f"Periods loaded: {len(self.all_periods)}")
for period in self.all_periods:
    print(f"  {period['type']}: {period['start']} - {period['end']}")
```

### Step 4: Binary Search Your Code

- Add print at **start** of suspected function
- Add print at **end** of suspected function
- If both print, bug is elsewhere
- If first prints but not second, bug is in that function
- Keep narrowing down

### Step 5: Compare Working vs Broken

- When does it work? (ending on break)
- When does it break? (ending on active)
- What's different in the code paths?

---

## 🎯 Debugging Checklist

### Before You Start:

- [ ] Can you reproduce the bug consistently?
- [ ] Do you have test data to work with?
- [ ] Have you checked the error message/logs?

### Investigation:

- [ ] Check the data layer first (data.json)
- [ ] Print variable values at key points
- [ ] Verify your assumptions with assertions
- [ ] Check edge cases (empty data, null values)

### Using Debugger:

- [ ] Set breakpoint where you think bug occurs
- [ ] Step through code line by line
- [ ] Watch variable values change
- [ ] Check call stack for context

### After Fix:

- [ ] Test the original bug scenario
- [ ] Test edge cases
- [ ] Remove debug print statements
- [ ] Add logging if needed for future
- [ ] Consider adding tests to prevent regression

---

## 🧪 Writing Debug-Friendly Code

### 1. **Add Logging Early**

```python
logger.debug(f"Starting session: {session_name}")
logger.info(f"Session ended. Duration: {duration}s")
```

### 2. **Validate Assumptions**

```python
assert self.session_active, "Session must be active to end"
assert session_name in all_data, f"Session {session_name} not found"
```

### 3. **Use Descriptive Variable Names**

```python
# Bad
t = time.time()
d = t - s

# Good
current_time = time.time()
duration = current_time - start_time
```

### 4. **Return Early from Invalid States**

```python
if not self.session_active:
    logger.warning("Attempted to end inactive session")
    return
```

### 5. **Add Comments for Complex Logic**

```python
# Save final active period before ending session
# This is needed because toggle_break() saves periods,
# but end_session() doesn't call toggle_break() when ending on active
if not self.break_active and self.active_period_start_time:
    # Save logic here...
```

---

## 🔧 Quick Reference

### Print Debugging Snippet:

```python
print(f"=== DEBUG: {__name__} ===")
print(f"Variable: {variable}")
print(f"Type: {type(variable)}")
import json; print(json.dumps(dict_var, indent=2))
```

### VS Code Debug Launch Config:

Create `.vscode/launch.json`:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: Current File",
      "type": "python",
      "request": "launch",
      "program": "${file}",
      "console": "integratedTerminal"
    }
  ]
}
```

### PDB Quick Reference:

```
h       - help
n       - next line
s       - step into
c       - continue
p var   - print variable
pp var  - pretty print
l       - list code
w       - where am I (call stack)
q       - quit
```

---

## 📚 Additional Resources

- [Python Debugging With Pdb](https://realpython.com/python-debugging-pdb/)
- [VS Code Python Debugging](https://code.visualstudio.com/docs/python/debugging)
- [Python Logging HOWTO](https://docs.python.org/3/howto/logging.html)
- [Debugging Strategies](https://blog.regehr.org/archives/199)

---

## Summary

**For this bug:**

1. ✅ Added print statements to track data flow
2. ✅ Found `end_session()` wasn't saving final active period
3. ✅ Fixed by adding save logic before stopping session
4. ✅ Debug prints show the data is now correct

**General approach:**

1. Check data.json first (data layer)
2. Add strategic prints (execution flow)
3. Use debugger for complex issues (step through)
4. Compare working vs broken scenarios
5. Test the fix thoroughly
