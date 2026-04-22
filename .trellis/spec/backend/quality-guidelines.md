# Quality Guidelines

> Code quality standards for backend Python development.

---

## Overview

This is a Python script-focused project. Quality standards prioritize readability, maintainability, and correct type usage.

**Core principles:**
1. **Explicit is better than implicit** - type hints everywhere
2. **Simple is better than complex** - avoid over-engineering
3. **Readability counts** - code is read more than written
4. **Practicality beats purity** - exceptions to rules are OK if documented

---

## Python Version & Syntax

**Minimum Python: 3.10**

Use these modern features:
- `from __future__ import annotations` - allows forward references
- Type union syntax: `Path | None` instead of `Optional[Path]`
- `pathlib.Path` for ALL path operations (not `os.path`)
- f-strings for string formatting
- walrus operator `:=` where it improves readability

---

## Required Patterns

### Type Hints on Everything

**All functions must have type annotations:**

```python
# GOOD
def get_repo_root(start_path: Path | None = None) -> Path:
    ...

def set_current_task(task_path: str, repo_root: Path | None = None) -> bool:
    ...

# BAD - missing types
def get_config(filename):
    ...
```

### Use pathlib, not os.path

```python
# GOOD
from pathlib import Path
output_dir = Path("archive") / project_name
output_dir.mkdir(parents=True, exist_ok=True)

# BAD
import os
output_dir = os.path.join("archive", project_name)
os.makedirs(output_dir, exist_ok=True)
```

### Module Docstrings

```python
#!/usr/bin/env python3
"""
Single-line summary.

Longer description of what this module does and key
functions or classes it provides.
"""
```

### Section Dividers in Large Files

For files with multiple logical sections:

```python
# =============================================================================
# Repository Root
# =============================================================================

def get_repo_root(...) -> Path:
    ...

# =============================================================================
# Developer
# =============================================================================

def get_developer(...) -> str | None:
    ...
```

### Return Early Pattern

```python
# GOOD - reduce indentation, clear flow
def get_developer(repo_root: Path | None = None) -> str | None:
    if repo_root is None:
        repo_root = get_repo_root()

    dev_file = repo_root / ".developer"
    if not dev_file.is_file():
        return None

    try:
        content = dev_file.read_text(encoding="utf-8")
        for line in content.splitlines():
            if line.startswith("name="):
                return line.split("=", 1)[1].strip()
    except (OSError, IOError):
        pass

    return None
```

---

## Forbidden Patterns

### ❌ Wildcard Imports

```python
# BAD
from common import *

# GOOD
from common.paths import get_repo_root, get_tasks_dir
```

### ❌ Catch-All `utils.py` Files

```python
# BAD - one big messy file
common/utils.py

# GOOD - split by domain
common/paths.py
common/log.py
common/config.py
common/tasks.py
```

### ❌ Mutable Default Arguments

```python
# BAD - default list/dict persists across calls!
def add_item(item, items=[]):
    items.append(item)
    return items

# GOOD
def add_item(item, items=None):
    if items is None:
        items = []
    items.append(item)
    return items
```

### ❌ `os.path` Instead of `pathlib`

```python
# BAD - legacy API
os.path.join(a, b)
os.makedirs(path, exist_ok=True)
os.path.isfile(path)

# GOOD - modern, object-oriented
Path(a) / b
Path(path).mkdir(parents=True, exist_ok=True)
Path(path).is_file()
```

### ❌ Bare `except:`

```python
# BAD - catches KeyboardInterrupt too!
try:
    something()
except:
    pass

# GOOD
try:
    something()
except (OSError, ValueError) as e:
    log_error(f"Failed: {e}")
```

### ❌ Print Debug Statements Left in Code

```python
# BAD - remove before committing!
print("HERE!!!")
print(f"x = {x}")
```

---

## Code Style

### Formatting
- 4-space indentation (no tabs)
- Max line length: ~100 chars (pragmatic, not strict)
- Blank lines between functions and logical sections
- One import per line

### Imports Ordering

```python
# 1. Future imports (first!)
from __future__ import annotations

# 2. Standard library
import json
import re
from pathlib import Path
from typing import Dict, List

# 3. Third-party
import requests

# 4. Local
from .common.log import log_error
```

### Function Names
- Verb-first: `get_`, `set_`, `create_`, `validate_`, `process_`
- `get_` for retrievals that might fail (returns `None` or default)
- `is_` / `has_` for boolean checks: `is_file()`, `has_current_task()`

---

## Testing Requirements

**Currently: No formal test suite**

**Testing principles:**
- Scripts should have `if __name__ == "__main__":` blocks that demo usage
- Edge cases should be handled gracefully (return None, not crash)
- Fail fast on invalid inputs

**Future recommendations:**
- Add pytest for core utilities in `common/`
- Test error handling paths specifically

---

## Code Review Checklist

**Reviewers should verify:**

1. **Type hints present** on all functions
2. **`pathlib` used** instead of `os.path`
3. **No bare `except:`** clauses
4. **No debug print statements** left in code
5. **Section dividers** used in files > 100 lines
6. **Error messages are useful** - user knows what went wrong
7. **File encoding specified** when opening files: `encoding="utf-8"`

```python
# GOOD - specify encoding!
with open(filepath, "w", encoding="utf-8") as f:
    ...

# BAD - platform-dependent default encoding
with open(filepath, "w") as f:
    ...
```

---

## Common Bugs & Lessons Learned

### 1. Path Resolution Across Platforms
- Always use `Path.resolve()` for absolute paths
- Use `Path.as_posix()` when storing paths as strings for cross-platform

### 2. Encoding Issues
- Windows default encoding is not UTF-8
- Always specify `encoding="utf-8"` when opening files

### 3. Circular Imports
- Move imports inside functions if needed (lazy import pattern)
- Example in `paths.py`: `from .config import get_spec_base` inside the function

### 4. None vs Empty String
- Use `is None` check, not truthiness, for optional strings that might be empty

```python
# GOOD - correct check
if normalized is None or not normalized:
    return ""

# BAD - empty string would be treated same as None
if not normalized:
    return ""
```
