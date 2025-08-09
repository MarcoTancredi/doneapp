# PROTOCOL.md — Patch Application Protocol

This repository uses a **structured patch system** for file operations. Any AI or developer can apply changes by following this exact format. All patches are processed by `tools/apply_changes.py`.

> **CRITICAL**: Follow this format exactly. Any deviation will cause patch application to fail.

---

## PATCH FORMAT OVERVIEW

Each patch can contain multiple actions in a single block. Available actions:

1. **#Action System** - Execute system commands
2. **#Action DeleteFile** - Delete files/directories  
3. **#Action CreateFile** - Create complete files
4. **#Action DeleteText** - Remove text sections from files
5. **#Action InsertText** - Insert text at specific locations
6. **#Action ModifyText** - Replace text sections in files

**Format Rules:**
- Each action starts with `#Action [ActionName]`
- Each action ends with `#END Action [ActionName]` or EOF
- Context lines (`#BeforeToKeep`, `#AfterToKeep`) are **NEVER** modified
- Use ASCII characters only (no curly quotes, em-dashes)
- UTF-8 encoding with LF line endings

---

## ACTION 1: #Action System

Execute system commands (restart server, git operations, etc.)
#Action System
Local: [working_directory_path]
[command_line_1]
[command_line_2]
[command_line_n]
#END Action System

**Example:**
#Action System
Local: .
git add .
git commit -m "Applied patches"
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
#END Action System

---

## ACTION 2: #Action DeleteFile

Delete files or directories. Non-existent files generate warnings, not errors.
#Action DeleteFile
Local: [file_or_directory_path_1]
Local: [file_or_directory_path_2]
Local: [file_or_directory_path_n]
#END Action DeleteFile

**Example:**
#Action DeleteFile
Local: temp/cache.tmp
Local: logs/old_logs/
Local: backup_file.bak
#END Action DeleteFile

---

## ACTION 3: #Action CreateFile

Create complete files (overwrites if exists).
#Action CreateFile
Local: [file_path]
[complete_file_content]
[line_2]
[line_n]
#END Action CreateFile

**Example:**
#Action CreateFile
Local: config/settings.py
DEBUG = True
DATABASE_URL = "sqlite:///app.db"
SECRET_KEY = "your-secret-key"
#END Action CreateFile

---

## ACTION 4: #Action DeleteText

Remove text sections between two context markers. Context lines are preserved.
#Action DeleteText
Local: [file_path]
#BeforeToKeep
[at_least_3_context_lines]
[that_precede_deletion_area]
[and_will_remain_unchanged]
#EndBeforeToKeep
#AfterToKeep
[at_least_3_context_lines]
[that_follow_deletion_area]
[and_will_remain_unchanged]
#EndAfterToKeep
#END Action DeleteText

**Logic:** Everything BETWEEN `#BeforeToKeep...#EndBeforeToKeep` and `#AfterToKeep...#EndAfterToKeep` sections gets deleted.

**Example:**
#Action DeleteText
Local: app/main.py
#BeforeToKeep
from fastapi import FastAPI
app = FastAPI()
#EndBeforeToKeep
#AfterToKeep
@app.get("/health")
def health_check():
#EndAfterToKeep
#END Action DeleteText

---

## ACTION 5: #Action InsertText

Insert text at a specific location between context markers.
#Action InsertText
Local: [file_path]
#BeforeToKeep
[at_least_3_context_lines]
[that_precede_insertion_point]
[and_will_remain_unchanged]
#EndBeforeToKeep
#AfterToKeep
[at_least_3_context_lines]
[that_follow_insertion_point]
[and_will_remain_unchanged]
#EndAfterToKeep
#TextToInsert
[content_to_insert]
[line_2]
[line_n]
#EndTextToInsert
#END Action InsertText

**Logic:** `#TextToInsert...#EndTextToInsert` content gets inserted BETWEEN the context sections.

**Example:**
#Action InsertText
Local: app/main.py
#BeforeToKeep
from fastapi import FastAPI
app = FastAPI()
#EndBeforeToKeep
#AfterToKeep
@app.get("/health")
def health_check():
#EndAfterToKeep
#TextToInsert
@app.get("/status")
def get_status():
return {"status": "running"}
#EndTextToInsert
#END Action InsertText

