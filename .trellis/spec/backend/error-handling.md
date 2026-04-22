# Error Handling

> How errors are handled in this Python project.

---

## Overview

This project uses **simple, pragmatic error handling** suitable for CLI tools and scripts. Since this is not a user-facing web service, the focus is on:
- Clear error messages for developers
- Graceful degradation where possible
- Fail-fast with informative output

**No custom exception hierarchy** is currently used - standard Python exceptions are sufficient.

---

## Error Types

Use Python's built-in exception types:

| Exception | Use Case |
|-----------|----------|
| `ValueError` | Invalid argument values |
| `TypeError` | Wrong type passed |
| `OSError` / `IOError` | File system operations |
| `Exception` | General catch-all (use sparingly) |

**Do not create custom exception classes** unless you need to catch specific error types across module boundaries.

---

## Error Handling Patterns

### Pattern 1: Try-Except with Print + Return None

For operations that can fail (network, file I/O), catch the exception, print a message, and return `None`.

**Example (`scripts/zread_scraper.py:75-83`):**
```python
def fetch_page(self, url: str) -> str:
    try:
        response = self.session.get(url, timeout=30)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"  Error: {e}")
        return None
```

**When to use:**
- CLI scripts where user should see errors immediately
- Functions where `None` return clearly indicates failure
- Cases where execution can continue despite this failure

### Pattern 2: Fail Silent with Fallback Return

For optional operations, return `None` or empty default without logging.

**Example (`.trellis/scripts/common/paths.py:86-92`):**
```python
try:
    content = dev_file.read_text(encoding="utf-8")
    for line in content.splitlines():
        if line.startswith("name="):
            return line.split("=", 1)[1].strip()
except (OSError, IOError):
    pass
return None
```

### Pattern 3: requests + raise_for_status()

For HTTP operations using the `requests` library:

```python
response = self.session.get(url, timeout=30)
response.raise_for_status()  # Raises exception for 4xx/5xx status codes
return response.text
```

**Always include timeout** - never do `requests.get(url)` without it!

---

## Error Output

### CLI Error Messages

Use the standard print-based colored logging from `common/log.py`:

```python
from common.log import log_error, log_warn

log_error("Failed to read configuration file")
log_warn("Directory already exists, continuing anyway")
```

### Error Message Guidelines

1. **Be specific**: `Failed to read config.json` not `Error occurred`
2. **Include the exception**: `print(f"Error: {e}")`
3. **Context matters**: Prefix with what was being attempted
4. **User-facing messages**: No stack traces unless in debug mode

---

## Common Mistakes

### ❌ Bare `except:`

```python
# BAD - catches KeyboardInterrupt too!
try:
    something()
except:
    pass

# GOOD - catch specific exceptions
try:
    something()
except (OSError, ValueError) as e:
    log_error(f"Failed: {e}")
```

### ❌ Silent Failures Without Indication

```python
# BAD - user has no idea why it didn't work
try:
    write_file(data)
except Exception:
    return None

# GOOD - at least warn the user
try:
    write_file(data)
except Exception as e:
    log_warn(f"Could not write file: {e}")
    return None
```

### ❌ Swallowing Exceptions Too Broadly

```python
# BAD - hides actual bugs
try:
    complex_logic()
except Exception:
    return default_value

# GOOD - only catch what you expect
try:
    file_operation()
except OSError:
    return fallback_value
```

### ❌ Missing Timeouts on Network Calls

```python
# BAD - hangs forever if server doesn't respond
requests.get(url)

# GOOD - always specify timeout
requests.get(url, timeout=30)
```

---

## When to Let Exceptions Propagate

**Let exceptions bubble up** when:
1. It's a programming error (e.g., `TypeError`, `ValueError` from bad args)
2. The caller is better equipped to handle it
3. The error is fatal and should stop execution

**Catch exceptions** when:
1. You can provide a fallback value
2. You need to clean up resources
3. The user needs a friendly message instead of a traceback
4. The script should continue running despite the error
