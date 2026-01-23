#!/usr/bin/env python3
"""
Project Scaffolder - Automated Development Standards Setup

Creates standardized development documentation and configuration for new projects.
Includes DEVELOPMENT.md, agent instructions, testing setup, and VS Code configuration.

Usage:
    python scaffold_project.py /path/to/new/project [--language python] [--tdd]
    python scaffold_project.py . --language typescript --tdd
    python scaffold_project.py ../my-new-app
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime

# Template configurations
TEMPLATES = {
    "DEVELOPMENT.md": """# Development Guide - {project_name}

**⚠️ AGENTS: Read this file BEFORE implementing any features or bug fixes.**

## Overview

This project follows Test-Driven Development (TDD) practices with a structured approach to testing and feature development. All code must be properly tested before being considered complete.

## Testing Hierarchy

All new features and bug fixes must follow this testing progression:

### 1. Import Test (Smoke Test)
**Purpose**: Verify the module can be imported without errors  
**When**: First test for any new module or major refactor  
**How**:
```{language}
{import_test_example}
```

### 2. Unit Tests
**Purpose**: Test individual functions/methods in isolation  
**When**: After import test passes, test each function separately  
**Coverage Requirements**: 
- All public functions/methods
- Edge cases and boundary conditions
- Error handling and exceptions
- Return values and side effects

### 3. Integration Tests
**Purpose**: Test components working together  
**When**: After unit tests pass, test module interactions  

### 4. End-to-End Tests
**Purpose**: Test complete user workflows  
**When**: After integration tests pass  

## Development Workflow

### Adding a New Feature

