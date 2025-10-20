# Custom Modifications to ActivityWatch

**Last Updated:** October 20, 2025
**Modified By:** Ali Can Ipek
**Purpose:** Document all changes made to core ActivityWatch files for custom aw-export-daily-report module integration

---

## Overview

This document tracks modifications made to the ActivityWatch codebase to integrate the custom `aw-export-daily-report` module. These changes enable:
- Unified virtual environment architecture
- Custom module bundling in DMG distribution
- Flask/flask-restx dependency compatibility fixes

---

## Modified Core Files

### 1. **Makefile** (Root Directory)

**File:** `Makefile`

**Changes:**

```diff
- SUBMODULES := aw-core aw-client aw-qt aw-server aw-server-rust aw-watcher-afk aw-watcher-window
+ SUBMODULES := aw-core aw-client aw-qt aw-server aw-server-rust aw-watcher-afk aw-watcher-window aw-export-daily-report
```

**Reason:** Include custom module in build process

```diff
- python3 -m pip install 'setuptools>49.1.1' --user
+ python3 -m pip install 'setuptools>49.1.1'
```

**Reason:** Install setuptools into unified venv instead of user directory

```diff
- python -c "import aw_server; print(aw_server.__version__)"
+ cd aw-server && poetry run python -c "import aw_server; print(aw_server.__version__)"
```

**Reason:** Use Poetry-managed environment for version check

---

### 2. **aw.spec** (PyInstaller Bundling Spec)

**File:** `aw.spec`

**Changes:**

**Added location variable (Line ~93):**
```python
aw_export_daily_report_location = Path("aw-export-daily-report")
```

**Added build analysis (Lines ~175-182):**
```python
aw_export_daily_report_a = build_analysis(
    "aw_export_daily_report",
    aw_export_daily_report_location,
    datas=[
        (aw_export_daily_report_location / "web", "aw_export_daily_report/web"),
        (aw_export_daily_report_location / "config", "aw_export_daily_report/config"),
    ],
)
```

**Reason:** Bundle web UI assets and config files into distribution

**Added to MERGE statement (Line ~194):**
```python
MERGE(
    (aw_server_a, "aw-server", "aw-server"),
    (aw_qt_a, "aw-qt", "aw-qt"),
    (aw_watcher_afk_a, "aw-watcher-afk", "aw-watcher-afk"),
    (aw_watcher_window_a, "aw-watcher-window", "aw-watcher-window"),
    (aw_watcher_input_a, "aw-watcher-input", "aw-watcher-input"),
    (aw_notify_a, "aw-notify", "aw-notify"),
+   (aw_export_daily_report_a, "aw-export-daily-report", "aw-export-daily-report"),
)
```

**Added collection (Line ~218):**
```python
aw_export_daily_report_coll = build_collect(aw_export_daily_report_a, "aw-export-daily-report")
```

**Added to macOS bundle (Line ~228):**
```python
if platform.system() == "Darwin":
    app = BUNDLE(
        awq_coll,
        aws_coll,
        aww_coll,
        awa_coll,
        awi_coll,
        aw_notify_coll,
+       aw_export_daily_report_coll,
        name="ActivityWatch.app",
        ...
    )
```

**Added macOS framework imports (Lines ~148-151):**
```python
aw_watcher_afk_a = build_analysis(
    "aw_watcher_afk",
    awa_location,
    hiddenimports=[
        # ... existing imports ...
+       "Quartz",
+       "Cocoa",
+       "objc",
    ],
)
```

**Reason:** Ensure macOS-specific dependencies are included in bundle

---

### 3. **aw-server/pyproject.toml** (Git Submodule)

**File:** `aw-server/pyproject.toml`

**Changes:**

```diff
[tool.poetry.dependencies]
python = "^3.8"
aw-core = "^0.5.8"
aw-client = "^0.5.8"
- flask = "^2.2"
+ flask = "~2.2.5"
- flask-restx = "^1.0.3"
+ flask-restx = "~1.1.0"
flask-cors = "*"
importlib-metadata = {version = "*", python = "<3.10"}
werkzeug = "^2.3.3"
```

**Reason:** Lock Flask to 2.2.5 to fix flask-restx compatibility issue
- flask-restx 1.2.0+ has breaking changes with Flask 2.3+
- flask-restx removed `flask.scaffold` module causing import errors
- Version ~2.2.5 ensures compatibility without breaking changes

**Issue Reference:**
- GitHub Issue: python-restx/flask-restx#583
- Error: `ModuleNotFoundError: No module named 'flask.scaffold'`
- Solution: Lock to Flask 2.2.5 + flask-restx 1.1.0 combination

---

### 4. **aw-export-daily-report/pyproject.toml** (Custom Module)

**File:** `aw-export-daily-report/pyproject.toml`

**Changes:**

