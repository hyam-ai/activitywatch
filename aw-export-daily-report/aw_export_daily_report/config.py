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
            "timezone": "Europe/Berlin",
            "asana_gid": None  # Cached Asana user GID
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

    def get_user_asana_gid(self) -> Optional[str]:
        """Get cached Asana user GID from settings"""
        settings = self.load_settings()
        return settings.get('user', {}).get('asana_gid')

    def set_user_asana_gid(self, asana_gid: str) -> bool:
        """Cache Asana user GID in settings"""
        settings = self.load_settings()
        settings['user']['asana_gid'] = asana_gid
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