# Shortcuts Guide - Quick Development Commands

This guide explains all the shortcuts available for faster development with AI agents.

## Methods Available

### 1. VS Code Snippets (Fastest for Chat)

**Location**: `.vscode/project.code-snippets`

**How to use**: Type the prefix in **GitHub Copilot Chat** or any text editor:

| Prefix          | Description                    | Usage                   |
| --------------- | ------------------------------ | ----------------------- |
| `/dev-feature`  | Implement new feature with TDD | Type in chat, press Tab |
| `/dev-bug`      | Fix bug with TDD workflow      | Type in chat, press Tab |
| `/dev-test`     | Add comprehensive tests        | Type in chat, press Tab |
| `/dev-refactor` | Refactor code safely           | Type in chat, press Tab |
| `/dev-review`   | Review code against standards  | Type in chat, press Tab |
| `/dev-verify`   | Verify changes checklist       | Type in chat, press Tab |
| `/tdd`          | Quick TDD reminder             | Type in chat, press Tab |
| `/standards`    | Reference all standards        | Type in chat, press Tab |

**Example**:

1. Open Copilot Chat (Ctrl+I or click chat icon)
2. Type `/dev-feature` and press Tab
3. Snippet expands with full prompt
4. Fill in the placeholders (feature name, etc.)
5. Send to Copilot

---

### 2. GitHub Copilot Chat Settings

**Location**: `.vscode/copilot-settings.json`

**What it does**: Automatically includes instructions with EVERY Copilot interaction

**Configuration**:

```json
{
  "github.copilot.chat.codeGeneration.instructions": [
    {
      "text": "Always read and follow DEVELOPMENT.md..."
    }
  ],
  "github.copilot.chat.context.files": [
    "DEVELOPMENT.md",
    ".github/COPILOT_INSTRUCTIONS.md",
    "tests/TEST_STATUS.md"
  ]
}
```

**Benefits**:

- ✅ No need to reference docs manually
- ✅ Copilot always sees your standards
- ✅ Works for all interactions automatically

---

### 3. File References in Chat

**How to use**: Reference files directly in Copilot Chat

**Syntax**:

- `#file:DEVELOPMENT.md` - Include entire file
- `#file:DEVELOPMENT.md#Adding-a-New-Feature` - Include specific section
- `#file:copilot-prompts.md#/dev-feature` - Reference specific prompt

**Examples**:

```
#file:DEVELOPMENT.md implement a date filter feature
```

```
#file:copilot-prompts.md#/dev-bug fix the idle detection issue
```

---

### 4. Copilot Prompts File

**Location**: `.vscode/copilot-prompts.md`

**How to use**: Reference specific prompts by section

**Example**:

```
#file:copilot-prompts.md#/dev-feature add user authentication
```

The prompt template expands automatically.

---

### 5. Workspace Context (Built-in)

**What**: GitHub Copilot automatically includes:

- `.github/COPILOT_INSTRUCTIONS.md` (always loaded)
- Recently edited files
- Open files in editor
- Files you `@mention`

**How to leverage**:

- Keep DEVELOPMENT.md open while coding
- Open test files as reference
- Use `@workspace` to search entire project

---

## Quick Reference Table

| Task              | Fastest Method  | Command                                     |
| ----------------- | --------------- | ------------------------------------------- |
| New feature       | VS Code snippet | `/dev-feature` + Tab                        |
| Bug fix           | VS Code snippet | `/dev-bug` + Tab                            |
| Add tests         | VS Code snippet | `/dev-test` + Tab                           |
| Code review       | VS Code snippet | `/dev-review` + Tab                         |
| General question  | File reference  | `#file:DEVELOPMENT.md`                      |
| Specific workflow | File section    | `#file:DEVELOPMENT.md#Adding-a-New-Feature` |
| Quick reminder    | File reference  | `#file:COPILOT_INSTRUCTIONS.md`             |

---

## Advanced Techniques

### Combining References

```
#file:DEVELOPMENT.md#Testing-Best-Practices
#file:TEST_STATUS.md
Add tests for the screenshot module
```

### Using @workspace

```
@workspace Where should I put the new analysis utility function?
```

### Chain Commands

```
/dev-feature user preferences
Then /dev-review the implementation
```

---

## Setting Up

### Enable Settings (One-time)

1. Open `.vscode/copilot-settings.json` in this project
2. Verify these settings are present:
   - `github.copilot.chat.codeGeneration.instructions`
   - `github.copilot.chat.context.files`
3. Reload VS Code if needed

### Test Snippets

1. Open Copilot Chat (Ctrl+I)
2. Type `/dev-`
3. You should see autocomplete suggestions
4. Press Tab to expand

### Verify File References

1. In Copilot Chat, type `#file:`
2. You should see autocomplete with project files
3. Select a file to include it

---

## Pro Tips

### 1. Create Your Own Snippets

Edit `.vscode/project.code-snippets` to add custom shortcuts:

```json
"My Custom Workflow": {
  "prefix": "/my-workflow",
  "body": [
    "Your prompt here with ${1:placeholders}"
  ],
  "description": "What it does"
}
```

### 2. Combine with @mentions

```
@workspace #file:DEVELOPMENT.md
Find all functions that need unit tests
```

### 3. Use Multi-line Prompts

Snippets support multi-line templates - use them for complex workflows:

```
/dev-feature user authentication
[expanded prompt includes all TDD steps]
```

### 4. Reference Multiple Files

```
#file:DEVELOPMENT.md
#file:TEST_STATUS.md
#file:tests/test_analysis.py
Fix the analysis tests to match current architecture
```

---

## Troubleshooting

### Snippets not showing

- Reload VS Code window
- Check `.vscode/project.code-snippets` exists
- Verify JSON syntax is valid

### File references not working

- Update GitHub Copilot extension
- Check file paths are correct
- Use relative paths from workspace root

### Settings not applying

- Reload VS Code
- Check `.vscode/copilot-settings.json` syntax
- Verify workspace folder is open (not just files)

---

## Summary

**Fastest workflow**:

1. Use VS Code snippets for common tasks (`/dev-feature`, `/dev-bug`, etc.)
2. Let `.vscode/copilot-settings.json` automatically include standards
3. Reference specific docs when needed: `#file:DEVELOPMENT.md`
4. Keep `.github/COPILOT_INSTRUCTIONS.md` updated (always auto-loaded)

**Result**: Type `/dev-feature` instead of entire TDD workflow prompt! 🚀

---

## Examples in Action

### Before (manual):

```
Following DEVELOPMENT.md standards, implement a CSV export feature.

Requirements:
1. Read DEVELOPMENT.md testing hierarchy
2. Create tests/test_csv_export.py
[... 10 more lines ...]
```

### After (with snippet):

```
/dev-feature CSV export
[Tab - expands automatically]
```

**Savings**: 30 seconds → 2 seconds per request! ⚡
