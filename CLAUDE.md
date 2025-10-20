# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## MCP Tool Usage Rules

**CRITICAL: Always use the appropriate MCP tools for code analysis and file editing in this repository.**

### Code Analysis & Navigation (Serena MCP)

When exploring, reading, or understanding code, **ALWAYS use Serena MCP tools**:

- **`mcp__serena__get_symbols_overview`**: Get high-level overview of symbols in a file before reading details
- **`mcp__serena__find_symbol`**: Find classes, functions, methods by name path (e.g., `ActivityWatchClient/heartbeat`)
  - Use `depth` parameter to retrieve children (e.g., `depth=1` for class methods)
  - Use `include_body=true` only when you need to see implementation
  - Use `substring_matching=true` for partial name matches
  - Use `relative_path` parameter to restrict search to specific files/directories
- **`mcp__serena__find_referencing_symbols`**: Find all places where a symbol is used
- **`mcp__serena__search_for_pattern`**: Search for regex patterns in code (use for non-symbol searches)
  - Set `restrict_search_to_code_files=true` when searching for code symbols
  - Use `paths_include_glob` and `paths_exclude_glob` for targeted searches
- **`mcp__serena__list_dir`**: Explore directory structure
- **`mcp__serena__find_file`**: Find files by name/mask

**DO NOT read entire files unless absolutely necessary.** Use symbolic tools to read only the code you need.

### File Editing (Filesystem Morph MCP)

When editing or writing code files, **ALWAYS prefer `mcp__filesystem-with-morph__edit_file`**:

- **`mcp__filesystem-with-morph__edit_file`**: Primary tool for editing files
  - Shows only changed lines with minimal context
  - Use `// ... existing code ...` placeholders for unchanged blocks
  - Include descriptive hints: `// ... keep auth logic ...`
  - Batch all edits to the same file in one call
  - Provide clear `instruction` parameter describing the change
  - More efficient than legacy Edit tool

**Only use legacy Edit/Write tools if morph tool is unavailable or fails.**

### Symbol-Level Editing (Serena MCP)

For replacing entire functions/classes/methods, use Serena's symbol editing tools:

- **`mcp__serena__replace_symbol_body`**: Replace entire symbol body (function, class, method)
- **`mcp__serena__insert_after_symbol`**: Insert new code after a symbol
- **`mcp__serena__insert_before_symbol`**: Insert new code before a symbol (useful for imports)
- **`mcp__serena__rename_symbol`**: Rename symbols throughout entire codebase

**When to use symbol vs. morph editing:**
- Use symbol tools when replacing/inserting entire functions/classes
- Use morph tool when modifying specific lines within a function

### Workflow Example

```
1. Get overview: mcp__serena__get_symbols_overview("aw-client/aw_client/client.py")
2. Find symbol: mcp__serena__find_symbol(name_path="ActivityWatchClient", depth=1)
3. Read method: mcp__serena__find_symbol(name_path="ActivityWatchClient/heartbeat", include_body=true)
4. Find usages: mcp__serena__find_referencing_symbols(name_path="ActivityWatchClient/heartbeat")
5. Edit file: mcp__filesystem-with-morph__edit_file(path="...", code_edit="...", instruction="...")
```

---

## ActivityWatch Monorepo Architecture

## Overview

ActivityWatch is a modular, open-source time tracking application that records user activity in a privacy-first manner. The monorepo uses git submodules to manage distinct components, with Python-based watchers and clients, two server implementations (Python and Rust), and a Qt-based desktop manager.

**Key Principle:** Data collection happens locally, controlled by the user. The server acts as a storage and query engine while watchers feed activity data through heartbeat APIs.

---

## Repository Structure

The monorepo is organized as a meta-package containing:

```
activitywatch/
├── aw-core/               # Core Python library (shared by all Python modules)
├── aw-client/             # Python client library (used by watchers)
├── aw-server/             # Python server implementation
├── aw-server-rust/        # Rust server implementation (future default)
│   ├── aw-models/         # Data model types
│   ├── aw-datastore/      # SQLite storage layer
│   ├── aw-query/          # Query engine
│   ├── aw-transform/      # Event transformation
│   ├── aw-sync/           # Sync module
│   ├── aw-client-rust/    # Rust client library
│   └── aw-webui/          # Frontend (shared with Python server)
├── aw-qt/                 # Desktop manager (PyQt6, starts modules)
├── aw-watcher-afk/        # AFK/active status watcher
├── aw-watcher-window/     # Active window/app tracker
├── aw-watcher-input/      # Input device tracking (optional)
├── aw-notify/             # Notification system (optional)
├── scripts/               # Build/deployment utilities
└── Makefile               # Bundle-level build coordination
```

