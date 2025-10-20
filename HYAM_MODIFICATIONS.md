# HY.AM Modifications to ActivityWatch

**Fork Date:** 2025-10-20
**Base Version:** ActivityWatch master branch
**Organization:** HY.AM Studios

---

## Modified Files

### 1. Makefile (Line 46)

**Original:**
```makefile
pip install 'setuptools>49.1.1'
```

**Modified:**
```makefile
python3 -m pip install 'setuptools>49.1.1' --user
```

**Reason:**
- Fixes permission issues on macOS
- Uses explicit Python 3 pip module (more reliable)
- Installs to user directory without sudo

**Conflict Risk:** Low (build scripts change infrequently)

**Resolution Strategy:** If upstream modifies this line, evaluate:
- Keep our version if it provides macOS compatibility
- Merge both approaches if upstream version is compatible
- Test installation on team machines before merging

---

## Added Modules

### 1. aw-export-daily-report/

**Purpose:** Daily activity review and export interface

**Location:** `/aw-export-daily-report/`

**Features:**
- Timeline-based activity review UI
- Real-time activity data fetching from ActivityWatch
- Asana task integration
- N8N webhook support for automation
- Export to JSON format
- HY.AM design system implementation

**Dependencies:**
- aw-core (^0.5.17)
- aw-client (^0.5.14)
- Flask for web server
- Python 3.8+

**Conflict Risk:** None (isolated module, no upstream overlap)

**Integration Points:**
- Uses ActivityWatch REST API (`localhost:5600`)
- Independent web server on port 9999
- No modifications to core ActivityWatch code

**Documentation:**
- See `aw-export-daily-report/README.md` for usage
- See `aw-export-daily-report/Update Checklist for 20OCT2025.md` for roadmap

---

## Added Documentation

### 1. CLAUDE.md
- Instructions for Claude AI assistant when working with this codebase
- MCP tool usage rules
- ActivityWatch architecture overview
- Custom module documentation

### 2. HYAM_DESIGN_SYSTEM_COMPLETE.md
- Complete HY.AM Studios design system
- Typography, colors, spacing guidelines
- Component specifications
- Implementation reference for UI consistency

### 3. HY.AM_logo_social_dark.png / HY.AM_logo_social_light.png
- HY.AM Studios branding assets
- Used in aw-export-daily-report UI

---

## Upstream Sync Strategy

### Regular Sync Schedule
- Review official ActivityWatch updates **monthly**
- Fetch upstream: `git fetch upstream`
- Review changes: `git log upstream/master`
- Merge when safe: `git merge upstream/master`

### Pre-Merge Checklist
- [ ] Review upstream CHANGELOG
- [ ] Check if Makefile was modified
- [ ] Test `aw-export-daily-report` after merge
- [ ] Verify submodules still work
- [ ] Run build: `make build`
- [ ] Test daily review UI: `poetry run python -m aw_export_daily_report`

### Conflict Resolution Priority
1. **Core ActivityWatch code:** Always use upstream version
2. **Makefile:** Evaluate case-by-case, prefer our version if needed for team
3. **aw-export-daily-report/:** Keep ours (no conflicts expected)
4. **Documentation:** Keep ours

---

## Team Installation Notes

### Fresh Install
```bash
# Clone HY.AM fork
git clone https://github.com/HYAM-ORG/activitywatch.git
cd activitywatch

# Initialize submodules
git submodule update --init --recursive

# Build ActivityWatch
make build

# Install aw-export-daily-report
cd aw-export-daily-report
poetry install
poetry run aw-export-daily-report test
```

### If Makefile Pip Install Fails
The Makefile has been modified to use `python3 -m pip install --user`. If issues persist:

```bash
# Manual setuptools install
python3 -m pip install 'setuptools>49.1.1' --user

# Then continue build
make build
```

---

## Maintenance Contacts

**Primary Maintainer:** Ali Can İpek
**Repository:** https://github.com/HYAM-ORG/activitywatch (after transfer)
**Issues:** Report in fork repository, not upstream
**Upstream:** https://github.com/ActivityWatch/activitywatch

---

## Version History

| Date | Version | Changes |
|------|---------|---------|
| 2025-10-20 | 1.0.0 | Initial fork with aw-export-daily-report module |

---

## Future Considerations

### Potential Upstream Contributions
If `aw-export-daily-report` proves valuable, consider:
- Proposing as official ActivityWatch plugin
- Submitting PR to upstream (requires refactoring for generalization)
- Publishing as standalone ActivityWatch extension

### Maintenance Notes
- Keep `aw-export-daily-report` as self-contained as possible
- Minimize modifications to core ActivityWatch files
- Document all changes in this file
- Test thoroughly before merging upstream updates
