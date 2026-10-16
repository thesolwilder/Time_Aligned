# Project Scaffolder - Automated Setup for Development Standards

Quickly bootstrap new projects with standardized development documentation, TDD setup, and AI agent configurations.

## Quick Start

### Create a New Python Project

```bash
python scaffold_project.py /path/to/new/project
```

### Create a TypeScript Project

```bash
python scaffold_project.py /path/to/new/project --language typescript
```

### Scaffold Current Directory

```bash
python scaffold_project.py .
```

## What It Creates

### Directory Structure

```
your-project/
├── .github/
│   └── COPILOT_INSTRUCTIONS.md    # AI agent standing orders
├── .vscode/
│   ├── copilot-prompts.md         # Chat prompt templates
│   ├── copilot-settings.json      # Auto-load dev standards
│   └── project.code-snippets      # /dev-feature shortcuts
├── docs/                           # Documentation
├── tests/                          # Test directory
├── src/                            # Source code (TS/JS)
├── DEVELOPMENT.md                  # Complete dev guide
├── README.md                       # Project overview
├── .gitignore                      # Standard ignores
└── [language-specific configs]    # pytest.ini, vitest.config, etc.
```

### Files Created

1. **DEVELOPMENT.md** - Comprehensive development guide
   - TDD workflow (import → unit → integration → E2E)
   - Testing best practices
   - Code quality standards
   - Git conventions

2. **.github/COPILOT_INSTRUCTIONS.md** - AI agent instructions
   - Auto-loaded by GitHub Copilot
   - Enforces TDD approach
   - Quick reference checklist

3. **VS Code Configuration**
   - Copilot settings (auto-includes DEVELOPMENT.md)
   - Slash command snippets (/dev-feature, /dev-bug, etc.)
   - Prompt templates

4. **Language-Specific Setup**
   - **Python**: pytest.ini, requirements-dev.txt, **init**.py
   - **TypeScript**: vitest.config.ts, tsconfig.json
   - **JavaScript**: vitest configuration

## Usage

### Command Line Options

```bash
python scaffold_project.py <path> [options]

Arguments:
  path                  Path to project directory (use . for current)

Options:
  --language, -l        Language: python, typescript, javascript (default: python)
  --tdd                 Include TDD configs (default: true)
  --no-tdd             Exclude TDD configs
  -h, --help           Show help message
```

### Examples

**New Python project:**

```bash
python scaffold_project.py ~/projects/my-api
```

**TypeScript project in current directory:**

```bash
cd my-typescript-app
python scaffold_project.py . --language typescript
```

**JavaScript project without TDD:**

```bash
python scaffold_project.py ../simple-js-tool --language javascript --no-tdd
```

## What You Get

### Immediate Benefits

1. **Standardized TDD workflow** across all projects
2. **AI agents automatically follow your standards** (no reminders needed)
3. **Slash commands** for common tasks (/dev-feature, /dev-bug)
4. **Consistent project structure**
5. **Testing setup pre-configured**

### Using Shortcuts in New Projects

Once scaffolded, open the project in VS Code and:

**In Copilot Chat** (Ctrl+I):

- Type `/dev-feature` → Expands to full TDD feature prompt
- Type `/dev-bug` → Bug fix workflow with tests
- Type `/dev-test` → Add comprehensive tests

**Copilot Behavior**:

- Automatically reads DEVELOPMENT.md
- Follows TDD by default
- References your testing hierarchy

## Alternative Methods

### Method 1: GitHub Template Repository (Recommended for Teams)

**One-time setup:**

1. Create a repo called `project-template`
2. Run scaffolder once: `python scaffold_project.py project-template`
3. Push to GitHub
4. Mark as template repository (Settings → Template repository)

**For new projects:**

```bash
# GitHub UI: "Use this template" button
# Or CLI:
gh repo create my-new-project --template yourusername/project-template
```

**Pros**: Built into GitHub, easy sharing, version control
**Cons**: Requires GitHub, one template per tech stack

---

### Method 2: Cookiecutter (Python Package)

**Setup:**

```bash
pip install cookiecutter
```

**Create template structure** (one-time):

```
cookiecutter-template/
├── {{cookiecutter.project_name}}/
│   ├── DEVELOPMENT.md
│   ├── .github/COPILOT_INSTRUCTIONS.md
│   └── ...
└── cookiecutter.json
```

**Use:**

```bash
cookiecutter path/to/template
# Prompts for project name, language, etc.
```

**Pros**: Interactive prompts, powerful templating, community support
**Cons**: Requires learning cookiecutter syntax

---

### Method 3: Shell Script (Cross-Platform)

**Create `scaffold.sh` or `scaffold.ps1`:**