1. **Create test file** (if doesn't exist): `tests/test_<feature>.{ext}`
2. **Write import test**: Verify module loads
3. **Write unit tests**: Test each function (TDD - write tests first!)
4. **Implement feature**: Write minimal code to pass tests
5. **Write integration tests**: Test feature with related components
6. **Refactor**: Improve code while keeping tests green
7. **Update documentation**: README, docstrings, etc.

### Fixing a Bug

1. **Create failing test**: Reproduce the bug in a test
2. **Verify test fails**: Confirms bug exists
3. **Fix the bug**: Minimal change to make test pass
4. **Run full test suite**: Ensure no regressions
5. **Add edge case tests**: Prevent similar bugs

### Before Committing

```bash
# Run all tests
{test_command}

# Verify no regressions
# All tests should pass or have documented reasons for skipping
```

## Testing Best Practices

### Do's ✅

- Write tests BEFORE implementation (TDD)
- Test one thing per test function
- Use descriptive test names
- Keep tests fast (mock I/O, external APIs)
- Clean up test artifacts
- Test edge cases and error conditions
- Keep tests independent (no shared state)

### Don'ts ❌

- Don't test implementation details
- Don't write tests after the fact (TDD violation)
- Don't skip tests without documenting why
- Don't use production data
- Don't create interdependent tests
- Don't ignore failing tests
- Don't commit without running tests

## Code Quality Standards

### Before Submitting Code

- [ ] All tests pass
- [ ] New features have tests at all levels
- [ ] Bug fixes have regression tests
- [ ] Code follows existing patterns
- [ ] No commented-out code
- [ ] Docstrings for public functions
- [ ] No hardcoded paths or credentials
- [ ] Error handling is tested

## Git Workflow

### Commit Messages

```
<type>: <short description>

<optional detailed description>

Tests: <test status>
```

**Types**: feat, fix, test, refactor, docs, chore

**Example**:
```
feat: Add user authentication

Implements JWT-based authentication with token refresh.
Includes middleware for protected routes.

Tests: All passing (12 new unit tests, 3 integration tests)
```

---

**Remember**: The goal is maintainable, reliable code. Tests are not a burden - they're your safety net that enables confident refactoring and rapid development.

*Generated: {date}*
""",
    ".github/COPILOT_INSTRUCTIONS.md": """# GitHub Copilot Instructions

**🤖 AI Agents: These are standing orders for all work on this repository.**

## Primary Directive

**ALWAYS read [DEVELOPMENT.md](../DEVELOPMENT.md) before implementing features or fixing bugs.**

## Test-Driven Development (Required)

1. **Import Test** → 2. **Unit Tests** → 3. **Integration Tests** → 4. **E2E Tests**

Never skip steps. Write tests BEFORE implementation code.

## Before Any Code Changes

- [ ] Read DEVELOPMENT.md testing hierarchy
- [ ] Check for existing test patterns
- [ ] Verify test file exists: `tests/test_<module>.{ext}`
- [ ] Plan test coverage for the change

## After Code Changes

- [ ] All new functions have unit tests
- [ ] Integration tests added if component interactions changed
- [ ] All tests pass: `{test_command}`
- [ ] No regressions in existing tests

## Code Standards

- **Style**: Follow existing patterns in the codebase
- **Testing**: Mock external dependencies (files, APIs, time)
- **Documentation**: Docstrings for all public functions
- **Data**: Never use production data in tests

## Testing Patterns

**Import smoke test example:**
```{language}
{import_test_example}
```

**Unit test pattern:**
```{language}
{unit_test_example}
```

## Questions to Ask Before Implementing

1. What tests need to be written?
2. What existing tests might break?
3. Does this change the public API?
4. Are there edge cases to test?
5. Can this be tested in isolation?

## Failure Mode

If you cannot determine the correct approach:
1. Reference DEVELOPMENT.md
2. Look at similar existing tests
3. Ask for clarification rather than guessing

---

**Default assumption**: User wants TDD approach with full test coverage. If unsure, write tests first.

*Generated: {date}*
""",
    ".vscode/copilot-prompts.md": """# GitHub Copilot Chat Prompts

Use `#file:copilot-prompts.md` in chat to reference these prompts quickly.

## Feature Implementation

### /dev-feature
Following DEVELOPMENT.md standards, implement [FEATURE_NAME].

Requirements:
1. Read DEVELOPMENT.md testing hierarchy
2. Create tests/test_[feature].{ext}
3. Write tests FIRST (TDD approach):
   - Import test (smoke test)
   - Unit tests (isolated functions)
   - Integration tests (component interactions)
   - E2E tests (complete workflow)
4. Implement minimal code to pass tests
5. Run full test suite to verify no regressions

### /dev-bug
Following DEVELOPMENT.md bug fix workflow, fix [BUG_DESCRIPTION].

Process:
1. Create a failing test that reproduces the bug
2. Verify test fails
3. Fix the bug with minimal changes
4. Verify test passes
5. Run full test suite (no regressions)
6. Add edge case tests if needed

### /dev-test
Add comprehensive tests for [MODULE/FUNCTION] following DEVELOPMENT.md.

Test progression:
1. Import test (if new module)
2. Unit tests for each function
3. Integration tests for interactions
4. E2E tests for workflows

### /dev-review
Review this implementation against standards in DEVELOPMENT.md.

Checklist:
- [ ] Test coverage (import → unit → integration → E2E)
- [ ] Follows existing patterns
- [ ] All tests passing
- [ ] Docstrings present
- [ ] No hardcoded values
- [ ] Error handling tested

### /tdd
Use Test-Driven Development approach from DEVELOPMENT.md:
1. Write failing test
2. Implement minimal code to pass
3. Refactor while keeping tests green

*Generated: {date}*
""",
    ".vscode/project.code-snippets": """{
  "Copilot: Implement Feature with TDD": {
    "prefix": "/dev-feature",
    "body": [
      "Following DEVELOPMENT.md standards, implement ${{1:feature name}}.",
      "",
      "Requirements:",
      "1. Read DEVELOPMENT.md testing hierarchy",
      "2. Create tests/test_${{2:feature}}.{ext}",
      "3. Write tests FIRST (TDD approach)",
      "4. Implement minimal code to pass tests",
      "5. Run full test suite"
    ],
    "description": "TDD feature implementation"
  },
  "Copilot: Fix Bug with TDD": {
    "prefix": "/dev-bug",
    "body": [
      "Following DEVELOPMENT.md bug fix workflow, fix: ${{1:bug description}}.",
      "",
      "Process:",
      "1. Create failing test",
      "2. Fix the bug",
      "3. Verify all tests pass"
    ],
    "description": "Bug fix workflow"
  },
  "Copilot: Add Tests": {
    "prefix": "/dev-test",
    "body": [
      "Add comprehensive tests for ${{1:module/function}} following DEVELOPMENT.md.",
      "",
      "Test progression: import → unit → integration → E2E"
    ],
    "description": "Add tests"
  }
}
""",
    ".vscode/copilot-settings.json": """{
  "// GitHub Copilot Agent Settings": "Auto-loads development standards",
  
  "github.copilot.chat.codeGeneration.instructions": [
    {
      "text": "Always read and follow DEVELOPMENT.md before implementing features or fixing bugs. Use Test-Driven Development (TDD): import test → unit tests → integration tests → E2E tests. See .github/COPILOT_INSTRUCTIONS.md for quick reference."
    }
  ],
  
  "github.copilot.chat.context.files": [
    "DEVELOPMENT.md",
    ".github/COPILOT_INSTRUCTIONS.md"
  ]
}
""",
    ".gitignore": """# Testing
__pycache__/
*.pyc
*.pyo
*.pyd
.pytest_cache/
.coverage
htmlcov/
*.cover
.hypothesis/

# IDE
.vscode/settings.json
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Environment
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# Build
dist/
build/
*.egg-info/
""",
}


# Language-specific configurations
LANGUAGE_CONFIGS = {
    "python": {
        "ext": "py",
        "test_command": "pytest",
        "import_test_example": """def test_import():
    \"\"\"Verify module imports without errors.\"\"\"
    from myapp import module_name
    assert module_name is not None""",
        "unit_test_example": """def test_function_expected_behavior():
    \"\"\"Test that function does X when given Y.\"\"\"
    # Arrange
    input_val = "test"
    expected = "result"
    
    # Act
    result = my_function(input_val)
    
    # Assert
    assert result == expected""",
        "additional_files": {
            "pytest.ini": """[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = --strict-markers --verbose --cov=src --cov-report=html
""",
            "requirements-dev.txt": """pytest>=7.0.0
pytest-cov>=4.0.0
pytest-mock>=3.10.0
""",
        },
    },
    "typescript": {
        "ext": "ts",
        "test_command": "npm test",
        "import_test_example": """import { describe, it, expect } from 'vitest';
import * as module from './module';

describe('Module Import', () => {
  it('should import without errors', () => {
    expect(module).toBeDefined();
  });
});""",
        "unit_test_example": """import { describe, it, expect } from 'vitest';
import { myFunction } from './myFunction';

describe('myFunction', () => {
  it('should return expected result', () => {
    // Arrange
    const input = 'test';
    const expected = 'result';
    
    // Act
    const result = myFunction(input);
    
    // Assert
    expect(result).toBe(expected);
  });
});""",
        "additional_files": {
            "vitest.config.ts": """import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    globals: true,
    environment: 'node',
    coverage: {
      provider: 'v8',
      reporter: ['text', 'html'],
    },
  },
});
""",
            "tsconfig.json": """{
  "compilerOptions": {
    "target": "ES2020",
    "module": "ESNext",
    "moduleResolution": "node",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true
  },
  "include": ["src/**/*"],
  "exclude": ["node_modules", "dist"]
}
""",
        },
    },
    "javascript": {
        "ext": "js",
        "test_command": "npm test",
        "import_test_example": """const { describe, it, expect } = require('vitest');
