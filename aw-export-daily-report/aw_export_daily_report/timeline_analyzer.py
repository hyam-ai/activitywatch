"""
Timeline-based activity analyzer
Groups activities into 15-minute blocks to show chronological work context
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any
from collections import defaultdict


class TimelineAnalyzer:
    """Analyzes activities in 15-minute blocks to identify main vs supporting work"""

    BLOCK_SIZE_MINUTES = 15
    MIN_ACTIVITY_SECONDS = 10  # Filter noise

    # Apps that should be grouped by window title (browsers and editors)
    BROWSERS = {'Google Chrome', 'Comet', 'Safari', 'Firefox', 'Arc', 'Brave', 'Microsoft Edge'}
    EDITORS = {'Cursor', 'Code', 'Visual Studio Code', 'Xcode', 'PyCharm', 'IntelliJ IDEA', 'Sublime Text'}

    def __init__(self, events: List[Dict[str, Any]]):
        self.events = events
        self.timeline = []

    def analyze(self) -> Dict[str, Any]:
        """
        Main entry point

        Returns:
            Timeline structure with blocks showing main and supporting activities
        """
        if not self.events:
            return {"timeline_blocks": [], "total_active_time": 0}

        # 1. Filter active events only
        active_events = self._filter_active_events()

        if not active_events:
            return {"timeline_blocks": [], "total_active_time": 0}

        # 2. Get day boundaries
        day_start, day_end = self._get_day_boundaries(active_events)

        # 3. Create 15-minute blocks
        raw_blocks = self._create_time_blocks(day_start, day_end, active_events)

        # 4. Merge consecutive blocks with same main activity
        merged_blocks = self._merge_consecutive_blocks(raw_blocks)

        # 5. Calculate total time
        total_time = sum(block['duration'] for block in merged_blocks)

        return {
            "date": day_start.strftime('%Y-%m-%d'),
            "timeline_blocks": merged_blocks,
            "raw_15min_blocks": raw_blocks,  # Include raw blocks for debugging
            "total_active_time": total_time
        }

    def _filter_active_events(self) -> List[Dict[str, Any]]:
        """Filter out AFK periods and very short activities"""
        return [
            event for event in self.events
            if not event.get('afk', False)
            and float(event.get('duration', 0)) >= self.MIN_ACTIVITY_SECONDS
        ]

    def _extract_primary_window(self, app: str, title: str) -> str:
        """
        Extract the primary/meaningful part of a window title

        For browsers: Extract website + page name (e.g., "Timely - Hours")
        For editors: Extract project/file name
        """
        if not title:
            return app

        # For browsers, extract website and page name
        if app in self.BROWSERS:
            # Remove common browser suffixes
            for suffix in [' - Google Chrome', ' - Comet', ' - Safari', ' - Firefox', ' - Arc', ' - Brave', ' - Microsoft Edge']:
                title = title.replace(suffix, '')

            # Pattern 1: "Page - Website" (e.g., "Hours - Timely")
            # Pattern 2: "Page | Website" (e.g., "People | Float")
            # Pattern 3: "Website: Description" (e.g., "21st.dev: The first vibe-crafting tool")
            # Pattern 4: Just "Page" (e.g., "ActivityWatch")

            # Check for " - " separator
            if ' - ' in title:
                parts = title.split(' - ')
                if len(parts) == 2:
                    # Assume format is "Page - Website"
                    page = parts[0].strip()
                    website = parts[1].strip()
                    # Format as "Website - Page" for consistency
                    return f"{website} - {page}"
                else:
                    # Multiple " - ", take first part as page name
                    return parts[0].strip()

            # Check for " | " separator
            if ' | ' in title:
                parts = title.split(' | ')
                if len(parts) == 2:
                    page = parts[0].strip()
                    website = parts[1].strip()
                    return f"{website} - {page}"
                else:
                    return parts[0].strip()

            # Check for ":" separator (e.g., "21st.dev: Description")
            if ': ' in title:
                parts = title.split(': ', 1)
                website = parts[0].strip()
                description = parts[1].strip()
                # Use website name + abbreviated description
                return f"{website} - {description[:30]}" if len(description) > 30 else f"{website} - {description}"

            # No clear pattern, return as-is
            return title.strip()

        # For editors, extract project or file name
        if app in self.EDITORS:
            # Common patterns: "file.py — project" or "project - Editor"
            if ' — ' in title:
                parts = title.split(' — ')
                # Return project name (usually after —)
                return parts[-1].strip() if len(parts) > 1 else parts[0].strip()

            if ' - ' in title:
                parts = title.split(' - ')
                # Return last part (usually project/context)
                return parts[-1].strip()

            return title.strip()

        # For other apps, return full title
        return title.strip()

    def _get_day_boundaries(self, events: List[Dict[str, Any]]) -> tuple:
        """Get start and end of the day from events"""
        timestamps = []
        for e in events:
            ts = e['timestamp']
            # Handle both datetime objects and ISO strings
            if isinstance(ts, str):
                ts = datetime.fromisoformat(ts.replace('Z', '+00:00'))
            timestamps.append(ts)

        day_start = min(timestamps).replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        return day_start, day_end

    def _create_time_blocks(
        self,
        day_start: datetime,
        day_end: datetime,
        events: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Divide day into 15-minute blocks and analyze each
        Also tracks AFK/inactive periods as separate blocks

        Returns:
            List of blocks with main and supporting activities (or AFK markers)
        """
        blocks = []
        current_time = day_start
        block_duration = timedelta(minutes=self.BLOCK_SIZE_MINUTES)
        last_active_block_end = None

        while current_time < day_end:
            block_end = current_time + block_duration

            # Get events that overlap with this block
            block_events = self._get_events_in_block(current_time, block_end, events)

            if block_events:
                # Check if there was a gap since last active block
                if last_active_block_end and current_time > last_active_block_end:
                    # Insert AFK block for the gap
                    afk_block = {
                        'start_time': last_active_block_end.strftime('%H:%M'),
                        'end_time': current_time.strftime('%H:%M'),
                        'duration': int((current_time - last_active_block_end).total_seconds()),
                        'is_afk': True,
                        'main_activity': {
                            'app': 'AFK / Inactive',
                            'raw_app': 'AFK',
                            'primary_window': '',
                            'windows': [],
                            'duration': int((current_time - last_active_block_end).total_seconds()),
                            'percentage': 100.0
                        },
                        'supporting_activities': []
                    }
                    blocks.append(afk_block)

                # Analyze this active block
                block_data = self._analyze_block(current_time, block_end, block_events)
                if block_data:
                    block_data['is_afk'] = False
                    blocks.append(block_data)
                    last_active_block_end = block_end

            current_time = block_end

        return blocks

    def _get_events_in_block(
        self,
        block_start: datetime,
        block_end: datetime,
        events: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Get all events that overlap with this time block"""
        block_events = []

        for event in events:
            ts = event['timestamp']
            # Handle both datetime objects and ISO strings
            if isinstance(ts, str):
                event_start = datetime.fromisoformat(ts.replace('Z', '+00:00'))
            else:
                event_start = ts
            event_end = event_start + timedelta(seconds=float(event['duration']))

            # Check if event overlaps with block
            if event_start < block_end and event_end > block_start:
                # Calculate overlap duration
                overlap_start = max(event_start, block_start)
                overlap_end = min(event_end, block_end)
                overlap_duration = (overlap_end - overlap_start).total_seconds()

                if overlap_duration > 0:
                    block_events.append({
                        **event,
                        'block_duration': overlap_duration  # Duration within this specific block
                    })

        return block_events

    def _analyze_block(
        self,
        block_start: datetime,
        block_end: datetime,
        block_events: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Analyze a single 15-minute block

        Determines main activity (most time spent) and supporting activities
        Groups browsers/editors by window title, other apps by app name
        """
        # Group by activity key (app or app+window for browsers/editors)
        activity_times = defaultdict(lambda: {'duration': 0, 'windows': [], 'app': '', 'primary_window': '', 'events': []})

        for event in block_events:
            app = event.get('app', 'Unknown')
            title = event.get('title', '')
            duration = event.get('block_duration', 0)

            # Get event timestamps
            ts = event['timestamp']
            if isinstance(ts, str):
                event_start = datetime.fromisoformat(ts.replace('Z', '+00:00'))
            else:
                event_start = ts
            event_end = event_start + timedelta(seconds=float(event.get('duration', 0)))

            # Determine grouping key
            if app in self.BROWSERS or app in self.EDITORS:
                # For browsers/editors: group by primary window
                primary_window = self._extract_primary_window(app, title)
                activity_key = f"{app}:{primary_window}"
                activity_times[activity_key]['app'] = app
                activity_times[activity_key]['primary_window'] = primary_window
            else:
                # For other apps: group by app name only
                activity_key = app
                activity_times[activity_key]['app'] = app
                activity_times[activity_key]['primary_window'] = ''

            activity_times[activity_key]['duration'] += duration
            if title and title not in activity_times[activity_key]['windows']:
                activity_times[activity_key]['windows'].append(title)

            # Store event details for timestamp tracking
            activity_times[activity_key]['events'].append({
                'start': event_start,
                'end': event_end,
                'title': title,
                'duration': duration
            })

        if not activity_times:
            return None

        # Sort activities by duration (descending)
        sorted_activities = sorted(activity_times.items(), key=lambda x: x[1]['duration'], reverse=True)

        # Main activity = activity with most time
        main_key, main_data = sorted_activities[0]

        # Format main activity display name
        if main_data['primary_window']:
            main_display_name = f"{main_data['primary_window']} ({main_data['app']})"
        else:
            main_display_name = main_data['app']

        # Supporting activities = all others
        supporting = []
        for key, data in sorted_activities[1:]:
            if data['primary_window']:
                display_name = f"{data['primary_window']} ({data['app']})"
            else:
                display_name = data['app']

            # Calculate earliest start and latest end from events
            if data['events']:
                start_time_utc = min(e['start'] for e in data['events'])
                end_time_utc = max(e['end'] for e in data['events'])
            else:
                start_time_utc = None
                end_time_utc = None

            supporting.append({
                'app': display_name,
                'windows': data['windows'],
                'duration': round(data['duration']),
                'start_time_utc': start_time_utc.isoformat() if start_time_utc else None,
                'end_time_utc': end_time_utc.isoformat() if end_time_utc else None,
                'events': data['events']  # Include raw event details
            })

        total_block_duration = sum(data['duration'] for _, data in sorted_activities)

        # Calculate main activity timestamps
        if main_data['events']:
            main_start_utc = min(e['start'] for e in main_data['events'])
            main_end_utc = max(e['end'] for e in main_data['events'])
        else:
            main_start_utc = None
            main_end_utc = None

        return {
            'start_time': block_start.strftime('%H:%M'),
            'end_time': block_end.strftime('%H:%M'),
            'start_time_utc': block_start.isoformat(),
            'end_time_utc': block_end.isoformat(),
            'duration': round(total_block_duration),
            'main_activity': {
                'app': main_display_name,
                'raw_app': main_data['app'],
                'primary_window': main_data['primary_window'],
                'windows': main_data['windows'],
                'duration': round(main_data['duration']),
                'percentage': round((main_data['duration'] / total_block_duration) * 100, 1) if total_block_duration > 0 else 0,
                'start_time_utc': main_start_utc.isoformat() if main_start_utc else None,
                'end_time_utc': main_end_utc.isoformat() if main_end_utc else None,
                'events': main_data['events']  # Include raw event details
            },
            'supporting_activities': supporting
        }

    def _merge_consecutive_blocks(self, blocks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Merge consecutive blocks with the same main activity

        This creates the larger "work session" blocks like in Timely
        For browsers/editors, also checks if primary window matches
        """
        if not blocks:
            return []

        merged = []
        current_block = blocks[0].copy()
        current_block['supporting_activities'] = self._consolidate_supporting(
            [current_block]
        )

        for next_block in blocks[1:]:
            # Never merge AFK blocks - each AFK period is separate
            if current_block.get('is_afk') or next_block.get('is_afk'):
                # Save current and start new (don't merge)
                merged.append(current_block)
                current_block = next_block.copy()
                current_block['supporting_activities'] = self._consolidate_supporting(
                    [current_block]
                )
                continue

            # Check if main activity is the same
            # Compare raw_app and primary_window for accurate matching
            current_raw_app = current_block['main_activity'].get('raw_app', current_block['main_activity']['app'])
            next_raw_app = next_block['main_activity'].get('raw_app', next_block['main_activity']['app'])

            current_primary = current_block['main_activity'].get('primary_window', '')
            next_primary = next_block['main_activity'].get('primary_window', '')

            # For browsers/editors: must match both app AND primary window
            # For other apps: just match app name
            same_activity = False
            if current_raw_app in (self.BROWSERS | self.EDITORS):
                # Browser or editor: check both app and primary window
                same_activity = (current_raw_app == next_raw_app and current_primary == next_primary)
            else:
                # Other apps: just check app name
                same_activity = (current_raw_app == next_raw_app)

            if same_activity and self._same_main_windows(current_block, next_block):
                # Merge: extend end time and accumulate durations
                current_block['end_time'] = next_block['end_time']
                current_block['end_time_utc'] = next_block['end_time_utc']
                
                # Calculate duration from timestamp range instead of summing
                start_dt = datetime.fromisoformat(current_block['start_time_utc'])
                end_dt = datetime.fromisoformat(next_block['end_time_utc'])
                current_block['duration'] = int((end_dt - start_dt).total_seconds())
                
                current_block['main_activity']['duration'] += next_block['main_activity']['duration']

                # Consolidate supporting activities
                current_block['supporting_activities'] = self._consolidate_supporting(
                    [current_block, next_block]
                )
            else:
                # Different main activity, save current and start new
                merged.append(current_block)
                current_block = next_block.copy()
                current_block['supporting_activities'] = self._consolidate_supporting(
                    [current_block]
                )

        # Don't forget the last block
        merged.append(current_block)

        return merged

    def _same_main_windows(self, block1: Dict[str, Any], block2: Dict[str, Any]) -> bool:
        """Check if two blocks have significant overlap in window titles"""
        windows1 = set(block1['main_activity']['windows'])
        windows2 = set(block2['main_activity']['windows'])

        if not windows1 or not windows2:
            return True

        # If there's any overlap, consider them the same context
        return len(windows1 & windows2) > 0

    def _consolidate_supporting(self, blocks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Consolidate supporting activities across merged blocks"""
        app_data = defaultdict(lambda: {'duration': 0, 'windows': set(), 'events': []})

        for block in blocks:
            for support in block.get('supporting_activities', []):
                app = support['app']
                app_data[app]['duration'] += support['duration']
                app_data[app]['windows'].update(support['windows'])

                # Accumulate events for timestamp tracking
                if 'events' in support:
                    app_data[app]['events'].extend(support['events'])

        # Build consolidated list with timestamps
        consolidated = []
        for app, data in sorted(app_data.items(), key=lambda x: x[1]['duration'], reverse=True):
            # Calculate earliest start and latest end from all events
            if data['events']:
                start_time_utc = min(e['start'] for e in data['events'])
                end_time_utc = max(e['end'] for e in data['events'])
            else:
                start_time_utc = None
                end_time_utc = None

            consolidated.append({
                'app': app,
                'windows': list(data['windows']),
                'duration': data['duration'],
                'start_time_utc': start_time_utc.isoformat() if start_time_utc else None,
                'end_time_utc': end_time_utc.isoformat() if end_time_utc else None,
                'events': data['events']
            })

        return consolidated