---

## ACTION 6: #Action ModifyText

Replace text sections between context markers with new content. Supports multiple modifications in single action.
#Action ModifyText
Local: [file_path]
#BeforeToKeep
[at_least_3_context_lines]
[that_precede_modification_area]
[and_will_remain_unchanged]
#EndBeforeToKeep
#AfterToKeep
[at_least_3_context_lines]
[that_follow_modification_area]
[and_will_remain_unchanged]
#EndAfterToKeep
#TextToInsert
[replacement_content]
[line_2]
[line_n]
#EndTextToInsert
[optional: repeat #BeforeToKeep...#EndTextToInsert for additional modifications in same file]
#END Action ModifyText

**Logic:** Everything BETWEEN `#BeforeToKeep...#EndBeforeToKeep` and `#AfterToKeep...#EndAfterToKeep` sections gets replaced with `#TextToInsert...#EndTextToInsert` content.

**Single Modification Example:**
#Action ModifyText
Local: app/templates/login.html
#BeforeToKeep
<form id="loginForm" method="post">
    <div class="form-group">
        <label for="email">Email</label>
#EndBeforeToKeep
#AfterToKeep
    </div>
    <div class="form-group">
        <label for="password">Password</label>
#EndAfterToKeep
#TextToInsert
        <label for="login">Email or Username</label>
        <input type="text" id="login" name="login" class="form-control" required>
    </div>
    <div class="form-group">
        <label style="display: flex; align-items: center;">
            <input type="checkbox" name="remember_me" style="margin-right: 10px;">
            Keep me logged in
        </label>
#EndTextToInsert
#END Action ModifyText
```
Multiple Modifications Example:
#Action ModifyText
Local: app/main.py
#BeforeToKeep
from fastapi import FastAPI
app = FastAPI()
#EndBeforeToKeep
#AfterToKeep
@app.get("/")
def read_root():
#EndAfterToKeep
#TextToInsert
@app.get("/health")
def health_check():
    return {"status": "healthy"}

#EndTextToInsert
#BeforeToKeep
def read_root():
    return {"Hello": "World"}
#EndBeforeToKeep
#AfterToKeep

if __name__ == "__main__":
#EndAfterToKeep
#TextToInsert
    return {"status": "active", "version": "1.0"}

@app.get("/api/status")
def api_status():
    return {"api": "running", "timestamp": "2024-01-01T00:00:00Z"}

#EndTextToInsert
#END Action ModifyText

BACKUP SYSTEM

Backups created in .backups/YYYY-MM-DD_HHMMSS/ before first file modification
One backup per file per patch session
Original file structure preserved in backup directory


ERROR HANDLING

File not found: Warning for DeleteFile, Error for others
Context not found: Error with detailed location info
Parse errors: Error with line number and expected format
System command failure: Error with exit code and output


USAGE EXAMPLES
Multiple operations in one patch:
#Action DeleteFile
Local: temp/old_cache.tmp
#END Action DeleteFile

#Action CreateFile
Local: config/new_config.json
{"debug": true, "port": 8000}
#END Action CreateFile

#Action ModifyText
Local: app/main.py
#BeforeToKeep
app = FastAPI()

@app.get("/")
#EndBeforeToKeep
#AfterToKeep
def read_root():
    return {"Hello": "World"}
#EndAfterToKeep
#TextToInsert
def read_root():
    return {"status": "active", "version": "1.0"}
#EndTextToInsert
#END Action ModifyText

#Action System
Local: .
git add .
git commit -m "Updated configuration and endpoints"
#END Action System

VALIDATION RULES

Each #Action must have corresponding #END Action or reach EOF
Context sections (#BeforeToKeep, #AfterToKeep) need minimum 3 lines
Context lines must exist exactly in target file
File paths must be relative to project root
System commands executed in specified Local: directory
All delimiter sections must be properly closed with corresponding #End... markers

This protocol ensures deterministic, repeatable file operations with complete audit trail through backups.