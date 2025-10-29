"""
Asana API client for fetching tasks and managing integrations.
"""

import requests
from typing import Optional, List, Dict, Any


class AsanaClient:
    """Client for interacting with Asana API"""

    BASE_URL = "https://app.asana.com/api/1.0"
    DEFAULT_TIMEOUT = 30

    def __init__(self, token: str):
        """
        Initialize Asana client with personal access token

        Args:
            token: Asana personal access token
        """
        self.token = token
        self.headers = {
            "Authorization": f"Bearer {token}"
        }

    def _fetch_paginated(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        timeout: int = DEFAULT_TIMEOUT
    ) -> List[Dict[str, Any]]:
        """
        Fetch all paginated data from Asana API

        Args:
            url: API endpoint URL
            params: Query parameters dict
            timeout: Request timeout in seconds

        Returns:
            List of all items across all pages
        """
        all_items = []
        offset = None
        params = params.copy() if params else {}

        while True:
            # Add offset for pagination
            if offset:
                params['offset'] = offset

            try:
                response = requests.get(url, headers=self.headers, params=params, timeout=timeout)

                # Check for errors
                if response.status_code != 200:
                    print(f"⚠️  API returned status {response.status_code}")
                    break

                data = response.json()

                # Check for API errors
                if 'errors' in data:
                    error_msg = data['errors'][0].get('message', 'Unknown error')
                    print(f"❌ API error: {error_msg}")
                    break

                # Collect data from this page
                page_items = data.get('data', [])
                all_items.extend(page_items)

                # Check for next page
                next_page = data.get('next_page')
                if not next_page:
                    break  # No more pages

                offset = next_page.get('offset')
                if not offset:
                    break

            except requests.Timeout:
                print(f"⚠️  Request timeout after {timeout}s")
                break
            except requests.RequestException as e:
                print(f"⚠️  Request failed: {e}")
                break

        return all_items

    def get_workspace_gid(self) -> Optional[str]:
        """
        Get workspace GID (uses first workspace)

        Returns:
            Workspace GID or None if failed
        """
        workspaces = self._fetch_paginated(
            f"{self.BASE_URL}/workspaces",
            params={'limit': 100}
        )

        if not workspaces:
            return None

        return workspaces[0]['gid']

    def get_user_gid_by_email(self, email: str, workspace_gid: str) -> Optional[str]:
        """
        Get user GID by email address

        Args:
            email: User email address
            workspace_gid: Workspace GID to search in

        Returns:
            User GID or None if not found
        """
        workspace_users = self._fetch_paginated(
            f"{self.BASE_URL}/workspaces/{workspace_gid}/users",
            params={'opt_fields': 'name,email', 'limit': 100}
        )

        if not workspace_users:
            return None

        matching_user = next(
            (u for u in workspace_users if u.get('email', '').lower() == email.lower()),
            None
        )

        return matching_user['gid'] if matching_user else None

    def get_team_memberships(self, user_gid: str, workspace_gid: str) -> List[Dict[str, Any]]:
        """
        Get non-guest team memberships for user

        Args:
            user_gid: User GID
            workspace_gid: Workspace GID

        Returns:
            List of team membership objects (non-guest only)
        """
        memberships_data = self._fetch_paginated(
            f"{self.BASE_URL}/users/{user_gid}/team_memberships",
            params={
                'workspace': workspace_gid,
                'opt_fields': 'team,team.name,user,user.name,is_guest',
                'limit': 100
            }
        )

        if not memberships_data:
            return []

        # Filter out guest memberships - only keep where user is a member
        return [m for m in memberships_data if not m.get('is_guest', False)]

    def get_user_projects(self, user_gid: str, team_memberships: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Get all active projects user has access to

        Args:
            user_gid: User GID
            team_memberships: List of team memberships from get_team_memberships()

        Returns:
            List of project objects with membership info
        """
        all_projects = []

        for membership in team_memberships:
            team = membership.get('team', {})
            team_gid = team.get('gid')
            team_name = team.get('name', 'Unknown')

            if not team_gid:
                continue

            # Get projects for this team
            projects = self._fetch_paginated(
                f"{self.BASE_URL}/teams/{team_gid}/projects",
                params={'opt_fields': 'name,archived', 'limit': 100}
            )

            if projects:
                for project in projects:
                    project['team_name'] = team_name
                    project['team_gid'] = team_gid
                    all_projects.append(project)

        # Filter out archived projects - only keep active projects
        active_projects = [p for p in all_projects if not p.get('archived', False)]

        # Get project memberships to filter by user access
        user_accessible_projects = []

        for project in active_projects:
            project_gid = project.get('gid')
            if not project_gid:
                continue

            # Check if user has access to this project
            memberships = self._fetch_paginated(
                f"{self.BASE_URL}/projects/{project_gid}/project_memberships",
                params={'user': user_gid, 'limit': 100}
            )

            if memberships:
                # User has access
                project['access_level'] = memberships[0].get('access_level', 'N/A')
                user_accessible_projects.append(project)

        return user_accessible_projects

    def get_filtered_tasks(
        self,
        user_email: str,
        filter_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Get tasks for user, filtered by configuration

        Args:
            user_email: User email address
            filter_config: Filter configuration dict with keys:
                - match_task_names: List of exact task names to match
                - match_sections_containing: List of section keywords
                - match_all_tasks: If True, ignore filters and return all

        Returns:
            Dict with keys:
                - success: bool
                - user_email: str
                - user_gid: str
                - tasks: List[Dict] with task_id, task_name, project_name
                - error: str or None
        """
        # Default filter config
        if filter_config is None:
            filter_config = {
                'match_task_names': [],
                'match_sections_containing': ['time-tracking'],
                'match_all_tasks': False
            }

        # Get workspace
        workspace_gid = self.get_workspace_gid()
        if not workspace_gid:
            return {
                'success': False,
                'error': 'Failed to get workspace',
                'tasks': []
            }

        # Get user GID
        user_gid = self.get_user_gid_by_email(user_email, workspace_gid)
        if not user_gid:
            return {
                'success': False,
                'error': f'User with email {user_email} not found in workspace',
                'tasks': []
            }

        # Get team memberships
        team_memberships = self.get_team_memberships(user_gid, workspace_gid)
        if not team_memberships:
            return {
                'success': False,
                'error': 'No team memberships found',
                'tasks': []
            }

        # Get user projects
        user_projects = self.get_user_projects(user_gid, team_memberships)
        if not user_projects:
            return {
                'success': False,
                'error': 'No accessible projects found',
                'tasks': []
            }

        # Get tasks from all projects
        all_tasks = []

        for project in user_projects:
            project_gid = project.get('gid')
            project_name = project.get('name', 'Unknown')

            if not project_gid:
                continue

            tasks = self._fetch_paginated(
                f"{self.BASE_URL}/tasks",
                params={
                    'project': project_gid,
                    'opt_fields': 'name,assignee,assignee.name,memberships,memberships.section,memberships.section.name',
                    'limit': 100
                }
            )

            if tasks:
                for task in tasks:
                    task['project_context'] = {
                        'gid': project_gid,
                        'name': project_name
                    }
                    all_tasks.append(task)

        # Apply filters if not matching all tasks
        if not filter_config.get('match_all_tasks', False):
            filtered_tasks = [task for task in all_tasks if self._matches_filter(task, filter_config)]
        else:
            filtered_tasks = all_tasks

        # Transform to output format
        output_tasks = []
        for task in filtered_tasks:
            project_name = task.get('project_context', {}).get('name', '')

            output_tasks.append({
                'task_id': task.get('gid', ''),
                'task_name': task.get('name', ''),
                'project_name': project_name
            })

        return {
            'success': True,
            'user_email': user_email,
            'user_gid': user_gid,
            'tasks': output_tasks,
            'error': None
        }

    def _matches_filter(self, task: Dict[str, Any], filter_config: Dict[str, Any]) -> bool:
        """
        Check if task matches filter conditions (OR logic)

        Args:
            task: Task object from API
            filter_config: Filter configuration

        Returns:
            True if task matches any filter condition
        """
        task_name = task.get('name', '').lower()

        # Condition 1: Task name exact matches (case-insensitive)
        target_task_names = [name.lower() for name in filter_config.get('match_task_names', [])]
        if task_name in target_task_names:
            return True

        # Condition 2: Section name contains keyword (case-insensitive)
        memberships = task.get('memberships', [])
        if memberships and len(memberships) > 0:
            section_name = memberships[0].get('section', {}).get('name', '').lower()
            section_keywords = [kw.lower() for kw in filter_config.get('match_sections_containing', [])]

            for keyword in section_keywords:
                if keyword in section_name:
                    return True

        return False