**Submodule Status:** All major components except aw-webui are git submodules tracked in `.gitmodules`.

---

## Major Components

### 1. **aw-core** (Python Library)
**Language:** Python 3.8+  
**Type:** Shared library (no CLI)

**Modules:**
- `aw_core/`: Core data models and utilities
  - `models.py`: Event, Bucket data classes
  - `log.py`: Centralized logging infrastructure
  - `config.py`: Configuration management
  - `dirs.py`: Platform-specific data directories
  - `schema.py`: JSON schema definitions
- `aw_datastore/`: Local database abstraction
  - `datastore.py`: Peewee ORM-based database interface
  - `migration.py`: Schema migration system
- `aw_transform/`: Event transformation functions
  - `heartbeats.py`: Merge consecutive identical events
  - `simplify.py`: Remove redundant events
  - `classify.py`: Categorize events
  - Filtering, merging, chunking functions
- `aw_query/`: Query language engine (query2)

**Dependencies:** jsonschema, peewee, iso8601, click, timeslot  
**Build:** Poetry  
**Testing:** pytest with coverage  

**Key Pattern:** All data flows through standardized Event objects with timestamps and durations. The library provides the foundation for all Python components.

---

### 2. **aw-client** (Python Client Library)
**Language:** Python 3.8+  
**Type:** Library (provides CLI for debugging)

**Core Classes:**
- `ActivityWatchClient`: REST API wrapper with retry logic
  - Manages request queuing (persistent SQLite queue)
  - Heartbeat pre-merging (client-side optimization)
  - Automatic server reconnection
- `RequestQueue`: Background thread for async event dispatch
  - Survives server downtime by persisting events to disk
  - Implements exponential backoff retry strategy

**Key Methods:**
- `client.create_bucket()`: Register new data bucket
- `client.heartbeat()`: Send activity event (merged on server)
- `client.query()`: Execute query scripts server-side
- `client.get_events()`: Retrieve historical events

**Dependencies:** aw-core, requests, persist-queue, click  
**Build:** Poetry  
**Testing:** pytest with mock server  

**Key Pattern:** Watchers instantiate a client, call `heartbeat()` to report activity. The client handles offline scenarios transparently through queueing.

---

### 3. **aw-server** (Python Server - Current Default)
**Language:** Python 3.8+  
**Type:** REST API daemon  

**Architecture:**
- Flask REST API with flask-restx for OpenAPI documentation
- Peewee ORM database layer (SQLite or optional backends)
- RESTful endpoints at `/api/0/{resource}`

**Core Modules:**
- `server.py`: Flask app setup and middleware
- `api.py`: Business logic for buckets, events, heartbeats, queries
- `rest.py`: HTTP endpoint definitions
- `settings.py`: Per-device settings storage

**REST API Endpoints:**
- `GET /api/0/info`: Server metadata
- `POST /api/0/buckets/{bucket_id}`: Create bucket
- `POST /api/0/buckets/{bucket_id}/heartbeat`: Send heartbeat (with merge logic)
- `GET /api/0/buckets/{bucket_id}/events`: Retrieve events
- `POST /api/0/query`: Execute query scripts
- `GET/POST /api/0/settings`: Device-level settings

**Dependencies:** aw-core, aw-client, flask, werkzeug  
**Build:** Poetry with webui submodule  
**Testing:** pytest-flask with conftest fixtures  

**Key Pattern:** Heartbeat merging happens server-side—if data matches previous event and within pulsetime window, duration is extended rather than creating new event.

---

### 4. **aw-server-rust** (Rust Server - Future Default)
**Language:** Rust (Edition 2021)  
**Type:** Workspace with multiple crates  

**Crates Architecture:**
- `aw-models/`: Data structures (serde-compatible)
  - Shared types with Python server via JSON
  - Chrono for datetime handling
  
- `aw-datastore/`: SQLite storage layer
  - rusqlite with bundled SQLite
  - MPSC channel-based async requests
  - No dependency on aw-models (compile-time separation)
  
- `aw-query/`: Query execution engine
  - Port of Python query2 language
  - Handles event filtering, merging, transformations
  
