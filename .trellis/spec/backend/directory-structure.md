# Directory Structure

> How backend code is organized in this Python project.

---

## Overview

This is a **Python-based skills/project** focused on AI/development workflow tools. Code is organized as standalone scripts with shared common utilities.

**Key characteristics:**
- No monolithic `src/` directory - scripts live at top-level
- Shared utilities in `.trellis/scripts/common/`
- Script-based architecture, not a web framework
- Flat structure for simplicity

---

## Directory Layout

```
repo-root/
├── scripts/                    # Standalone utility scripts
│   ├── zread_scraper.py       # Web scraper for documentation
│   └── requirements.txt        # Script-specific dependencies
│
├── .trellis/                   # Trellis workflow system
│   ├── scripts/
│   │   ├── common/             # Shared utilities (imported across scripts)
│   │   │   ├── paths.py        # Path constants and resolution
│   │   │   ├── log.py          # Colored logging utilities
│   │   │   ├── config.py       # Configuration handling
│   │   │   ├── task_utils.py   # Task domain utilities
│   │   │   └── __init__.py
│   │   ├── task.py             # Main task management CLI
│   │   ├── get_context.py      # Context gathering script
│   │   └── ...
│   ├── spec/                   # Development guidelines
│   │   ├── backend/
│   │   ├── frontend/
│   │   └── guides/
│   └── tasks/                  # Active task directories
│
├── archive/                    # Archived data (e.g., scraped docs)
│   └── nowinandroid/
│       ├── docs/               # Markdown files
│       └── data/               # JSON files
│
├── .claude/                    # Claude-specific configuration
│   ├── commands/               # Custom slash commands
│   ├── agents/                 # Agent instructions
│   └── hooks/                  # Python hook scripts
│
└── .opencode/                  # Opencode/Codex configuration
    ├── commands/               # Custom slash commands
    └── agents/                 # Agent instructions
```

---

## Module Organization

### New Scripts

**Rule:** Standalone executable scripts go in `scripts/` at the repo root.

**Naming:** `snake_case.py` - descriptive, verb-noun pattern:
- `zread_scraper.py` ✓
- `task_utils.py` ✓
- `MyScript.py` ✗

### Shared Utilities

**Rule:** Reusable functions go in `.trellis/scripts/common/`

**Good patterns:**
- Group by domain: `paths.py`, `log.py`, `config.py`, `tasks.py`
- Each module has a single responsibility
- Use `__init__.py` for selective exports if needed

**Example - Good (`.trellis/scripts/common/paths.py`):**
- All path-related constants in one place
- Functions like `get_repo_root()`, `get_tasks_dir()` grouped together
- Easy to find and maintain

**Anti-patterns:**
- Don't put business logic in `common/` - it's for utilities only
- Don't create catch-all `utils.py` files - be specific

---

## File Naming Conventions

| Type | Convention | Example |
|------|------------|---------|
| Python files | `snake_case.py` | `task_utils.py`, `zread_scraper.py` |
| Constants file | `UPPER_SNAKE_CASE` | `DIR_WORKFLOW = ".trellis"` |
| Class names | `PascalCase` | `class ZreadScraper:`, `class Colors:` |
| Function names | `snake_case` | `get_repo_root()`, `log_info()` |
| Markdown docs | `kebab-case.md` | `directory-structure.md` |

---

## Examples

### Well-Organized Script

**`scripts/zread_scraper.py`** - Standalone script pattern:
- Single class `ZreadScraper` encapsulating all behavior
- `main()` function for CLI entry point
- Uses `argparse` for command-line arguments
- Imports from standard library and PyPI packages

### Well-Organized Common Module

**`.trellis/scripts/common/paths.py`** - Shared utility pattern:
- Constants defined at top with comments
- Functions grouped by logical section with `# === Section ===` dividers
- Type annotations on all functions
- Docstrings with Args/Returns documentation
- `if __name__ == "__main__":` block for testing

---

## When to Create New Files

1. **Standalone tool** → Create in `scripts/`
2. **Shared utility function** → Add to existing `.trellis/scripts/common/*.py` by domain
3. **New domain of shared code** → Create new file in `common/`
4. **Hook for IDE** → Put in `.claude/hooks/` or `.opencode/`
5. **Archived data** → Put in `archive/` with subdirectories by project
