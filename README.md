# AW HYAM Edition

> **Private fork of ActivityWatch**
> Modified for HYAM's internal time tracking requirements.
> **NOT affiliated with or endorsed by the ActivityWatch project.**

## About This Fork

This is a private fork of [ActivityWatch](https://activitywatch.net) - an open-source, privacy-first automated time tracker.

### HYAM-Specific Modifications

- **Unified virtual environment** - Single venv architecture instead of per-module Poetry venvs
- **Custom daily report module** - `aw-export-daily-report` with web UI and Asana integration
- **Smart activity review** - Categorized grouping, lunch tracking, weekend handling
- **Modified build system** - Custom code signing and bundling for macOS

### Original Project

- **Website:** https://activitywatch.net
- **Repository:** https://github.com/ActivityWatch/activitywatch
- **License:** Mozilla Public License 2.0 (MPLv2)
- **Authors:** Erik Bjäreholt, Johan Bjäreholt, and contributors

---

## What is ActivityWatch?

ActivityWatch is an automated time tracker that:
- Records currently active application and window title
- Tracks browser tabs and URLs
- Detects AFK (away from keyboard) status
- Runs locally with complete data privacy

All data stays on your machine. No cloud tracking, no external servers.

---

## Installation (HYAM Internal)

### Prerequisites
- macOS 10.9+ (tested on macOS 14.6)
- Python 3.9-3.13
- Git with submodule support

### Build from Source

```bash
# Clone repository
git clone <your-hyam-fork-url>
cd activitywatch_edited

# Initialize submodules
git submodule update --init --recursive

# Create unified venv
python3 -m venv venv
source venv/bin/activate

# Build all modules
make build

# Create DMG (macOS)
make dist/ActivityWatch.dmg
```

### Running

```bash
# Launch GUI manager
./dist/ActivityWatch.app/Contents/MacOS/aw-qt

# Or run individual components
aw-server          # Start server (port 5600)
aw-watcher-window  # Track active windows
aw-watcher-afk     # Track AFK status
aw-export-daily-report web  # Custom review UI (port 9999)
```

### Web Interface

- **Main dashboard:** http://localhost:5600
- **Daily review:** http://localhost:9999 (HYAM custom module)

---

## Custom Features (HYAM Edition)

### aw-export-daily-report

Daily activity review module with advanced filtering and categorization.

**Features:**
- Web UI for reviewing daily activities
- Asana task integration (email-based lookup)
- Smart categorization (Development, Browsing, Communication, etc.)
- Date navigation with weekend handling
- Lunch hour detection (excludes 12:00-15:00 AFK)
- Export to JSON for automation

**Usage:**
```bash
cd aw-export-daily-report

# Test connection
poetry run aw-export-daily-report test

# View statistics
poetry run aw-export-daily-report stats --date 2025-10-15

# Generate report
poetry run aw-export-daily-report report --print

# Start web UI (auto-starts with aw-qt)
poetry run aw-export-daily-report web
```

See `aw-export-daily-report/README.md` for details.

---

## Architecture

This fork maintains the same modular architecture as upstream ActivityWatch:

```
AW HYAM Edition
├── aw-server          # REST API & data storage (SQLite)
├── aw-qt              # Desktop manager (system tray)
├── aw-watcher-window  # Active window tracker
├── aw-watcher-afk     # AFK detection
├── aw-webui           # Web dashboard (upstream)
└── aw-export-daily-report  # Custom review module (HYAM)
```

**Data Flow:**
1. Watchers send "heartbeats" to server (localhost:5600)
2. Server merges consecutive identical events
3. Web UI queries server for visualization
4. Custom module adds review & export capabilities

---

## Modifications from Upstream

See `FORK_MODIFICATIONS.md` for comprehensive change documentation.

**Key differences:**
- Unified venv vs. per-module Poetry venvs
- Custom aw-export-daily-report module
- macOS code signing with HYAM Developer ID
- Modified Makefile and PyInstaller specs
- Flask 2.2.5 locked (upstream uses ^2.2)

---

## Development

### Building Individual Modules

```bash
# Build specific module
make --directory=aw-server build
make --directory=aw-qt build

# Run tests
make test

# Lint & typecheck
make lint
make typecheck
```

### Updating from Upstream

```bash
# Pull latest upstream changes
git pull origin master
git submodule update --remote

# Rebuild
make build
```

**Note:** HYAM-specific changes are isolated to avoid merge conflicts.

---

## Documentation

- **Upstream docs:** https://docs.activitywatch.net
- **Fork modifications:** [FORK_MODIFICATIONS.md](FORK_MODIFICATIONS.md)
- **Technical details:** [CUSTOM_MODIFICATIONS.md](CUSTOM_MODIFICATIONS.md)
- **Custom module:** [aw-export-daily-report/README.md](aw-export-daily-report/README.md)

---

## License

This fork maintains the original **Mozilla Public License 2.0 (MPLv2)**.

See [LICENSE.txt](LICENSE.txt) for full license text.

### Compliance
- ✅ Original license preserved
- ✅ Original authors credited
- ✅ Modifications documented
- ✅ Source code available

MPLv2 is a file-level copyleft license. All files retain their original licensing.

---

## Support

### For Upstream Issues
Report bugs related to core ActivityWatch features at:
https://github.com/ActivityWatch/activitywatch/issues

### For HYAM-Specific Issues
Contact internal maintainer: Mehmet Alican Ipek

---

## Acknowledgments

This fork is based on the excellent work of the ActivityWatch team:
- Erik Bjäreholt ([@ErikBjare](https://github.com/ErikBjare))
- Johan Bjäreholt ([@johan-bjareholt](https://github.com/johan-bjareholt))
- And all [contributors](https://github.com/ActivityWatch/activitywatch/graphs/contributors)

**ActivityWatch** is a community-driven project. Support the original:
- Website: https://activitywatch.net
- Forum: https://forum.activitywatch.net
- Documentation: https://docs.activitywatch.net
