# ActivityWatch Daily Report Exporter

Custom module for exporting timeline-based daily activity reports from ActivityWatch with web UI for review and submission.

## Features

- **Timeline View**: Activity organized in time blocks showing main and supporting activities
- **Web UI**: Browser-based review interface with selection capabilities
- **Webhook Integration**: Submit selected activities to external systems (N8N, Asana)
- **AFK Filtering**: Automatically filters out idle time
- **Asana Integration**: Fetch and display tasks for activity mapping
- **Smart Activity Grouping**: Merges consecutive similar activities into sessions

## Installation

```bash
cd aw-export-daily-report
poetry install
```

## Usage

### Start Web Server (Primary Interface)

```bash
poetry run aw-export-daily-report web
```

Open browser to `http://localhost:9999` to review and submit activities.

### Test Connection

```bash
poetry run aw-export-daily-report test
```

### View Quick Stats

```bash
# Today's stats
poetry run aw-export-daily-report stats

# Specific date
poetry run aw-export-daily-report stats --date 2025-10-15
```

### Export Reports (CLI)

```bash
# Export today's report as text
poetry run aw-export-daily-report export

# Export as markdown and print to terminal
poetry run aw-export-daily-report export --format markdown --print

# Export specific date as JSON
poetry run aw-export-daily-report export --date 2025-10-15 --format json -o report.json
```

## Python API

```python
from aw_export_daily_report import ActivityDataFetcher
from aw_export_daily_report.timeline_analyzer import TimelineAnalyzer
from datetime import datetime

# Fetch unified data (AFK + window merged)
fetcher = ActivityDataFetcher()
unified_data = fetcher.get_unified_daily_data()

# Generate timeline
analyzer = TimelineAnalyzer(unified_data)
timeline = analyzer.analyze()

# Access timeline blocks
for block in timeline['timeline_blocks']:
    print(f"{block['start_time']} - {block['main_activity']['app']}")
```

## Architecture

This module does NOT modify any ActivityWatch core code:

```
activitywatch/
├── aw-core/              # Untouched
├── aw-server/            # Untouched
├── aw-watcher-*/         # Untouched
│
└── aw-export-daily-report/  # Custom module
    ├── aw_export_daily_report/
    │   ├── data_fetcher.py       # Queries AW API, merges AFK + window
    │   ├── timeline_analyzer.py  # Creates timeline blocks
    │   ├── web_server.py         # Flask API + web UI
    │   └── __main__.py           # CLI interface
    ├── web/
    │   ├── index.html            # Review UI
    │   └── static/               # CSS/JS
    └── analysis/                 # Submitted activity exports
```

## Data Flow

```
ActivityWatch → data_fetcher.py → timeline_analyzer.py → Web UI → Webhook (N8N)
```

## License

MIT