- `aw-transform/`: Event transformation utilities
  - Mirrors Python aw_transform functions
  - Heartbeat merging logic
  
- `aw-client-rust/`: Client library for external watchers
  - Thin wrapper around reqwest HTTP client
  
- `aw-sync/`: Synchronization engine
  - Supports decentralized sync to filesystems (Syncthing, Dropbox)
  - Bidirectional merge with conflict resolution
  
- `aw-server/`: Main binary and HTTP server
  - Actix-web or similar async runtime
  - Binary targets: `aw-server`, `aw-sync`

**Build:** Cargo with workspace configuration  
**Testing:** cargo test with coverage tools (grcov, tarpaulin)  
**Packaging:** Supports Linux, macOS; Android via NDK (experimental)  

**Key Pattern:** Designed as drop-in replacement for Python server with better performance. API remains compatible; internal implementation uses Rust for efficiency.

---

### 5. **aw-qt** (Desktop Manager)
**Language:** Python 3.8+ / PyQt6  
**Type:** GUI daemon (system tray application)

**Core Components:**
- `manager.py`: Module discovery and lifecycle management
  - Discovers bundled/system modules via glob patterns
  - Starts/stops subprocesses with autostart logic
  - Monitors for crashes and restarts
  
- `trayicon.py`: System tray UI
  - Status display (running/stopped)
  - Context menu for control
  - Notifications
  
- `main.py`: Entry point and initialization

**Module Discovery:**
1. Search bundled directory (built with PyInstaller)
2. Search system PATH for aw-* executables
3. Prioritize bundled versions over system versions

**Autostart Sequence:**
- Starts aw-server-rust first (if enabled), else aw-server
- Then starts watchers (aw-watcher-window, aw-watcher-afk, etc.)
- Respects --testing flag for test mode

**Dependencies:** aw-core, PyQt6, click  
**Build:** Poetry, PyInstaller for bundling  
**macOS Special:** Uses AppKit to hide Dock icon  

**Key Pattern:** aw-qt acts as orchestrator, not a core component. Users can bypass it and run watchers/server directly.

---

### 6. **aw-watcher-afk** (AFK Status Watcher)
**Language:** Python 3.8+  
**Type:** Daemon (runs continuously)

**Architecture:**
- Platform-specific listeners detect keyboard/mouse activity
- Reports "afk" boolean status via heartbeats

**Platform Implementation:**
- **macOS:** pyobjc-framework-Quartz (global event monitor)
- **Windows:** pynput (low-level input hooks)
- **Linux:** python-xlib (X11 input events, pinned at v0.31 due to CPU issues)

**Core Logic:**
1. Start listener thread
2. On activity, send heartbeat with `{"status": "active"}`
3. After timeout (default: configurable), send `{"status": "afk"}`
4. Use client's queuing for offline resilience

**Dependencies:** aw-client, pynput, platform-specific libraries  
**Bucket Format:** `aw-watcher-afk_{hostname}`  
**Event Data Schema:** `{"status": "active"|"afk"}`  

**Key Pattern:** Simplest watcher—single boolean state that clients use to filter "real" vs idle time.

---

### 7. **aw-watcher-window** (Active Window Watcher)
**Language:** Python 3.8+  
**Type:** Daemon  

**Architecture:**
- Platform-specific hooks capture active window title and process name
- Reports via heartbeats with full window metadata

**Platform Implementation:**
- **macOS:** pyobjc-framework-ApplicationServices (window server)
- **Windows:** pywin32 + WMI (Windows Management Instrumentation)
- **Linux:** python-xlib (X11 window properties, pinned v0.31)

**Heartbeat Data:**
```json
{
  "window": "Browser - Google Chrome",
  "app": "google-chrome",
  "class": "google-chrome"
}
```

**Dependencies:** aw-client, platform-specific libraries (pywin32, pyobjc-*)  
**Bucket Format:** `aw-watcher-window_{hostname}`  

**Key Pattern:** Generates fine-grained events when window changes; heartbeat merging creates long-duration events for single app focus.

---

## Data Flow Architecture

### Write Path: Activity → Server

