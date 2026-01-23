# Agent Standing Orders - Implementation Options

This document explains how to ensure AI coding agents (like GitHub Copilot) follow your project's standards and procedures automatically.

## What I Created for You

### 1. [DEVELOPMENT.md](../DEVELOPMENT.md)

**Comprehensive development guide** covering:

- Test hierarchy (import → unit → integration → E2E)
- TDD workflow and best practices
- Code organization standards
- Testing patterns and examples
- Architecture documentation

**When agents reference this**: When they need detailed guidance on implementation

### 2. [.github/COPILOT_INSTRUCTIONS.md](../COPILOT_INSTRUCTIONS.md)

**Quick reference for AI agents** with:

- Concise standing orders
- Pre/post-flight checklists
- Quick code patterns
- Link to full DEVELOPMENT.md

**When agents reference this**: GitHub Copilot automatically reads this on every interaction

---

## How Agents Will Use These Files

### Automatic Recognition (GitHub Copilot)

GitHub Copilot **automatically reads** these files:

- `.github/COPILOT_INSTRUCTIONS.md` - Always included in context
- `DEVELOPMENT.md` - High priority for development questions
- `CONTRIBUTING.md` - Standard for open source projects
- `README.md` - Project overview

### File Naming Best Practices

**Highly Recognized Names** (agents prioritize these):

- ✅ `DEVELOPMENT.md` - Development practices
- ✅ `CONTRIBUTING.md` - Contribution guidelines
- ✅ `TESTING.md` - Testing procedures
- ✅ `ARCHITECTURE.md` - System design
- ✅ `.github/COPILOT_INSTRUCTIONS.md` - AI-specific guidance

**Less Recognized** (might be missed):

- ❌ `PROJECT_GUIDELINES.md`
- ❌ `CODING_STANDARDS.md`
- ❌ Custom names

---

## Alternative Approaches to Markdown Files

### Option 1: Inline Documentation (Code Comments)

**What**: Document standards directly in code

```python
"""
TESTING STANDARD:
All new features require:
1. Import test
2. Unit tests (>80% coverage)
3. Integration tests
See DEVELOPMENT.md for details
"""
```

**Pros**:

- Always visible in context
- Harder to miss

**Cons**:

- Clutters code
- Harder to maintain
- Not language-agnostic

**Verdict**: ❌ Use for specific modules only, not project-wide

---

### Option 2: pytest.ini / setup.cfg

**What**: Configuration files that enforce standards

```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = --strict-markers --cov=src --cov-report=html
```

**Pros**:

- Enforces standards automatically
- Works with CI/CD
- Language/tool specific best practices

**Cons**:

- Only enforces structure, not documentation
- Agents may not read config files for guidance
- Limited to tool-specific rules

**Verdict**: ✅ Use IN ADDITION to markdown docs

---

### Option 3: Pre-commit Hooks

**What**: Automated checks before commits

```bash
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: pytest
        name: Run tests
        entry: python tests/run_all_tests.py
        language: system
        pass_filenames: false
```

**Pros**:

- Enforces standards automatically
- Prevents bad code from being committed
- No human intervention needed

**Cons**:

- Doesn't guide during development
- Agents don't typically interact with git hooks
- Can be bypassed with `--no-verify`

**Verdict**: ✅ Use IN ADDITION to docs for enforcement

---

### Option 4: GitHub Actions / CI/CD

**What**: Automated testing on every push/PR

```yaml
# .github/workflows/test.yml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run tests
        run: python tests/run_all_tests.py
```

**Pros**:

- Catches issues before merge
- Forces compliance
- Public visibility

**Cons**:

- Feedback loop is slower
- Doesn't guide during development
- Requires GitHub/CI setup

**Verdict**: ✅ Use IN ADDITION for production enforcement

---

### Option 5: Templates

**What**: File templates agents can copy

```
# tests/TEMPLATE_test_module.py
"""Template for new test files."""

def test_import():
    """Verify module imports without errors."""
    # TODO: Import your module
    pass

def test_function_name():
    """Test specific function behavior."""
    # Arrange
    # Act
    # Assert
    pass
```

**Pros**:

- Standardizes structure
- Easy to follow
- Reduces decision fatigue

**Cons**:

- Agents may not use templates automatically
- Requires explicit instruction to use
- Needs maintenance

**Verdict**: ⚠️ Good for humans, less useful for agents

---

### Option 6: Living Documentation (Tests as Spec)

**What**: Tests themselves serve as documentation

