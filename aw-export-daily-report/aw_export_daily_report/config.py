"""
Settings management for aw-export-daily-report
"""

import json
from pathlib import Path
from typing import Optional
import re


class SettingsManager:
    """Manages user settings with validation and persistence"""

    DEFAULT_SETTINGS = {
        "user": {
            "email": "",
            "timezone": "Europe/Berlin"
        },
        "work_schedule": {
            "enabled": False,
            "days": ["monday", "tuesday", "wednesday", "thursday", "friday"],
            "start_time": "09:00",
            "end_time": "18:00"
        },
        "integrations": {
            "n8n": {
                "enabled": True,
                "webhook_url": "https://wins-n8n.zeabur.app/webhook/ai-tracker"
            },
            "asana": {
                "enabled": False,
                "personal_access_token": "",  # Load from .env file (ASANA_PERSONAL_ACCESS_TOKEN)
                "cache": {
                    "user_gid": "",
                    "tasks_cache": {}
                },
                "task_filters": {
                    "match_task_names": [
                        "Internal Comms & Team Management",
                        "Meetings, Communications, Project Management",
                        "Team Management (1-on-1s, all-hands, best-self review, management meeting, retrospective, sprint meetings, stand-up & team meeting)"
                    ],
                    "match_sections_containing": ["time-tracking"],
                    "match_all_tasks": False
                }
            }
        }
    }

    def __init__(self, config_path: Optional[Path] = None):
        """Initialize settings manager with config file path"""
        if config_path is None:
            # Default: aw-export-daily-report/config/settings.json
            project_root = Path(__file__).parent.parent
            config_path = project_root / 'config' / 'settings.json'

        self.config_path = config_path
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

    def load_settings(self) -> dict:
        """Load settings from file, return defaults if missing"""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    # Merge with defaults (in case new fields added)
                    return self._merge_with_defaults(settings)
            else:
                return self.DEFAULT_SETTINGS.copy()
        except Exception as e:
            print(f"Error loading settings: {e}")
            return self.DEFAULT_SETTINGS.copy()

    def save_settings(self, settings: dict) -> tuple[bool, list[str]]:
        """
        Validate and save settings to file

        Returns:
            (success: bool, errors: list[str])
        """
        # Validate settings
        errors = self._validate_settings(settings)
        if errors:
            return False, errors

        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)
            return True, []
        except Exception as e:
            return False, [f"Failed to save settings: {str(e)}"]

    def get_user_email(self) -> str:
        """Get user email from settings"""
        settings = self.load_settings()
        return settings.get('user', {}).get('email', '')

    def get_user_timezone(self) -> str:
        """Get user timezone from settings"""
        settings = self.load_settings()
        return settings.get('user', {}).get('timezone', 'Europe/Berlin')

    def get_webhook_url(self) -> str:
        """Get N8N webhook URL from settings"""
        settings = self.load_settings()
        return settings.get('integrations', {}).get('n8n', {}).get('webhook_url', '')

    def get_asana_token(self) -> str:
        """
        Get Asana personal access token from settings or .env file

        Priority: settings.json > .env file > empty string
        """
        import os
        from dotenv import load_dotenv

        # Try settings first
        settings = self.load_settings()
        token = settings.get('integrations', {}).get('asana', {}).get('personal_access_token', '')

        # If empty, try loading from .env
        if not token:
            load_dotenv()
            token = os.getenv('ASANA_PERSONAL_ACCESS_TOKEN', '')

        return token

    def get_asana_user_gid(self) -> str:
        """Get cached Asana user GID from settings"""
        settings = self.load_settings()
        return settings.get('integrations', {}).get('asana', {}).get('cache', {}).get('user_gid', '')

    def set_asana_user_gid(self, gid: str) -> bool:
        """
        Cache Asana user GID to settings
        
        Args:
            gid: User GID to cache
            
        Returns:
            True if saved successfully
        """
        settings = self.load_settings()
        
        # Ensure asana settings exist
        if 'integrations' not in settings:
            settings['integrations'] = {}
        if 'asana' not in settings['integrations']:
            settings['integrations']['asana'] = self.DEFAULT_SETTINGS['integrations']['asana'].copy()
        if 'cache' not in settings['integrations']['asana']:
            settings['integrations']['asana']['cache'] = {}
            
        settings['integrations']['asana']['cache']['user_gid'] = gid
        
        success, _ = self.save_settings(settings)
        return success

    def is_asana_enabled(self) -> bool:
        """Check if Asana integration is enabled"""
        settings = self.load_settings()
        return settings.get('integrations', {}).get('asana', {}).get('enabled', False)

    def get_asana_filters(self) -> dict:
        """Get Asana task filter configuration"""
        settings = self.load_settings()
        return settings.get('integrations', {}).get('asana', {}).get('task_filters', {})

    def get_cached_tasks(self, email: str, ttl_seconds: int = 1800) -> Optional[list]:
        """
        Get cached Asana tasks for email if cache is fresh
        
        Args:
            email: User email
            ttl_seconds: Time-to-live in seconds (default: 1800 = 30 minutes)
            
        Returns:
            List of tasks if cache is fresh, None otherwise
        """
        from datetime import datetime, timezone
        
        settings = self.load_settings()
        tasks_cache = settings.get('integrations', {}).get('asana', {}).get('cache', {}).get('tasks_cache', {})
        
        if email not in tasks_cache:
            return None
            
        cache_entry = tasks_cache[email]
        cached_tasks = cache_entry.get('tasks', [])
        timestamp_str = cache_entry.get('timestamp', '')
        
        if not timestamp_str:
            return None
            
        try:
            # Parse timestamp
            cached_time = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            current_time = datetime.now(timezone.utc)
            
            # Check if cache is fresh
            age_seconds = (current_time - cached_time).total_seconds()
            
            if age_seconds < ttl_seconds:
                return cached_tasks
            else:
                return None  # Cache expired
                
        except Exception as e:
            print(f"Error checking cache: {e}")
            return None

    def set_cached_tasks(self, email: str, tasks: list) -> bool:
        """
        Cache Asana tasks for email with current timestamp
        
        Args:
            email: User email
            tasks: List of task objects to cache
            
        Returns:
            True if saved successfully
        """
        from datetime import datetime, timezone
        
        settings = self.load_settings()
        
        # Ensure structure exists
        if 'integrations' not in settings:
            settings['integrations'] = {}
        if 'asana' not in settings['integrations']:
            settings['integrations']['asana'] = self.DEFAULT_SETTINGS['integrations']['asana'].copy()
        if 'cache' not in settings['integrations']['asana']:
            settings['integrations']['asana']['cache'] = {}
        if 'tasks_cache' not in settings['integrations']['asana']['cache']:
            settings['integrations']['asana']['cache']['tasks_cache'] = {}
            
        # Store tasks with timestamp
        settings['integrations']['asana']['cache']['tasks_cache'][email] = {
            'tasks': tasks,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        success, _ = self.save_settings(settings)
        return success

    def _merge_with_defaults(self, settings: dict) -> dict:
        """Merge user settings with defaults for any missing fields"""
        merged = self.DEFAULT_SETTINGS.copy()

        # Deep merge user settings
        if 'user' in settings:
            merged['user'].update(settings['user'])
        if 'work_schedule' in settings:
            merged['work_schedule'].update(settings['work_schedule'])
        if 'integrations' in settings:
            if 'n8n' in settings['integrations']:
                merged['integrations']['n8n'].update(settings['integrations']['n8n'])
            if 'asana' in settings['integrations']:
                merged['integrations']['asana'].update(settings['integrations']['asana'])
                # Deep merge task_filters and cache
                if 'task_filters' in settings['integrations']['asana']:
                    merged['integrations']['asana']['task_filters'].update(
                        settings['integrations']['asana']['task_filters']
                    )
                if 'cache' in settings['integrations']['asana']:
                    merged['integrations']['asana']['cache'].update(
                        settings['integrations']['asana']['cache']
                    )

        return merged

    def _validate_settings(self, settings: dict) -> list[str]:
        """Validate settings structure and values"""
        errors = []

        # Validate email
        email = settings.get('user', {}).get('email', '')
        if email and not self._is_valid_email(email):
            errors.append("Invalid email format")

        # Validate timezone (basic check - just ensure it's not empty)
        timezone = settings.get('user', {}).get('timezone', '')
        if not timezone:
            errors.append("Timezone is required")

        # Validate work schedule times
        start_time = settings.get('work_schedule', {}).get('start_time', '')
        end_time = settings.get('work_schedule', {}).get('end_time', '')

        if start_time and not self._is_valid_time(start_time):
            errors.append("Invalid start time format (use HH:MM)")
        if end_time and not self._is_valid_time(end_time):
            errors.append("Invalid end time format (use HH:MM)")

        return errors

    def _is_valid_email(self, email: str) -> bool:
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))

    def _is_valid_time(self, time_str: str) -> bool:
        """Validate HH:MM time format"""
        pattern = r'^([0-1][0-9]|2[0-3]):[0-5][0-9]$'
        return bool(re.match(pattern, time_str))