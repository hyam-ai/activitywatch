#!/usr/bin/env python3
"""
Test script to show detailed activity data
Run this to see what data we have available for formatting
"""

from aw_export_daily_report import ActivityDataFetcher, DailyReportFormatter
from datetime import datetime
import json

def show_detailed_data():
    print("=" * 70)
    print("DETAILED ACTIVITY DATA TEST")
    print("=" * 70)
    print()

    # Fetch data
    fetcher = ActivityDataFetcher()
    unified_data = fetcher.get_unified_daily_data()

    print(f"Total events found: {len(unified_data)}")
    print()

    # Show first 10 events in detail
    print("SAMPLE EVENTS (first 10):")
    print("-" * 70)

    for i, event in enumerate(unified_data[:10], 1):
        print(f"\nEvent #{i}:")
        print(f"  Time: {event['timestamp']}")
        print(f"  Duration: {event['duration']:.1f}s ({event['duration']/60:.1f}m)")
        print(f"  App: {event['app']}")
        print(f"  Title: {event['title']}")
        print(f"  AFK: {event['afk']}")

    print()
    print("=" * 70)
    print()

    # Group by app and show details
    print("GROUPED BY APPLICATION:")
    print("-" * 70)

    from collections import defaultdict
    app_data = defaultdict(lambda: {'total_duration': 0, 'titles': []})

    for event in unified_data:
        if not event['afk']:  # Only active time
            app = event['app']
            app_data[app]['total_duration'] += event['duration']
            app_data[app]['titles'].append({
                'title': event['title'],
                'duration': event['duration']
            })

    # Sort by duration
    sorted_apps = sorted(app_data.items(), key=lambda x: x[1]['total_duration'], reverse=True)

    for app, data in sorted_apps[:5]:  # Top 5 apps
        total_mins = data['total_duration'] / 60
        print(f"\n{app} - Total: {total_mins:.1f}m")
        print(f"  Window titles/activities:")

        # Show unique titles with aggregated duration
        title_durations = defaultdict(float)
        for item in data['titles']:
            title_durations[item['title']] += item['duration']

        sorted_titles = sorted(title_durations.items(), key=lambda x: x[1], reverse=True)

        for title, duration in sorted_titles[:5]:  # Top 5 titles per app
            mins = duration / 60
            # Truncate long titles
            display_title = title[:60] + "..." if len(title) > 60 else title
            print(f"    • {display_title} ({mins:.1f}m)")

    print()
    print("=" * 70)
    print()

    # Statistics
    formatter = DailyReportFormatter(unified_data)
    stats = formatter.calculate_stats()

    print("STATISTICS:")
    print(f"  Total time: {stats['total_time_hours']:.2f}h")
    print(f"  Active time: {stats['active_time_hours']:.2f}h")
    print(f"  AFK time: {stats['afk_time_hours']:.2f}h")
    print(f"  Active %: {stats['active_percentage']:.1f}%")
    print(f"  Number of events: {stats['num_events']}")


if __name__ == '__main__':
    show_detailed_data()