```diff
[tool.poetry.dependencies]
python = "^3.9"
aw-client = "^0.5.14"
aw-core = "^0.5.17"
click = "*"
- flask = "*"
+ flask = "~2.2.5"
flask-cors = "*"
+ werkzeug = "^2.3.3,<3.0"
python-dotenv = "^1.1.1"
```

**Reason:**
- Match Flask version with aw-server to avoid conflicts in unified venv
- Prevent Flask 3.x installation which breaks flask-restx
- Lock werkzeug to 2.x series (3.x incompatible with flask-restx 1.1.0)

---

## Dependency Resolution Strategy

### Problem
Original configuration allowed conflicting Flask versions:
- aw-server: `flask = "^2.2"` → Poetry installed 2.3.3
- aw-export-daily-report: `flask = "*"` → Poetry installed 3.0.3
- Conflict in unified venv caused build failures

### Solution
Locked all modules to compatible versions:
- Flask: `~2.2.5` (locks to 2.2.x series)
- flask-restx: `~1.1.0` (latest compatible with Flask 2.2.x)
- werkzeug: `^2.3.3,<3.0` (excludes 3.x series)

### Poetry Version Syntax
- `^2.2` = Allow 2.2.0 - 2.9.9 (any 2.x ≥ 2.2)
- `~2.2.5` = Allow 2.2.5 - 2.2.9 (only patch updates)
- `<3.0` = Block all 3.x versions

---

## Virtual Environment Architecture

### Before (Multiple Venvs)
```
~/Library/Caches/pypoetry/virtualenvs/
├── aw-core-LLO5Klh7-py3.12/
├── aw-client-mjoLFcCh-py3.12/
├── aw-server-rvm61R2k-py3.12/
├── aw-qt-cfF1cfQU-py3.12/
├── aw-watcher-afk-IWqf4KF3-py3.12/
├── aw-watcher-window-eTY3ZjqG-py3.12/
└── aw-export-daily-report-SPJn_s7g-py3.12/
```

**Issues:**
- Each module had isolated venv with different dependency versions
- PyInstaller couldn't bundle modules with conflicting dependencies
- DMG builds failed or created broken applications

### After (Unified Venv)
```
activitywatch_edited/
└── venv/  # Single shared virtual environment
    ├── bin/
    │   ├── aw-server
    │   ├── aw-watcher-window
    │   ├── aw-watcher-afk
    │   └── aw-export-daily-report
    └── lib/python3.9/site-packages/
        ├── flask-2.2.5/
        ├── flask_restx-1.1.0/
        └── werkzeug-2.3.8/
```

**Benefits:**
- All modules share consistent dependency versions
- PyInstaller bundles all modules successfully
- DMG builds work without conflicts
- Faster builds (shared dependencies)

---

## Build Process Changes

### Standard Build (Development)
```bash
# Create unified venv
python3 -m venv venv
source venv/bin/activate

# Build all modules (installs into shared venv)
make build
```

### DMG Build (Distribution)
```bash
# From project root with venv activated
make dist/ActivityWatch.dmg
```

**Output:**
- `dist/ActivityWatch.app` - macOS application bundle
- `dist/ActivityWatch.dmg` - Distributable installer (includes aw-export-daily-report)

---

## Custom Module Details

### aw-export-daily-report

**Location:** `aw-export-daily-report/`

**Purpose:** Daily activity review with Asana task integration

**Structure:**
```
aw-export-daily-report/
├── aw_export_daily_report/      # Python package
│   ├── __init__.py
│   ├── __main__.py              # CLI entry point
│   ├── web_server.py            # Flask web UI (port 9999)
│   ├── data_fetcher.py
│   ├── report_formatter.py
│   └── config.py
├── web/                          # Web UI assets
│   ├── index.html
│   ├── settings.html
│   └── static/
│       ├── app.js
│       ├── styles.css
│       ├── settings.js
│       ├── settings.css
│       └── hyam-logo-*.png      # Custom branding
├── config/                       # Configuration files
├── pyproject.toml
└── README.md
```

**CLI Commands:**
```bash
aw-export-daily-report test      # Test connection
aw-export-daily-report stats     # Show statistics
aw-export-daily-report export    # Export reports
aw-export-daily-report web       # Start web UI (port 9999)
```

**Bundling:**
- Executable: `aw-export-daily-report` in ActivityWatch.app/Contents/MacOS/
- Web assets: Bundled via aw.spec datas parameter
- Config: Bundled alongside web assets

**Web UI Access (from bundle):**
```bash
/Applications/ActivityWatch.app/Contents/MacOS/aw-export-daily-report web
```

---

## Testing Checklist

### After Making These Changes