```python
def test_backup_system_creates_timestamped_files():
    """
    SPECIFICATION:
    Backup system must create files with format:
    <original>_backup_YYYYMMDD_HHMMSS
    """
    # Test implementation
```

**Pros**:

- Self-documenting
- Always up to date
- Agents learn from examples

**Cons**:

- Requires excellent test coverage
- Not comprehensive for architecture
- Hard to get big picture

**Verdict**: ✅ Excellent complement to markdown docs

---

### Option 7: Docstring Conventions

**What**: Standardized function documentation

```python
def process_session(session_data: dict) -> dict:
    """
    Process a tracking session.

    Testing Requirements:
        - Unit: Test with valid/invalid session data
        - Integration: Test with real data file

    Args:
        session_data: Dict with required keys: start_time, end_time

    Returns:
        Processed session with calculated duration

    Raises:
        ValueError: If required keys missing
    """
```

**Pros**:

- Context-aware documentation
- Guides both humans and agents
- Standard Python practice

**Cons**:

- Only covers individual functions
- Verbose
- Agents may not prioritize reading all docstrings

**Verdict**: ✅ Use for implementation details

---

## Recommended Stack (My Opinion)

### Tier 1: Core Guidance (What I Built for You)

1. **`.github/COPILOT_INSTRUCTIONS.md`** - Quick AI reference (auto-loaded)
2. **`DEVELOPMENT.md`** - Comprehensive guide
3. **Well-structured existing tests** - Learning by example

### Tier 2: Enforcement

4. **`pytest.ini`** - Test configuration standards
5. **Pre-commit hooks** - Prevent bad commits
6. **GitHub Actions** - CI/CD testing

### Tier 3: Supporting Materials

7. **Docstrings** - Function-level guidance
8. **README.md** - Project overview
9. **Test templates** - For human developers

---

## How to Reinforce Standards with Agents

### Every Interaction Pattern

When requesting features/fixes, include:

```
"Before starting, review DEVELOPMENT.md for testing standards.
Follow the TDD approach: import test → unit → integration → E2E"
```

### Better Yet - Reference File Directly

```
"Add a new priority filter feature.
See DEVELOPMENT.md section 'Adding a New Feature' for the workflow."
```

### Let Agents Self-Check

```
"After implementation, verify against the checklist in
.github/COPILOT_INSTRUCTIONS.md"
```

---

## Making This Automatic

### GitHub Copilot Workspace

GitHub Copilot Chat in VS Code automatically considers:

- Files in `.github/` directory
- Standard community files (CONTRIBUTING, etc.)
- Recently edited files
- Files matching your query

**Your setup** (`.github/COPILOT_INSTRUCTIONS.md`) will be **automatically included** in context for most requests.

### When Agents Might Still Miss It

Agents may not reference docs when:

1. Request is very narrow ("fix this typo")
2. User is very explicit ("just add this line")
3. Context window is full
4. Agent focuses on wrong files

**Solution**: Remind agents in your request:

```
"Following DEVELOPMENT.md standards, add feature X"
```

---

## Testing Your Setup

Try asking an agent:

```
"What testing approach should I use for a new CSV export feature?"
```

✅ **Good response**: References DEVELOPMENT.md, explains import → unit → integration

❌ **Bad response**: Generic testing advice without project context

If bad, make your request more explicit:

```
"According to this project's DEVELOPMENT.md, what testing approach
should I use for a new CSV export feature?"
```

---

## Long-term Maintenance

### Keep Docs Updated

- When you change architecture, update DEVELOPMENT.md
- When you add new testing tools, update patterns
- When you change workflows, update checklists

### Make Docs Discoverable

- Link from README.md
- Mention in PR templates
- Include in onboarding

### Review Periodically

- Are agents following standards?
- Are docs still accurate?
- Are there new patterns to document?

---

## Summary

**Best approach**: ✅ **The markdown files I created**

- `.github/COPILOT_INSTRUCTIONS.md` (auto-loaded by Copilot)
- `DEVELOPMENT.md` (comprehensive reference)

**Supporting approaches**:

- pytest.ini for test configuration
- Pre-commit hooks for enforcement
- Good test examples for learning
- Docstrings for implementation details

**How to use**:

- Reference files in requests: "Following DEVELOPMENT.md..."
- Let agents self-check against checklists
- Update docs as project evolves

**The key**: Consistent, well-named files in standard locations that agents recognize and prioritize.

---

**Your setup is now ready!** Future agents will automatically consider `.github/COPILOT_INSTRUCTIONS.md` and can be directed to DEVELOPMENT.md for comprehensive guidance.