```
Watcher Process
  └─> aw_client.ActivityWatchClient
      └─> client.heartbeat(bucket_id, event, pulsetime=60)
          ├─> [If queued=True]
          │   ├─> Pre-merge with last_heartbeat locally
          │   └─> Add to RequestQueue (SQLite persist-queue)
          │       └─> RequestQueue thread → server
          │
          └─> [If queued=False]
              └─> REST POST /api/0/buckets/{id}/heartbeat?pulsetime=60
                  └─> Server receives heartbeat
                      ├─> Compare with last event in bucket
                      ├─> If data matches & within pulsetime:
                      │   └─> Extend duration of last event
                      └─> Else:
                          └─> Insert new event

Server Storage
  └─> Datastore (Peewee/rusqlite)
      └─> SQLite database
```

**Key Optimization:** Heartbeat merging reduces storage by 10-100x for continuous activities (e.g., coding for 8 hours = 1 event instead of 480).

---

### Read Path: Query → Results

```
Web UI / Client
  └─> GET /api/0/buckets/{id}/events?start=X&end=Y
  
  Server.api.get_events()
  └─> Datastore.get(start, end)
      └─> SQL query + Event object conversion
          └─> Return to client

Query Execution:
  POST /api/0/query
  Body: {"query": ["events = get_events(...)", "classify(events, ...)"]}
  
  Server.api.query2()
  └─> query2_engine.query(name, query_str, start, end, db)
      ├─> Parse query DSL (chain of transformations)
      ├─> Execute transformations in sequence:
      │   ├─> get_events() → fetch raw events
      │   ├─> filter_keyvals() → filter by data fields
      │   ├─> merge_events_by_keys() → combine similar events
      │   ├─> classify() → categorize (regex rules)
      │   └─> ... (other transforms)
      └─> Return result as list of events
```

---

### Offline Resilience: Request Queueing

```
Network Unavailable
  └─> aw_client tries POST
      └─> Connection fails → requests.ConnectTimeout
          └─> RequestQueue catches exception
              └─> Persist event to disk (~/data/aw-client/queued/*.persistqueue)
                  └─> [User closes app, reboots, etc.]

Network Restored
  └─> RequestQueue.run() loop
      └─> _try_connect() succeeds
          └─> Dequeue persisted events in FIFO order
              └─> POST each to server
                  └─> Server merges/stores normally
```

**File Format:** SQLite database per watcher per mode (production/testing)  
**Persistence:** Survives application restarts indefinitely

---

## Module Dependencies

### Dependency Graph

```
aw-core
  ↑
  └─ aw-client
      ↑
      └─ aw-watcher-afk, aw-watcher-window, aw-notify
      └─ aw-server (imports aw-client for testing)

aw-server
  ├─ aw-core
  ├─ aw-client
  └─ aw-webui (bundled static assets)

aw-qt
  ├─ aw-core (for config/logging)
  └─ (subprocess launches: aw-server, aw-watcher-*)

aw-server-rust (workspace)
  ├─ aw-models (data types)
  ├─ aw-datastore (aw-models, aw-transform)
  ├─ aw-query (aw-models, aw-datastore)
  ├─ aw-sync (aw-models, aw-datastore)
  ├─ aw-transform (aw-models)
  └─ aw-server (all of above)
```

**Key Design:** Python components share aw-core; Rust components are independent ecosystem with Cargo workspace.

---

## Testing Infrastructure

### Python Modules (aw-core, aw-client, aw-server, watchers)

**Test Framework:** pytest with coverage

**Test Locations:**
- `{module}/tests/` - Unit and integration tests
- Coverage reports: XML, HTML, terminal

**Example (aw-core):**
```bash
make test  # pytest tests/ with coverage
make typecheck  # mypy on all modules
make lint  # ruff check
```

**CI Integration:**
- Run via `poetry run make -C {module} test`
- Integration tests also in `scripts/tests/integration_tests.py`

**Coverage Tools:**
- pytest-cov for Python coverage
- Coverage HTML reports in coverage_html/

### Rust Modules (aw-server-rust)

**Test Framework:** cargo test

**Coverage Options:**
- `grcov`: LLVM-based coverage with lcov output
- `tarpaulin`: Alternative coverage tool

**Example:**
```bash
make test  # cargo test
make test-coverage-grcov  # with instrumentation
make coverage-grcov-html  # generate HTML report
```

**CI:**
- Runs for every platform (Linux, macOS, Windows)
- Integration tests test upgrade paths between Python/Rust servers

### Bundle-Level Testing

**Integration Tests:**
```bash
make test  # Run all submodule tests (python)
make test-integration  # Cross-module integration with both servers
```

