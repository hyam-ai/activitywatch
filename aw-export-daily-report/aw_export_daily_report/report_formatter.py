"""
Report formatter module
Converts unified activity data into formatted daily reports
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any
from collections import defaultdict
import json


class DailyReportFormatter:
    """Formats unified activity data into various report formats"""

    def __init__(self, unified_data: List[Dict[str, Any]]):
        """
        Initialize with unified activity data

        Args:
            unified_data: List of unified events from ActivityDataFetcher
        """
        self.data = unified_data

    def calculate_stats(self) -> Dict[str, Any]:
        """
        Calculate summary statistics from unified data

        Returns:
            Dictionary with:
            - total_time: Total tracked time in seconds
            - active_time: Time spent active (not AFK) in seconds
            - afk_time: Time spent AFK in seconds
            - app_breakdown: Time per application
            - top_apps: Top 5 applications by time
            - active_percentage: Percentage of time active
        """
        total_time = 0
        active_time = 0
        afk_time = 0
        app_durations = defaultdict(float)

        for event in self.data:
            duration = event['duration']
            app = event['app']
            is_afk = event['afk']

            total_time += duration
            app_durations[app] += duration

            if is_afk:
                afk_time += duration
            else:
                active_time += duration

        # Sort apps by duration
        sorted_apps = sorted(
            app_durations.items(),
            key=lambda x: x[1],
            reverse=True
        )

        active_percentage = (active_time / total_time * 100) if total_time > 0 else 0

        return {
            'total_time_seconds': total_time,
            'total_time_hours': total_time / 3600,
            'active_time_seconds': active_time,
            'active_time_hours': active_time / 3600,
            'afk_time_seconds': afk_time,
            'afk_time_hours': afk_time / 3600,
            'app_breakdown': dict(app_durations),
            'top_apps': sorted_apps[:5],
            'active_percentage': active_percentage,
            'num_events': len(self.data)
        }

    def format_as_json(self, include_raw_events: bool = False) -> str:
        """
        Format report as JSON

        Args:
            include_raw_events: Whether to include full event details

        Returns:
            JSON string
        """
        stats = self.calculate_stats()

        report = {
            'report_date': datetime.now().isoformat(),
            'statistics': stats,
        }

        if include_raw_events:
            # Convert datetime objects to ISO format for JSON
            events_serializable = []
            for event in self.data:
                event_copy = event.copy()
                if 'timestamp' in event_copy:
                    event_copy['timestamp'] = event_copy['timestamp'].isoformat()
                if 'raw_window_event' in event_copy:
                    del event_copy['raw_window_event']  # Remove non-serializable
                events_serializable.append(event_copy)

            report['events'] = events_serializable

        return json.dumps(report, indent=2)

    def format_as_text_summary(self) -> str:
        """
        Format report as human-readable text summary

        Returns:
            Formatted text report
        """
        stats = self.calculate_stats()

        lines = []
        lines.append("=" * 60)
        lines.append("DAILY ACTIVITY REPORT")
        lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("=" * 60)
        lines.append("")

        # Summary statistics
        lines.append("SUMMARY")
        lines.append("-" * 60)
        lines.append(f"Total Tracked Time:  {self._format_duration(stats['total_time_seconds'])}")
        lines.append(f"Active Time:         {self._format_duration(stats['active_time_seconds'])} ({stats['active_percentage']:.1f}%)")
        lines.append(f"AFK Time:            {self._format_duration(stats['afk_time_seconds'])}")
        lines.append(f"Number of Events:    {stats['num_events']}")
        lines.append("")

        # Top applications
        lines.append("TOP APPLICATIONS")
        lines.append("-" * 60)
        for i, (app, duration) in enumerate(stats['top_apps'], 1):
            percentage = (duration / stats['total_time_seconds'] * 100) if stats['total_time_seconds'] > 0 else 0
            lines.append(f"{i}. {app:30s} {self._format_duration(duration):>15s} ({percentage:>5.1f}%)")
        lines.append("")

        lines.append("=" * 60)

        return "\n".join(lines)

    def format_as_markdown(self) -> str:
        """
        Format report as Markdown for team communication (Slack, email, etc.)

        Returns:
            Markdown formatted report
        """
        stats = self.calculate_stats()

        lines = []
        lines.append("# Daily Activity Report")
        lines.append(f"**Date:** {datetime.now().strftime('%Y-%m-%d')}")
        lines.append("")

        # Summary
        lines.append("## Summary")
        lines.append(f"- **Total Time:** {self._format_duration(stats['total_time_seconds'])}")
        lines.append(f"- **Active Time:** {self._format_duration(stats['active_time_seconds'])} ({stats['active_percentage']:.1f}%)")
        lines.append(f"- **AFK Time:** {self._format_duration(stats['afk_time_seconds'])}")
        lines.append("")

        # Top apps table
        lines.append("## Top Applications")
        lines.append("")
        lines.append("| Rank | Application | Time | % of Total |")
        lines.append("|------|-------------|------|------------|")

        for i, (app, duration) in enumerate(stats['top_apps'], 1):
            percentage = (duration / stats['total_time_seconds'] * 100) if stats['total_time_seconds'] > 0 else 0
            lines.append(f"| {i} | {app} | {self._format_duration(duration)} | {percentage:.1f}% |")

        lines.append("")
        lines.append("---")
        lines.append(f"*Generated by ActivityWatch Export Tool on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")

        return "\n".join(lines)

    def format_as_csv(self) -> str:
        """
        Format events as CSV for spreadsheet import

        Returns:
            CSV string with header
        """
        lines = []
        lines.append("timestamp,duration_seconds,application,title,afk_status")

        for event in self.data:
            timestamp = event['timestamp'].isoformat() if hasattr(event['timestamp'], 'isoformat') else str(event['timestamp'])
            duration = event['duration']
            app = event['app'].replace(',', ';')  # Escape commas
            title = event['title'].replace(',', ';')  # Escape commas
            afk = 'AFK' if event['afk'] else 'Active'

            lines.append(f"{timestamp},{duration},{app},{title},{afk}")

        return "\n".join(lines)

    def _format_duration(self, seconds: float) -> str:
        """Format seconds as human-readable duration (e.g., '2h 15m')"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)

        if hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m"

    def export_to_file(self, format_type: str = 'json', filename: str = None) -> str:
        """
        Export report to file

        Args:
            format_type: One of 'json', 'text', 'markdown', 'csv'
            filename: Optional filename (auto-generated if not provided)

        Returns:
            Path to exported file
        """
        if filename is None:
            date_str = datetime.now().strftime('%Y-%m-%d')
            filename = f"activity_report_{date_str}.{format_type}"

        format_map = {
            'json': self.format_as_json,
            'text': self.format_as_text_summary,
            'txt': self.format_as_text_summary,
            'markdown': self.format_as_markdown,
            'md': self.format_as_markdown,
            'csv': self.format_as_csv
        }

        formatter = format_map.get(format_type.lower())
        if not formatter:
            raise ValueError(f"Unknown format type: {format_type}")

        content = formatter()

        with open(filename, 'w') as f:
            f.write(content)

        return filename