- [x] Remove old Poetry venvs: `rm -rf ~/Library/Caches/pypoetry/virtualenvs/aw-*`
- [x] Create unified venv: `python3 -m venv venv && source venv/bin/activate`
- [x] Build all modules: `make build`
- [x] Test import: `python -c "import aw_server; print('OK')"`
- [x] Test custom module: `aw-export-daily-report test`
- [x] Build DMG: `make dist/ActivityWatch.dmg`
- [x] Install DMG: Mount and drag to Applications
- [x] Test bundled app: Open ActivityWatch.app
- [x] Verify watchers running: Check aw-qt menu → Modules
- [x] Test custom module in bundle: `/Applications/ActivityWatch.app/Contents/MacOS/aw-export-daily-report web`

---

## Known Issues & Limitations

### 1. Web UI Not Auto-Started
**Issue:** aw-export-daily-report web UI doesn't auto-start with ActivityWatch.app

**Current State:**
- aw-server, aw-watcher-afk, aw-watcher-window auto-start ✓
- aw-export-daily-report requires manual launch ✗

**Workaround:**
```bash
/Applications/ActivityWatch.app/Contents/MacOS/aw-export-daily-report web
```

**Permanent Fix (Optional):**
Modify `aw-qt/aw_qt/manager.py` to include aw-export-daily-report in module list.
Add menu item in `aw-qt/aw_qt/trayicon.py` to open http://localhost:9999.

**Trade-off:** Requires modifying aw-qt core (complicates upstream updates)

### 2. urllib3 Warning
**Warning Message:**
```
NotOpenSSLWarning: urllib3 v2 only supports OpenSSL 1.1.1+,
currently 'ssl' module is compiled with 'LibreSSL 2.8.3'
```

**Impact:** Non-critical, doesn't affect functionality

**Cause:** macOS uses LibreSSL instead of OpenSSL

**Fix:** Can be ignored or suppress with:
```python
import warnings
warnings.filterwarnings('ignore', category=NotOpenSSLWarning)
```

### 3. Asana Integration Errors
**Error:** 500 Internal Server Error on `/api/asana/tasks`

**Cause:** Missing or invalid Asana API credentials

**Fix:** Configure `.env` file with valid Asana token:
```bash
# aw-export-daily-report/.env
ASANA_ACCESS_TOKEN=your_token_here
```

**Impact:** Web UI loads but Asana task list fails to populate

---

## Maintenance Notes

### Updating ActivityWatch Upstream

When pulling upstream changes:

1. **Check for conflicts:**
```bash
git pull upstream master
git status
```

2. **Files that may conflict:**
- `Makefile` - Re-add aw-export-daily-report to SUBMODULES
- `aw.spec` - Re-add custom module bundling code
- `aw-server/pyproject.toml` - Re-apply Flask version locks

3. **Always test build after update:**
```bash
make clean_all
rm -rf venv
python3 -m venv venv
source venv/bin/activate
make build
make dist/ActivityWatch.dmg
```

### Regenerating Lock Files

If Poetry reports lock file out of sync:

```bash
cd aw-export-daily-report
poetry lock
cd ..
make build
```

### Debugging Build Issues

**Flask import errors:**
```bash
# Check installed versions
pip show flask flask-restx werkzeug

# Should show:
# Flask: 2.2.5
# flask-restx: 1.1.0
# werkzeug: 2.3.8
```

**PyInstaller bundling errors:**
```bash
# Test import before bundling
python -c "import aw_export_daily_report.web_server"
python -c "from aw_export_daily_report.web_server import run_server"
```

---

## Rollback Instructions

If modifications cause issues:

### 1. Revert Core Files
```bash
git checkout HEAD -- Makefile aw.spec pyproject.toml
```

### 2. Remove Custom Module from Build
```bash
# Edit Makefile, remove aw-export-daily-report from SUBMODULES
# Edit aw.spec, remove all aw_export_daily_report references
```

### 3. Rebuild
```bash
make clean_all
rm -rf venv
python3 -m venv venv
source venv/bin/activate
make build
```

---

## References

### Documentation
- ActivityWatch Official Docs: https://docs.activitywatch.net/
- Installing from Source: https://docs.activitywatch.net/en/latest/installing-from-source.html
- Poetry Documentation: https://python-poetry.org/docs/

### Issues & Solutions
- flask-restx Flask 2.3+ Compatibility: https://github.com/python-restx/flask-restx/issues/583
- ActivityWatch Flask Import Error: https://github.com/ActivityWatch/activitywatch/issues/1142
- PyInstaller Bundling Guide: https://pyinstaller.org/en/stable/usage.html

### Git Commits
- Custom module integration: cbc839f (feat: Add comprehensive activity review features)
- Previous stable: 9598c26 (feat: Add HY.AM aw-export-daily-report module)

---

## Contact & Support

**Maintainer:** Ali Can Ipek
**Date Created:** October 20, 2025
**Last Tested:** October 20, 2025
**ActivityWatch Version:** v0.13.2.dev+cbc839f
**Python Version:** 3.9.6
**macOS Version:** Darwin 24.6.0

---

*This document should be updated whenever core file modifications are made.*
