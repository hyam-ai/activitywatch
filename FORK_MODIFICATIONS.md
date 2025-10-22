# Fork Modifications

## Legal Notice

This is a private fork of [ActivityWatch](https://github.com/ActivityWatch/activitywatch).

- **Original Project:** ActivityWatch
- **Original Authors:** Erik Bjäreholt, Johan Bjäreholt, and contributors
- **Original License:** Mozilla Public License 2.0 (MPLv2)
- **Fork Maintainer:** HYAM (Mehmet Alican Ipek)
- **Fork Purpose:** Internal time tracking and review workflows

**This fork is NOT endorsed by or affiliated with the ActivityWatch project.**

---

## Changes from Upstream

### Build System
- **Unified venv:** Single root-level venv instead of per-module Poetry venvs
  - Eliminates 22+ individual virtualenvs in `~/Library/Caches/pypoetry/virtualenvs/`
  - All modules share consistent dependency versions at `activitywatch_edited/venv/`
  - Fixes DMG build conflicts and PyInstaller bundling issues

- **Dependency pinning:**
  - Flask locked to ~2.2.5 (prevents Flask 3.x incompatibilities)
  - flask-restx locked to ~1.1.0 (fixes `ModuleNotFoundError: No module named 'flask.scaffold'`)
  - werkzeug constraint ^2.3.3,<3.0

- **Custom module bundling:**
  - Added `aw-export-daily-report` to SUBMODULES in Makefile
  - Bundled in PyInstaller spec with web UI assets and config files
  - Auto-starts with aw-qt manager on launch

### Custom Modules

#### aw-export-daily-report
A custom daily activity review module with Asana integration.

**Features:**
- Web UI on port 9999 for manual activity review
- Merges AFK status with window tracking data
- Categorized activity grouping (Development, Browsing, Communication, etc.)
- Email-based Asana task lookup with GID caching
- Date navigation with smart weekend handling (auto-loads Friday on Mondays)
- Lunch tracking detection (12:00-15:00 AFK exclusion)
- Theme persistence with FOUC prevention
- N8N webhook integration (planned)

**CLI Commands:**
```bash
aw-export-daily-report test      # Test connection
aw-export-daily-report stats     # Quick statistics
aw-export-daily-report report    # Generate grouped report
aw-export-daily-report web       # Start web server (auto-starts with aw-qt)
```

**Integration:**
- Uses ActivityWatch REST API (public endpoints only)
- No modifications to core ActivityWatch modules
- Can be updated independently from upstream

### Code Signing
- macOS app signing with Developer ID: Mehmet Alican Ipek (24FS34VCA3)
- Custom entitlements for notarization (`entitlements.plist`)
- DMG notarization for macOS Gatekeeper compatibility

### Documentation
- Added `CUSTOM_MODIFICATIONS.md` - comprehensive technical documentation
- Added `FORK_MODIFICATIONS.md` (this file) - legal and modification summary
- Removed upstream contribution guidelines (not accepting external PRs)

### Build Artifacts
- DMG filename: `ActivityWatch.dmg` (will be renamed to `AW-HYAM-Edition.dmg`)
- App bundle: `ActivityWatch.app` (will be renamed to `AW-HYAM-Edition.app`)

---

## Upstream Sync Policy

This fork periodically merges upstream changes while preserving HYAM-specific modifications.

**Custom changes are isolated to:**
- `/aw-export-daily-report/` (custom module, not a submodule)
- `/CUSTOM_MODIFICATIONS.md`, `/FORK_MODIFICATIONS.md` (documentation)
- Build scripts (`Makefile`, `aw.spec`, `pyproject.toml`)
- Root-level `.gitignore` (ignores `aw-export-daily-report/` analysis JSONs)

**Submodules remain pointed at upstream:**
- All git submodules in `.gitmodules` reference original ActivityWatch repositories
- Enables easier merging of upstream updates
- Web UI (aw-webui) retains original ActivityWatch branding

---

## Files Modified from Upstream

### Root Directory
- `Makefile` - Added aw-export-daily-report to SUBMODULES
- `aw.spec` - Added custom module bundling, macOS frameworks, web UI assets
- `pyproject.toml` - Flask/flask-restx version locks
- `.gitignore` - Added aw-export-daily-report analysis JSON exclusions

### Submodules (via git submodule commits)
- `aw-server/` - Flask version lock in pyproject.toml
- `aw-qt/` - Added aw-export-daily-report to autostart_modules

### Custom Files (New)
- `/aw-export-daily-report/` - Entire custom module
- `/CUSTOM_MODIFICATIONS.md` - Technical documentation
- `/FORK_MODIFICATIONS.md` - This file

---

## Testing & Validation

✅ Verified working as of last commit:
- `make build` completes successfully
- `make dist/ActivityWatch.dmg` builds without errors
- Custom module bundled and functional in .app
- All watchers start without conflicts
- Web UI accessible at localhost:9999
- Asana integration works with bundled .env token

---

## Known Differences from Upstream

1. **No distributed builds** - This fork uses custom code signing, not upstream CI/CD
2. **macOS-focused** - Primary target is macOS (tested on macOS 14.6)
3. **Custom auto-start** - aw-export-daily-report starts automatically with aw-qt
4. **Bundled secrets** - .env file with Asana token embedded in bundle (not in git)
5. **No aw-server-rust** - Currently using Python server only (may change)

---

## Support

For issues related to:
- **Upstream ActivityWatch features:** Report to https://github.com/ActivityWatch/activitywatch/issues
- **HYAM-specific changes:** Contact internal maintainer (Mehmet Alican Ipek)

---

## License Compliance

This fork complies with the Mozilla Public License 2.0 (MPLv2):
- ✅ Original license preserved in `LICENSE.txt`
- ✅ Original authors credited above
- ✅ Modifications documented in this file
- ✅ Source code available (private repository, MPLv2 allows this)
- ✅ No trademark infringement (renamed to "AW HYAM Edition")

MPLv2 is a file-level copyleft license. Files from upstream retain their original MPLv2 licensing. New files added in this fork (e.g., `/aw-export-daily-report/`) are also licensed under MPLv2 to maintain compatibility.