const module = require('./module');

describe('Module Import', () => {
  it('should import without errors', () => {
    expect(module).toBeDefined();
  });
});""",
        "unit_test_example": """const { describe, it, expect } = require('vitest');
const { myFunction } = require('./myFunction');

describe('myFunction', () => {
  it('should return expected result', () => {
    const input = 'test';
    const expected = 'result';
    const result = myFunction(input);
    expect(result).toBe(expected);
  });
});""",
    },
}


def scaffold_project(project_path: str, language: str = "python", tdd: bool = True):
    """
    Create development standards structure in a project directory.

    Args:
        project_path: Path to the project directory
        language: Programming language (python, typescript, javascript)
        tdd: Whether to include TDD-specific configurations
    """
    project_path = Path(project_path).resolve()
    project_name = project_path.name

    print(f"🚀 Scaffolding project: {project_name}")
    print(f"   Path: {project_path}")
    print(f"   Language: {language}")
    print(f"   TDD: {'Enabled' if tdd else 'Disabled'}\n")

    # Ensure project directory exists
    project_path.mkdir(parents=True, exist_ok=True)

    # Get language configuration
    lang_config = LANGUAGE_CONFIGS.get(language, LANGUAGE_CONFIGS["python"])

    # Template variables
    template_vars = {
        "project_name": project_name,
        "language": language,
        "ext": lang_config["ext"],
        "test_command": lang_config["test_command"],
        "import_test_example": lang_config["import_test_example"],
        "unit_test_example": lang_config["unit_test_example"],
        "date": datetime.now().strftime("%Y-%m-%d"),
    }

    # Create directory structure
    directories = [
        ".github",
        ".vscode",
        "tests",
        "src" if language in ["typescript", "javascript"] else "",
        "docs",
    ]

    for dir_name in directories:
        if dir_name:
            (project_path / dir_name).mkdir(exist_ok=True)
            print(f"✓ Created directory: {dir_name}/")

    # Create files from templates
    for filename, template in TEMPLATES.items():
        file_path = project_path / filename
        file_path.parent.mkdir(parents=True, exist_ok=True)

        content = template.format(**template_vars)
        file_path.write_text(content, encoding="utf-8")
        print(f"✓ Created: {filename}")

    # Create language-specific files
    if "additional_files" in lang_config:
        for filename, content in lang_config["additional_files"].items():
            file_path = project_path / filename
            file_path.write_text(content, encoding="utf-8")
            print(f"✓ Created: {filename}")

    # Create README if it doesn't exist
    readme_path = project_path / "README.md"
    if not readme_path.exists():
        readme_content = f"""# {project_name}