**Upgrade Tests (.github/workflows/test.yml):**
- Tests migration from old→new server versions
- Combinations: py→py, rust→rust, py→rust, rust→py (not supported)
- Creates bucket, sends heartbeat, validates state persistence

---

## Build Systems

### Bundle-Level Build (Root Makefile)

**Main Targets:**
```makefile
make build          # Install all Python + build Rust (via submodule Makefiles)
make install        # System integration (desktop shortcuts, etc.)
make test           # Run all submodule tests
make typecheck      # mypy on all modules
make lint           # ruff across all modules
make package        # Create distribution bundles
make clean          # Remove build artifacts
```

**Build Order:**
1. Verify setuptools version
2. Check for cargo (if not SKIP_SERVER_RUST=true)
3. For each submodule: `make build`
4. Rebuild aw-client and aw-core (due to dependency issues)

**Conditional Compilation:**
- `SKIP_SERVER_RUST=true`: Skip Rust server (useful for CI without Rust toolchain)
- `AW_EXTRAS=true`: Include aw-notify and aw-watcher-input
- `SKIP_WEBUI=true`: Skip rebuilding web UI

### Python Module Build (Poetry)

**Each module has:** `pyproject.toml` with Poetry configuration

**Build Steps:**
```makefile
make build     # poetry install (installs editable + dependencies)
make test      # pytest tests/
make typecheck  # mypy
make lint      # ruff check
make package    # pyinstaller for bundling (aw-server, aw-qt only)
```

**Packaging:**
- aw-server: Built with PyInstaller as standalone app
- aw-qt: Built with PyInstaller bundle including all modules
- Bundles remove problematic libraries (libdrm, libharfbuzz, etc.)

### Rust Module Build (Cargo)

**Root:** `aw-server-rust/Cargo.toml` (workspace)

**Workspace Members:**
- aw-models (library)
- aw-datastore (library)
- aw-query (library)
- aw-transform (library)
- aw-sync (binary)
- aw-server (binary)
- aw-client-rust (library)

**Build Modes:**
```makefile
make build              # Release build by default
make build RELEASE=false  # Debug build
make aw-server          # Build only server binary
make aw-sync            # Build only sync binary
```

**Versioning:**
- Version set from git tag in CI (if GITHUB_REF_TYPE=tag)
- Converts Python version format (v0.12.0b3 → 0.12.0-beta.3)

**Installation:**
```makefile
make install            # Copy binaries to ~/.local/bin or /usr/local/bin
make install PREFIX=/custom/path  # Custom prefix
```

---

## Architectural Patterns

### 1. **Event-Driven Streaming**
All components use immutable Event objects with timestamp/duration/data. No mutation; new events are created instead. Enables parallel processing and query optimization.

### 2. **Heartbeat-Based Merging**
Watchers send frequent heartbeats (every 1-5 seconds). Server merges consecutive identical heartbeats into longer single events. Client-side pre-merging reduces network traffic.

### 3. **Modular Watchers**
Watchers are independent processes, decoupled from server. Can be enabled/disabled per-user without rebuilding core. Extend by writing new watchers using aw-client library.

### 4. **Resilient Offline-First**
All clients (especially aw-client) persist events to disk when server unavailable. Automatic retry with exponential backoff. User never loses data due to network hiccup.

### 5. **Query Language + Transformation Pipeline**
Server exports query DSL allowing complex data transformations on server-side (more efficient than fetching all events to client). Filters, merges, categorizes in sequence.

### 6. **Dual-Server Strategy**
- **Python server:** Current default, easier to modify, good for development
- **Rust server:** High-performance drop-in replacement for production, same REST API
- CI tests both versions and upgrade paths between them

### 7. **Decentralized Sync (Planned)**
aw-sync module enables syncing database to filesystem (Syncthing, Dropbox), allowing multi-device ActivityWatch without central server. Each device resolves conflicts independently.

### 8. **Platform Abstraction**
Watchers handle OS differences internally (pyobjc for macOS, pywin32 for Windows, python-xlib for Linux). Single watcher package works cross-platform.

---

## Debugging & Development Workflow

### Running Locally

```bash
# 1. Build all modules
make build

# 2. Start server (in terminal 1)
aw-server  # or aw-server-rust

# 3. Start watchers (in terminal 2)
aw-watcher-window
aw-watcher-afk

# 4. View web UI
# Open http://localhost:3000 in browser

# 5. Query via client (in Python REPL)
from aw_client import ActivityWatchClient
client = ActivityWatchClient()
events = client.get_events("aw-watcher-window_hostname")
```

