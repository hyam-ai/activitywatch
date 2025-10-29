"""
Data fetcher module for ActivityWatch
Queries the AW API and unifies window + AFK data
"""

from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any
from aw_client import ActivityWatchClient
from aw_core.models import Event


class ActivityDataFetcher:
    """Fetches and unifies data from ActivityWatch buckets"""

    def __init__(self, client: ActivityWatchClient = None):
        """Initialize with optional custom client"""
        self.client = client or ActivityWatchClient()

    def get_buckets(self) -> Dict[str, Any]:
        """Get all available buckets"""
        return self.client.get_buckets()

    def find_window_bucket(self) -> str:
        """Find the window watcher bucket for this hostname"""
        buckets = self.get_buckets()
        for bucket_id in buckets:
            if bucket_id.startswith('aw-watcher-window_'):
                return bucket_id
        raise ValueError("No window watcher bucket found")

    def find_afk_bucket(self) -> str:
        """Find the AFK watcher bucket for this hostname"""
        buckets = self.get_buckets()
        for bucket_id in buckets:
            if bucket_id.startswith('aw-watcher-afk_'):
                return bucket_id
        raise ValueError("No AFK watcher bucket found")

    def get_events(self, bucket_id: str, start: datetime, end: datetime) -> List[Event]:
        """Get events from a specific bucket within time range"""
        return self.client.get_events(bucket_id, start=start, end=end)

    def get_daily_data(self, date: datetime = None) -> Dict[str, List[Event]]:
        """
        Get unified data for a specific day

        Args:
            date: The date to fetch data for (defaults to today)

        Returns:
            Dictionary with 'window' and 'afk' event lists
        """
        if date is None:
            date = datetime.now(timezone.utc)

        # Set time range for the full day
        start = datetime(date.year, date.month, date.day, 0, 0, 0, tzinfo=timezone.utc)
        end = start + timedelta(days=1)

        try:
            window_bucket = self.find_window_bucket()
            afk_bucket = self.find_afk_bucket()

            window_events = self.get_events(window_bucket, start, end)
            afk_events = self.get_events(afk_bucket, start, end)

            return {
                'window': window_events,
                'afk': afk_events,
                'date': date,
                'start': start,
                'end': end
            }
        except Exception as e:
            print(f"Error fetching daily data: {e}")
            return {
                'window': [],
                'afk': [],
                'date': date,
                'start': start,
                'end': end,
                'error': str(e)
            }

    def merge_window_with_afk(self, window_events: List[Event], afk_events: List[Event]) -> List[Dict[str, Any]]:
        """
        Merge window and AFK events to create unified activity records

        Each window event is annotated with whether the user was AFK during that time

        Args:
            window_events: List of window watcher events
            afk_events: List of AFK watcher events

        Returns:
            List of unified activity records with format:
            {
                'timestamp': datetime,
                'duration': float (seconds),
                'app': str,
                'title': str,
                'afk': bool,
                'category': str (e.g., 'productive', 'distracted', 'afk')
            }
        """
        unified_events = []

        for window_event in window_events:
            # Find overlapping AFK status
            is_afk = self._is_afk_during_event(window_event, afk_events)

            unified_events.append({
                'timestamp': window_event.timestamp,
                'duration': window_event.duration.total_seconds(),
                'app': window_event.data.get('app', 'Unknown'),
                'title': window_event.data.get('title', 'Unknown'),
                'afk': is_afk,
                'raw_window_event': window_event
            })

        return unified_events

    def _is_afk_during_event(self, window_event: Event, afk_events: List[Event]) -> bool:
        """
        Determine if user was AFK during a window event

        Returns True if majority of the window event overlaps with AFK status
        """
        event_start = window_event.timestamp
        event_end = window_event.timestamp + window_event.duration

        afk_duration = timedelta(0)

        for afk_event in afk_events:
            if afk_event.data.get('status') == 'afk':
                afk_start = afk_event.timestamp
                afk_end = afk_event.timestamp + afk_event.duration

                # Calculate overlap
                overlap_start = max(event_start, afk_start)
                overlap_end = min(event_end, afk_end)

                if overlap_start < overlap_end:
                    afk_duration += (overlap_end - overlap_start)

        # Consider AFK if more than 75% of time was AFK
        return afk_duration > window_event.duration * 0.75

    def get_unified_daily_data(self, date: datetime = None) -> List[Dict[str, Any]]:
        """
        Get unified daily activity data with AFK status merged

        This is the main method to use for generating reports
        """
        daily_data = self.get_daily_data(date)

        if 'error' in daily_data:
            return []

        return self.merge_window_with_afk(
            daily_data['window'],
            daily_data['afk']
        )