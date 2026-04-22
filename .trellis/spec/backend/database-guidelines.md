# Database Guidelines

> This project does not use a database.

---

## Overview

This is a **file-based project**, not a database-backed application.

**No database is used or needed:**
- All data stored in JSON, Markdown, and plain text files
- Configuration in simple file formats (`.developer`, `task.json`, etc.)
- No ORM, no migrations, no SQL

---

## Data Storage Patterns

### JSON for Structured Data

Use Python's `json` module for structured data:

```python
# Write with ensure_ascii=False for proper Unicode
with open(filepath, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

# Read and handle missing files gracefully
try:
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)
except FileNotFoundError:
    return None
```

### Markdown for Human-Readable Content

Generate Markdown programmatically for documentation:

```python
md_content = [f"# {title}", ""]
md_content.append(f"> Generated: {datetime.now()}")
md_content.append("")
md_content.append("## Section")
md_content.append("")

with open(filepath, "w", encoding="utf-8") as f:
    f.write("\n".join(md_content))
```

---

## When Would We Need a Database?

Consider a database only if any of these become true:
- Concurrent writes from multiple processes
- Complex queries across multiple datasets
- Transactional requirements
- Data exceeds file system practicality (~100MB+)

**Until then, files are simpler and work perfectly for this use case.**