### Testing Individual Modules

```bash
# aw-core: models, datastore, query engine
cd aw-core && make test

# aw-server: REST API
cd aw-server && make test

# aw-server-rust: high-performance server
cd aw-server-rust && make test

# Check for type errors
cd {module} && make typecheck
```

### Common Issues

1. **Server won't start:** Check port 5600 not in use
2. **Watchers not reporting:** Verify server is accessible at localhost:5600
3. **Events not merging:** Check pulsetime parameter (default 60 seconds)
4. **Offline queue stuck:** Delete `~/.local/share/aw-client/queued/*.persistqueue`
5. **Database corrupt:** Delete `~/.local/share/aw-server/` and restart

---

## Key Files for Contributing

| File | Purpose |
|------|---------|
| Makefile | Bundle-level build coordination |
| pyproject.toml | Root Poetry workspace (metadata only) |
| .gitmodules | Submodule definitions |
| aw-core/aw_core/models.py | Core Event/Bucket classes |
| aw-core/aw_datastore/ | Local database layer |
| aw-server/aw_server/api.py | REST API business logic |
| aw-server-rust/aw-server/src/lib.rs | Rust server implementation |
| aw-client/aw_client/client.py | Client library + request queueing |
| aw-qt/aw_qt/manager.py | Module discovery and lifecycle |

---

## Performance Considerations

1. **Heartbeat merging:** Reduces events by 10-100x for continuous activities
2. **Client-side pre-merge:** Reduces network traffic and server load
3. **Request queueing:** Batches events to reduce roundtrips
4. **SQLite with indices:** Fast queries even with millions of events
5. **Rust implementation:** 10-50x faster than Python for large datasets
6. **Query script execution:** Server-side processing faster than fetching all events

---

## Deployment Targets

- **Linux:** AppImage, tarball, native packages
- **macOS:** DMG with code signing and notarization
- **Windows:** Portable ZIP, NSIS installer
- **Android:** Experimental NDK-based build (aw-server-rust only)
- **Docker:** Community-maintained images

---

## Future Directions (In-Progress)

1. **aw-server-rust as default:** Performance gains, simpler deployment
2. **Decentralized sync:** Multi-device support without central server
3. **Mobile clients:** iOS/Android native apps
4. **Plugin system:** WASM-based watchers and transformations
5. **Real-time dashboards:** WebSocket-based live updates

---

## Custom Extensions

### aw-export-daily-report (Custom Module)

**IMPORTANT:** This is a custom extension module that does NOT modify core ActivityWatch code. It's designed to be maintained separately from upstream updates.

**Location:** `activitywatch/aw-export-daily-report/`
**Status:** ✅ Added to `.gitignore` - will not interfere with upstream updates
**Language:** Python 3.8+ (with Poetry)

#### Purpose

Exports unified daily activity reports with:
- **AFK + Window data merged** - Combines activity status with application usage
- **Categorized grouping** - Organizes apps by type (Development, Browsing, Communication, etc.)
- **Detailed breakdowns** - Shows files/windows/activities within each app
- **Multiple formats** - Text (grouped), JSON

#### Architecture

```
aw-export-daily-report/
├── aw_export_daily_report/
│   ├── __init__.py              # Module exports
│   ├── __main__.py              # CLI interface
│   ├── data_fetcher.py          # Queries AW API, unifies AFK + window data
│   ├── report_formatter.py      # Original simple formatters (legacy)
│   └── enhanced_formatter.py    # Grouped/categorized formatter (primary)
├── pyproject.toml               # Poetry configuration
├── README.md                    # Usage documentation
└── test_*.py                    # Test scripts
```

#### Key Components

**1. ActivityDataFetcher** (`data_fetcher.py`)
- Connects to local ActivityWatch server (localhost:5600)
- Discovers window and AFK watcher buckets automatically
- Fetches events for specified date range
- **Merges window events with AFK status** - Key unification logic
- Method: `get_unified_daily_data(date)` returns merged event list

**2. EnhancedReportFormatter** (`enhanced_formatter.py`)
- **Primary formatter** - Use this for clean, categorized reports
- Categorizes apps into: Development, Browsing, Communication, Design, Documentation, Media, AI Tools, Other
- Groups activities by category → app → specific files/windows
- Consolidates duplicate activities (same file visited multiple times)
- Filters AFK time automatically