[Project description here]

## Development

This project follows Test-Driven Development (TDD). See [DEVELOPMENT.md](DEVELOPMENT.md) for complete development standards and testing guidelines.

### Quick Start

```bash
# Install dependencies
{lang_config.get('install_command', '# Add installation steps')}

# Run tests
{lang_config["test_command"]}
```

### For AI Agents

This project has automated development standards:
- Read [DEVELOPMENT.md](DEVELOPMENT.md) before implementing features
- Use TDD: write tests first, then implementation
- Reference `.github/COPILOT_INSTRUCTIONS.md` for quick guidelines

### Contributing

See [DEVELOPMENT.md](DEVELOPMENT.md) for:
- Testing hierarchy (import → unit → integration → E2E)
- Development workflow
- Code quality standards
- Git commit conventions

*Project scaffolded: {datetime.now().strftime("%Y-%m-%d")}*
"""
        readme_path.write_text(readme_content, encoding="utf-8")
        print(f"✓ Created: README.md")

    # Create tests/__init__.py for Python
    if language == "python":
        init_file = project_path / "tests" / "__init__.py"
        init_file.write_text("# Tests package\n", encoding="utf-8")
        print(f"✓ Created: tests/__init__.py")

    print(f"\n✨ Project scaffolding complete!")
    print(f"\n📚 Next steps:")
    print(f"   1. Review DEVELOPMENT.md for development standards")
    print(f"   2. Customize .github/COPILOT_INSTRUCTIONS.md if needed")
    print(f"   3. Start coding with TDD: tests first, then implementation!")
    print(f"   4. Use /dev-feature, /dev-bug shortcuts in Copilot Chat")


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Scaffold a new project with development standards",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scaffold_project.py /path/to/new/project
  python scaffold_project.py . --language typescript
  python scaffold_project.py ../my-app --language python --tdd
        """,
    )

    parser.add_argument(
        "path", help="Path to the project directory (use . for current directory)"
    )
    parser.add_argument(
        "--language",
        "-l",
        choices=["python", "typescript", "javascript"],
        default="python",
        help="Programming language (default: python)",
    )
    parser.add_argument(
        "--tdd",
        action="store_true",
        default=True,
        help="Include TDD configurations (default: True)",
    )
    parser.add_argument(
        "--no-tdd", action="store_false", dest="tdd", help="Exclude TDD configurations"
    )

    args = parser.parse_args()

    try:
        scaffold_project(args.path, args.language, args.tdd)
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