```powershell
# scaffold.ps1
param(
    [Parameter(Mandatory=$true)]
    [string]$ProjectPath,
    [string]$Language = "python"
)

$ProjectName = Split-Path -Leaf $ProjectPath
New-Item -ItemType Directory -Force -Path $ProjectPath
New-Item -ItemType Directory -Force -Path "$ProjectPath\.github"
# ... create files ...
```

**Use:**

```powershell
.\scaffold.ps1 -ProjectPath "C:\projects\new-app" -Language python
```

**Pros**: No dependencies, fast, customizable
**Cons**: Harder to maintain templates inline

---

### Method 4: VS Code Extension (Most Integrated)

**Create a custom extension** that adds:

- Command: "Scaffold New Project"
- Webview for configuration
- Template generation

**Pros**: Native VS Code integration, GUI
**Cons**: Requires TypeScript, extension development knowledge

---

### Method 5: Degit (Fastest for Git Templates)

**Setup:**

```bash
npm install -g degit
```

**One-time**: Push template to GitHub

**Use:**

```bash
degit yourusername/project-template my-new-project
cd my-new-project
# Customize as needed
```

**Pros**: Extremely fast, no git history
**Cons**: Requires Node.js, GitHub template

---

## Comparison Table

| Method                       | Setup Time | Ease of Use | Customization | Sharing               |
| ---------------------------- | ---------- | ----------- | ------------- | --------------------- |
| **Python Script** (provided) | Instant    | 5/5         | 5/5           | Share script          |
| **GitHub Template**          | 10 min     | 5/5         | 3/5           | Built-in              |
| **Cookiecutter**             | 30 min     | 4/5         | 5/5           | Community             |
| **Shell Script**             | 20 min     | 4/5         | 4/5           | Share script          |
| **VS Code Extension**        | 2 hours    | 5/5         | 3/5           | Extension marketplace |
| **Degit**                    | 5 min      | 5/5         | 3/5           | GitHub                |

---

## My Recommendation

**For personal use**: Use the **Python script** (provided above)

- Works immediately
- Easy to customize templates
- Cross-platform
- No dependencies beyond Python

**For team/organization**: Create a **GitHub template repository**

- Easy for team members
- Version controlled
- Standard GitHub workflow
- Can combine with scaffolder script

**For public sharing**: **Cookiecutter template**

- Discoverable
- Community standard
- Professional appearance

---

## Customizing the Scaffolder

### Add Your Own Templates

Edit `scaffold_project.py` and modify the `TEMPLATES` dictionary:

```python
TEMPLATES = {
    "your-file.md": """Your template content here

    Variables: {project_name}, {language}, {date}
    """,
    # ... more templates
}
```

### Add New Languages

```python
LANGUAGE_CONFIGS = {
    "rust": {
        "ext": "rs",
        "test_command": "cargo test",
        "import_test_example": """...""",
        # ...
    }
}
```

### Add Project-Specific Files

```python
# In scaffold_project() function, add:
if project_name == "my-special-project":
    create_special_config()
```

---

## Using Across Multiple Machines

### Option 1: Put Script in PATH

**Windows:**

```powershell
# Move to a directory in PATH
Move-Item scaffold_project.py C:\tools\
# Add to PATH if needed
$env:Path += ";C:\tools"

# Use from anywhere:
python scaffold_project.py ~/new-project
```

**Linux/Mac:**

```bash
# Make executable
chmod +x scaffold_project.py

# Move to PATH
sudo mv scaffold_project.py /usr/local/bin/scaffold-project

# Use from anywhere:
scaffold-project ~/new-project
```

### Option 2: Create Alias

```powershell
# PowerShell profile
function Scaffold-Project {
    python C:\path\to\scaffold_project.py $args
}

# Use:
Scaffold-Project ~/new-project
```

### Option 3: Cloud Sync

Store script in Dropbox/OneDrive/Google Drive, symlink to PATH

---

## Next Steps

1. **Try it now:**

   ```bash
   python scaffold_project.py ~/test-project
   cd ~/test-project
   code .
   ```

2. **Test shortcuts:**
   - Open Copilot Chat (Ctrl+I)
   - Type `/dev-feature` and press Tab
   - See the magic!

3. **Customize templates** in `scaffold_project.py` to match your preferences

4. **Share with team** or create GitHub template repository

---

## FAQ

**Q: Can I run this on existing projects?**
A: Yes! It won't overwrite existing files. Safe to add standards to existing projects.

**Q: Do I need to commit the scaffolder to every project?**
A: No! Keep it in one place and run it for new projects.

**Q: Can I customize the templates?**
A: Absolutely! Edit the `TEMPLATES` dictionary in `scaffold_project.py`.

**Q: Does this work offline?**
A: Yes, it's completely local. No internet required.

**Q: What if I want different standards for different project types?**
A: Create multiple template configs or add CLI flags for variations.

---

**Happy scaffolding!**