**Output Format:**
```
DEVELOPMENT (25m - 81.8%)
----------------------------------------------------------------------
  Cursor - 25m
    • node — activitywatch (25m)
    • hyam.ui.brief.md (0m)

BROWSING (3m - 11.5%)
----------------------------------------------------------------------
  Google Chrome - 3m
    • ActivityWatch (2m)
```

#### CLI Commands

```bash
# Navigate to module
cd aw-export-daily-report

# Test connection to ActivityWatch
poetry run aw-export-daily-report test

# Quick statistics
poetry run aw-export-daily-report stats
poetry run aw-export-daily-report stats --date 2025-10-15

# Generate grouped report (RECOMMENDED)
poetry run aw-export-daily-report report --print
poetry run aw-export-daily-report report -o report.txt
poetry run aw-export-daily-report report --format json --print
poetry run aw-export-daily-report report --date 2025-10-15

# Legacy export command (simple format)
poetry run aw-export-daily-report export --format text --print
```

#### Python API Usage

```python
from aw_export_daily_report import ActivityDataFetcher, EnhancedReportFormatter
from datetime import datetime

# Fetch unified data
fetcher = ActivityDataFetcher()
unified_data = fetcher.get_unified_daily_data()  # Today
# OR: unified_data = fetcher.get_unified_daily_data(datetime(2025, 10, 15))

# Generate grouped report
formatter = EnhancedReportFormatter(unified_data)

# Get text report
text_report = formatter.format_as_grouped_text()
print(text_report)

# Get JSON (for programmatic use)
json_report = formatter.format_as_json()

# Get data for web UI (with selection structure)
web_data = formatter.format_as_web_ui_json()

# Export to file
formatter.export_to_file('text', 'daily_report.txt')
formatter.export_to_file('json', 'daily_report.json')
```

#### Category Mapping

Apps are automatically categorized based on this mapping (in `enhanced_formatter.py`):

| Category | Apps |
|----------|------|
| Development | Cursor, VS Code, Terminal, PyCharm, Xcode, etc. |
| Browsing | Chrome, Safari, Firefox, Arc, Brave |
| Communication | Slack, Discord, Zoom, Teams, Mail, Messages |
| Design | Figma, Sketch, Photoshop, Illustrator |
| Documentation | Notion, Obsidian, Word, Google Docs, Pages |
| Media | Spotify, TIDAL, Apple Music, YouTube, VLC |
| AI Tools | Claude, ChatGPT |
| Other | Anything not mapped above |

**To customize:** Edit `CATEGORY_MAP` dictionary in `enhanced_formatter.py`

#### Integration Points

**Data Source:**
- Queries ActivityWatch REST API at `http://localhost:5600/api/0/`
- Requires aw-server (Python or Rust) to be running
- Uses `aw-client` library for API communication

**Dependencies:**
- `aw-core` (^0.5.17) - Core data models
- `aw-client` (^0.5.14) - API client
- `click` - CLI framework

**No Core Modifications:**
- Does NOT modify any ActivityWatch core files
- Uses public REST API only
- Can be updated independently from ActivityWatch updates

#### Updating ActivityWatch (Upstream)

This module is isolated from upstream updates:

```bash
# Update ActivityWatch core
cd /path/to/activitywatch
git pull origin master
git submodule update --remote
make build

# aw-export-daily-report/ remains untouched (in .gitignore)
# No conflicts, no merges needed
```

#### Future Enhancements (Planned)

1. **Web UI** - Browser-based review page for daily activity
2. **Selection Interface** - Check/uncheck activities to include/exclude
3. **Webhook Integration** - Send selected data to N8N/automation tools
4. **Scheduling** - Automated daily report generation
5. **Team Notifications** - Daily reminders with review links

#### Development Notes

- **Python Version:** Use Python 3.12 (avoid 3.14 due to dependency issues)
- **Build:** `poetry install` (automatically uses correct Python version)
- **Testing:** Run test scripts: `poetry run python test_detailed_export.py`
- **Format:** Code follows ActivityWatch conventions (use ruff for linting)

#### Common Issues

1. **Connection Failed:** Ensure aw-server is running on port 5600
2. **No Data Found:** Check date range, verify watchers are running
3. **Import Errors:** Run `poetry install` to ensure dependencies are installed
4. **Python Version:** Use `poetry env use python3.12` if encountering build issues

