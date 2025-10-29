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
    MIN_ACTIVITY_SECONDS = 5  # Filter noise
    AFK_THRESHOLD_SECONDS = 120  # Only exclude AFK periods >= 2 minutes

    # Apps that should be grouped by window title (browsers and editors)
    BROWSERS = {'Google Chrome', 'Comet', 'Safari', 'Firefox', 'Arc', 'Brave', 'Microsoft Edge'}
    EDITORS = {'Cursor', 'Code', 'Visual Studio Code', 'Xcode', 'PyCharm', 'IntelliJ IDEA', 'Sublime Text'}

    # Project-based apps (extract project/file name from title)
    PROJECT_BASED_APPS = {
        # Creative Suite - Adobe
        'Adobe After Effects', 'Adobe Illustrator', 'Adobe InDesign',
        'Adobe Photoshop', 'Adobe Premiere Pro',
        
        # Creative Suite - Other
        'DaVinci Resolve', 'Descript', 'Figma', 'FigJam', 'Canva', 'Miro',
        
        # Video/Media
        'CapCut', 'Vyond', 'Wondershare Filmora',
        
        # Office
        'Microsoft Excel', 'Microsoft Word', 'Microsoft PowerPoint', 'Notion',
        
        # Development - Code Editors
        'Visual Studio Code', 'VS Code', 'IntelliJ IDEA', 'PyCharm', 'Eclipse',
        'WebStorm', 'Xcode', 'Android Studio', 'Sublime Text', 'Atom',
        'JupyterLab', 'CLion', 'Cursor', 'JetBrains Fleet',
        'Microsoft Visual Studio', 'NetBeans', 'Terminal',
        
        # AI Coding Agents
        'Claude Code', 'GitHub Copilot', 'Replit Ghostwriter', 'Windsurf',
        
        # Communication
        'Slack'
    }
    
    # Services that can be desktop OR browser (merge both versions)
    MERGEABLE_SERVICES = {
        # Project Management
        'Asana', 'Notion', 'ClickUp', 'Monday.com', 'Trello',
        
        # Creative
        'Figma', 'FigJam', 'Canva', 'Miro',
        
        # Communication
        'Slack', 'Zoom', 'Google Meet',
        
        # Google Workspace
        'Google Drive', 'Google Docs', 'Google Sheets', 'Google Slides',
        
        # Development
        'Replit', 'JupyterLab', 'GitHub Copilot',
        
        # Automation
        'n8n',
        
        # Other
        'Dropbox', 'Float'
    }

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
        """Filter out long AFK periods (>= 2 min), loginwindow (screen locked), and very short activities"""
        return [
            event for event in self.events
            if not (event.get('afk', False) and float(event.get('duration', 0)) >= self.AFK_THRESHOLD_SECONDS)
            and event.get('app', '') != 'loginwindow'
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

        # For n8n, remove the " - n8n" suffix
        if app == 'n8n':
            # Remove browser suffixes first
            for suffix in [' - Google Chrome', ' - Comet', ' - Safari', ' - Firefox', ' - Arc', ' - Brave', ' - Microsoft Edge']:
                title = title.replace(suffix, '')
            
            # Remove " - n8n" suffix only
            if title.endswith(' - n8n'):
                title = title[:-6]
            
            return title.strip()

        # For Google Meet, remove "Meet - " prefix only
        if app == 'Google Meet':
            # Remove browser suffixes first
            for suffix in [' - Google Chrome', ' - Comet', ' - Safari', ' - Firefox', ' - Arc', ' - Brave', ' - Microsoft Edge']:
                title = title.replace(suffix, '')
            
            # Remove "Meet - " prefix only, keep rest of title as-is
            if title.startswith('Meet - '):
                title = title[7:]
            
            return title.strip()

        # For browsers, extract website and page name
        if app in self.BROWSERS:
            # Gmail Exception: Special handling for Gmail/email clients
            if 'hy.am studios GmbH Mail' in title or '@hyam.de' in title or title.endswith('Mail'):
                # Format: "Google Chrome - [Email Subject] - alican@hyam.de - hy.am studios GmbH Mail"
                # Extract just the email subject
                # Remove browser prefix
                cleaned = title
                for prefix in ['Google Chrome - ', 'Safari - ', 'Firefox - ', 'Arc - ', 'Brave - ', 'Microsoft Edge - ']:
                    if cleaned.startswith(prefix):
                        cleaned = cleaned[len(prefix):]
                        break
                
                # Remove email suffix patterns
                if ' - alican@hyam.de - hy.am studios GmbH Mail' in cleaned:
                    subject = cleaned.split(' - alican@hyam.de - hy.am studios GmbH Mail')[0]
                elif ' - hy.am studios GmbH Mail' in cleaned:
                    subject = cleaned.split(' - hy.am studios GmbH Mail')[0]
                else:
                    subject = cleaned
                
                return f"Gmail - {subject.strip()}"
            
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

        # For Slack, extract channel/DM and workspace
        if app == 'Slack':
            # Common patterns:
            # "aiaiai (Channel) - HY.AM - 3 new items - Slack"
            # "Izzat, Sarah Heuser (DM) - HY.AM - 3 new items - Slack"
            # "! random (Channel) - HY.AM - 4 new items - Slack"
            
            # Remove " - Slack" suffix
            if ' - Slack' in title:
                title = title.replace(' - Slack', '')
            
            # Pattern: "channel_name (Channel/DM) - workspace - X new items"
            # Split by " - "
            parts = title.split(' - ')
            
            if len(parts) >= 2:
                # First part: channel/DM name (e.g., "aiaiai (Channel)")
                channel = parts[0].strip()
                # Second part: workspace name (e.g., "HY.AM")
                workspace = parts[1].strip()
                return f"{channel} - {workspace}"
            
            # Fallback: return cleaned title
            return title.strip()

        # For editors and project-based apps, extract project or file name
        if app in self.EDITORS or app in self.PROJECT_BASED_APPS:
            # Common patterns: "file.py — project" or "project - Editor"
            # Handle em dash (—) - most editors use this
            if ' — ' in title or '—' in title:
                # Try with space-padded em dash first
                parts = title.split(' — ') if ' — ' in title else title.split('—')
                # Return project name (usually after —)
                return parts[-1].strip() if len(parts) > 1 else parts[0].strip()

            # Handle regular dash
            if ' - ' in title:
                parts = title.split(' - ')
                # Return last part (usually project/context)
                return parts[-1].strip()

            return title.strip()

        # For other apps, return full title
        return title.strip()

    def _detect_service_in_title(self, title: str) -> str:
        """
        Detect if title contains a known service name
        
        Returns service name if found, else None
        Used to detect Figma/Asana/etc in browser titles for merging
        """
        if not title:
            return None
        
        title_lower = title.lower()
        
        # Check for mergeable services (highest priority)
        for service in self.MERGEABLE_SERVICES:
            if service.lower() in title_lower:
                return service
        
        # Common service keywords for browsers
        service_keywords = {
            'timely': 'Timely',
            'google drive': 'Google Drive',
            'google docs': 'Google Docs',
            'google sheets': 'Google Sheets',
            'google slides': 'Google Slides',
            'gmail': 'Gmail',
            'google meet': 'Google Meet',
            'meet': 'Google Meet',  # Standalone "meet" also maps to Google Meet
            'google calendar': 'Google Calendar',
            'asana': 'Asana',
            'notion': 'Notion',
            'slack': 'Slack',
            'zoom': 'Zoom',
            'github': 'GitHub',
            'figma': 'Figma',
            'figjam': 'FigJam',
            'canva': 'Canva',
            'miro': 'Miro',
            'trello': 'Trello',
            'monday.com': 'Monday.com',
            'clickup': 'ClickUp',
            'linear': 'Linear',
            'jira': 'Jira',
            'basecamp': 'Basecamp'
        }
        
        for keyword, service_name in service_keywords.items():
            if keyword in title_lower:
                return service_name
        
        return None

    def _extract_keywords(self, title: str) -> List[str]:
        """Extract meaningful keywords from title, excluding generic terms"""
        generic_terms = {
            'untitled', 'project', 'workspace', 'document', 'new', 'tab',
            'window', 'file', 'folder', 'chrome', 'google', 'safari', 'firefox',
            'browser', 'page', 'home', 'settings', 'preferences', 'search',
            'results', 'loading', 'welcome', 'default', 'blank', 'empty',
            'general', 'main', 'editor', 'viewer', 'preview', 'application',
            'app', 'program', 'system', 'menu', 'toolbar', 'sidebar', 'panel',
            'dialog', 'modal', 'popup', 'notification', 'alert', 'message',
            'inbox', 'dashboard', 'overview', 'summary', 'report', 'list',
            'view', 'details', 'info', 'about', 'help', 'support', 'guide',
            'tutorial', 'docs', 'documentation', 'readme', 'license', 'terms',
            'privacy', 'policy', 'login', 'signin', 'signup', 'register',
            'logout', 'account', 'profile', 'user', 'admin', 'administrator',
            'manager', 'control', 'configuration', 'options', 'advanced',
            'basic', 'simple', 'quick', 'start', 'getting', 'started',
            'open', 'close', 'save', 'export', 'import', 'download', 'upload',
            'copy', 'paste', 'cut', 'delete', 'remove', 'add', 'create',
            'edit', 'update', 'modify', 'change', 'rename', 'move'
        }
        
        words = title.lower().split()
        keywords = []
        
        for word in words:
            cleaned = ''.join(c for c in word if c.isalnum())
            if len(cleaned) > 3 and cleaned not in generic_terms:
                keywords.append(cleaned)
        
        return keywords

    def _get_day_boundaries(self, events: List[Dict[str, Any]]) -> tuple:
        """Get start and end of the day from events, limited to 06:00-21:00"""
        timestamps = []
        for e in events:
            ts = e['timestamp']
            # Handle both datetime objects and ISO strings
            if isinstance(ts, str):
                ts = datetime.fromisoformat(ts.replace('Z', '+00:00'))
            timestamps.append(ts)

        earliest = min(timestamps)
        
        # Start at 06:00 (6am) same day
        day_start = earliest.replace(hour=6, minute=0, second=0, microsecond=0)
        
        # End at 21:00 (9pm) same day
        day_end = earliest.replace(hour=21, minute=0, second=0, microsecond=0)
        
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
            event_end = event_start + timedelta(seconds=float(event.get('duration', 0)))

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

        Hybrid approach:
        - Known app types (browsers/editors/project-based): Use smart primary window extraction
        - Other apps: Use keyword frequency grouping
        """
        # Calculate timeline block duration (always use full interval)
        timeline_duration = (block_end - block_start).total_seconds()
        
        # STEP 1: Categorize and group events by app
        from collections import defaultdict
        app_groups = defaultdict(list)
        
        for event in block_events:
            app = event.get('app', 'Unknown')
            title = event.get('title', '')
            
            # REMOVED: Service detection and app categorization
            # Just group by raw app name
            app_groups[app].append(event)
        
        # STEP 2: Within each app, use category-specific grouping strategy
        activity_times = defaultdict(lambda: {
            'duration': 0, 'windows': [], 'app': '', 'keyword': '', 
            'primary_window': '', 'events': []
        })
        
        for app, app_events in app_groups.items():
            # REMOVED: Category-based grouping
            # Just group by raw window title
            for event in app_events:
                title = event.get('title', '')
                duration = event.get('block_duration', 0)
                
                # Get event timestamps
                ts = event['timestamp']
                if isinstance(ts, str):
                    event_start = datetime.fromisoformat(ts.replace('Z', '+00:00'))
                else:
                    event_start = ts
                event_end = event_start + timedelta(seconds=float(event.get('duration', 0)))
                
                # Format as "App Name - Window Title" (no manipulation)
                activity_key = f"{app}:{title}"
                if title:
                    display_name = f"{app} - {title}"
                else:
                    display_name = app
                
                activity_times[activity_key]['app'] = app
                activity_times[activity_key]['primary_window'] = title
                activity_times[activity_key]['display_name'] = display_name
                activity_times[activity_key]['duration'] += duration
                
                if title and title not in activity_times[activity_key]['windows']:
                    activity_times[activity_key]['windows'].append(title)
                
                activity_times[activity_key]['events'].append({
                    'start': event_start,
                    'end': event_end,
                    'title': title,
                    'duration': duration
                })
        
        if not activity_times:
            return None

        # Filter out activities < 60 seconds and sort by duration (descending)
        sorted_activities = sorted(
            [(key, data) for key, data in activity_times.items() if data['duration'] >= 60],
            key=lambda x: x[1]['duration'],
            reverse=True
        )
        
        # If no activities remain after filtering, return None
        if not sorted_activities:
            return None

        # Main activity = activity with most time
        main_key, main_data = sorted_activities[0]

        # Supporting activities = all others
        supporting = []
        for key, data in sorted_activities[1:]:
            display_name = data.get('display_name', data['app'])

            # Calculate earliest start and latest end from events
            if data['events']:
                start_time_utc = min(e['start'] for e in data['events'])
                end_time_utc = max(e['end'] for e in data['events'])
            else:
                start_time_utc = None
                end_time_utc = None

            supporting.append({
                'app': display_name,
                'primary_window': data['primary_window'],
                'windows': data['windows'],
                'duration': round(data['duration']),
                'start_time_utc': start_time_utc.isoformat() if start_time_utc else None,
                'end_time_utc': end_time_utc.isoformat() if end_time_utc else None,
                'events': data['events']
            })

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
            'duration': round(timeline_duration),
            'main_activity': {
                'app': main_data.get('display_name', main_data['app']),
                'raw_app': main_data['app'],
                'primary_window': main_data['primary_window'],
                'windows': main_data['windows'],
                'duration': round(main_data['duration']),
                'percentage': round((main_data['duration'] / timeline_duration) * 100, 1) if timeline_duration > 0 else 0,
                'start_time_utc': main_start_utc.isoformat() if main_start_utc else None,
                'end_time_utc': main_end_utc.isoformat() if main_end_utc else None,
                'events': main_data['events']
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
            # Compare raw_app and primary window for accurate matching
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
                # Safety check: ensure end_time doesn't exceed 21:00
                end_dt = datetime.fromisoformat(next_block['end_time_utc'])
                end_hour = end_dt.hour
                
                # Cap at 21:00 (do not merge beyond work hours)
                if end_hour >= 21:
                    max_end = end_dt.replace(hour=21, minute=0, second=0, microsecond=0)
                    current_block['end_time'] = max_end.strftime('%H:%M')
                    current_block['end_time_utc'] = max_end.isoformat()
                else:
                    current_block['end_time'] = next_block['end_time']
                    current_block['end_time_utc'] = next_block['end_time_utc']
                
                # Calculate duration from timestamp range instead of summing
                start_dt = datetime.fromisoformat(current_block['start_time_utc'])
                capped_end_dt = datetime.fromisoformat(current_block['end_time_utc'])
                current_block['duration'] = int((capped_end_dt - start_dt).total_seconds())
                
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

        # Apply 10% threshold filter: convert blocks with main activity < 10% to AFK
        filtered = []
        for block in merged:
            if block.get('is_afk'):
                # Already AFK, keep as-is
                filtered.append(block)
            else:
                main_percentage = block['main_activity']['percentage']
                if main_percentage >= 10.0:
                    # Keep blocks with significant main activity
                    filtered.append(block)
                else:
                    # Convert low-activity blocks to AFK
                    block['is_afk'] = True
                    block['main_activity'] = {
                        'app': 'AFK / Inactive',
                        'raw_app': 'AFK',
                        'primary_window': '',
                        'windows': [],
                        'duration': block['duration'],
                        'percentage': 100.0
                    }
                    block['supporting_activities'] = []
                    filtered.append(block)

        # Post-processing: Merge consecutive AFK blocks
        final_merged = []
        current_afk = None
        
        for block in filtered:
            if block.get('is_afk'):
                if current_afk is None:
                    # Start new AFK block
                    current_afk = block.copy()
                else:
                    # Extend existing AFK block
                    current_afk['end_time'] = block['end_time']
                    if 'end_time_utc' in block:
                        current_afk['end_time_utc'] = block['end_time_utc']
                    current_afk['duration'] += block['duration']
            else:
                # Active block - save any pending AFK block first
                if current_afk is not None:
                    final_merged.append(current_afk)
                    current_afk = None
                final_merged.append(block)
        
        # Don't forget trailing AFK block
        if current_afk is not None:
            final_merged.append(current_afk)

        return final_merged

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