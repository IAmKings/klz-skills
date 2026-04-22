# Logging Guidelines

> How logging and terminal output is done in this project.

---

## Overview

This project uses **simple print-based terminal output** with ANSI colors. There is no formal `logging` module usage - scripts output directly to stdout for CLI usability.

**Key characteristics:**
- Colored output for different message types
- Structured prefixes like `[INFO]`, `[ERROR]`
- User-friendly messages, not machine-readable logs
- Single source of truth in `.trellis/scripts/common/log.py`

---

## Logging Library

**Use `common.log` utilities** - NOT Python's built-in `logging` module.

```python
from .common.log import log_info, log_success, log_warn, log_error, colored, Colors
```

**Why not the `logging` module?**
- These are CLI tools, not server applications
- Users expect immediate, readable output
- Colors and formatting are more important than log rotation/structured logging
- Simplicity wins for small script projects

---

## Log Levels & Functions

| Function | Color | Use Case | Example |
|----------|-------|----------|---------|
| `log_info()` | Blue | General progress, what's happening | "Starting task creation" |
| `log_success()` | Green | Operations that completed OK | "Task created successfully" |
| `log_warn()` | Yellow | Non-fatal issues, defaults used | "File not found, using default" |
| `log_error()` | Red | Fatal errors, something broke | "Failed to write output file" |
| `print()` | Default | Script output, results, data | "Results: 42 items processed" |

### Example Usage

```python
log_info("Reading configuration...")

if config_file.exists():
    config = read_config(config_file)
    log_success(f"Loaded config with {len(config)} items")
else:
    log_warn("Config not found, using defaults")
    config = DEFAULT_CONFIG

try:
    result = process(config)
except Exception as e:
    log_error(f"Processing failed: {e}")
    return None
```

---

## Color Utilities

### Direct Color Usage

```python
from .common.log import Colors, colored

# Direct color codes
print(f"{Colors.GREEN}Done!{Colors.NC}")

# Helper function
print(colored("Success!", Colors.GREEN))
```

### Available Colors

| Constant | Purpose |
|----------|---------|
| `Colors.RED` | Errors |
| `Colors.GREEN` | Success |
| `Colors.YELLOW` | Warnings |
| `Colors.BLUE` | Info headers |
| `Colors.CYAN` | Accent text |
| `Colors.DIM` | Less important details |
| `Colors.NC` | Reset to default |

---

## What to Log

**Always log:**
- Script start/finish
- Major operations being performed
- Success/failure of key operations
- Errors with what was attempted
- Warnings when defaults are used

**Example flow:**
```
[INFO] Starting documentation scraper
[INFO] Processing page 1/29: Overview
[SUCCESS] Saved overview.md
[WARN] Page 5 skipped - not found
[ERROR] Failed to fetch page 12: timeout
[INFO] Done - 28/29 pages successful
```

---

## What NOT to Print

**Never print or log:**
- Secrets, API keys, passwords
- Personal identifiable information (PII)
- Debug print statements in committed code
- Full tracebacks unless in debug mode
- Excessively verbose output

**For debugging:**
```python
# TEMPORARY - remove before committing!
import pprint
pprint.pprint(data_structure)  # Remove me!
```

---

## Output Guidelines

### Keep it Clean

1. **No trailing whitespace** in output
2. **Consistent indentation** for nested items
3. **Progress indicators** for long operations:
   - `[3/29] Processing...` is better than flooding the terminal

### Formatting

- Use blank lines to separate logical sections
- Use `=` or `-` dividers for major sections:
  ```python
  print("=" * 70)
  print(f"Starting {project_name}")
  print("=" * 70)
  ```

---

## Common Mistakes

### ❌ Debug Print Statements Left in Code

```python
# BAD - don't leave these in!
print("DEBUG HERE!!!")
print(f"value = {x}")
```

### ❌ Silent Failures

```python
# BAD - user doesn't know what went wrong
try:
    process()
except:
    return None

# GOOD - at least warn
try:
    process()
except Exception as e:
    log_warn(f"Could not process: {e}")
    return None
```

### ❌ Using Python Logging Module Unnecessarily

```python
# BAD - overkill for CLI scripts
import logging
logging.basicConfig(level=logging.INFO)
logging.info("Starting...")

# GOOD - simple and colorful
from common.log import log_info
log_info("Starting...")
```

---

## Source of Truth

**All logging utilities are defined in one place:**
`.trellis/scripts/common/log.py`

Never redefine color codes or log functions elsewhere. If you need new functionality (e.g., `log_debug()`), add it to this file.
