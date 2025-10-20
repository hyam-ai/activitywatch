#!/usr/bin/env python3
"""
Test script to get all tasks assigned to me with their projects (Option 1)
"""

import requests
import json
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent / '.env'
load_dotenv(env_path)

ASANA_TOKEN = os.getenv('ASANA_PERSONAL_ACCESS_TOKEN')
BASE_URL = "https://app.asana.com/api/1.0"

def get_my_tasks_with_projects():
    if not ASANA_TOKEN:
        print("❌ ASANA_PERSONAL_ACCESS_TOKEN not found in .env file")
        return

    headers = {
        "Authorization": f"Bearer {ASANA_TOKEN}"
    }

    print("=" * 80)
    print("MY TASKS WITH PROJECTS")
    print("=" * 80)

    # 1. Get workspace GID first
    print("\n1. Getting workspace...")
    response = requests.get(f"{BASE_URL}/workspaces", headers=headers)
    workspaces = response.json()['data']

    if not workspaces:
        print("❌ No workspaces found")
        return

    workspace_gid = workspaces[0]['gid']
    workspace_name = workspaces[0]['name']
    print(f"✅ Using workspace: {workspace_name} (GID: {workspace_gid})")

    # 2. Get all tasks assigned to me with project details
    print("\n2. Fetching tasks assigned to me...")
    response = requests.get(
        f"{BASE_URL}/tasks",
        headers=headers,
        params={
            'assignee': 'me',
            'workspace': workspace_gid,
            'opt_fields': 'name,completed,due_on,projects.name,memberships.project.name,memberships.section.name',
            'limit': 100  # Adjust as needed
        }
    )

    if response.status_code != 200:
        print(f"❌ API request failed: {response.status_code}")
        print(response.text)
        return

    tasks = response.json()['data']
    print(f"✅ Found {len(tasks)} task(s) assigned to you")
    print()

    # 3. Organize tasks by project
    tasks_by_project = {}
    tasks_without_project = []

    for task in tasks:
        projects = task.get('projects', [])

        if not projects:
            tasks_without_project.append(task)
        else:
            for project in projects:
                project_name = project.get('name', 'Unknown Project')
                if project_name not in tasks_by_project:
                    tasks_by_project[project_name] = []
                tasks_by_project[project_name].append(task)

    # 4. Display results grouped by project
    print("=" * 80)
    print("TASKS GROUPED BY PROJECT")
    print("=" * 80)

    for project_name in sorted(tasks_by_project.keys()):
        project_tasks = tasks_by_project[project_name]
        print(f"\n📁 {project_name} ({len(project_tasks)} tasks)")
        print("-" * 80)

        for task in project_tasks:
            status = "✓" if task.get('completed') else "○"
            name = task['name']
            due_on = task.get('due_on', 'No due date')

            # Get section info if available
            memberships = task.get('memberships', [])
            section_info = ""
            if memberships:
                sections = [m.get('section', {}).get('name') for m in memberships if m.get('section')]
                if sections:
                    section_info = f" [{', '.join(sections)}]"

            print(f"  {status} {name}{section_info}")
            if due_on != 'No due date':
                print(f"    Due: {due_on}")

    # 5. Display tasks without projects
    if tasks_without_project:
        print(f"\n📋 TASKS WITHOUT PROJECT ({len(tasks_without_project)} tasks)")
        print("-" * 80)
        for task in tasks_without_project:
            status = "✓" if task.get('completed') else "○"
            name = task['name']
            due_on = task.get('due_on', 'No due date')
            print(f"  {status} {name}")
            if due_on != 'No due date':
                print(f"    Due: {due_on}")

    # 6. Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total tasks assigned to you: {len(tasks)}")
    print(f"Projects with your tasks: {len(tasks_by_project)}")
    print(f"Tasks without project: {len(tasks_without_project)}")

    # Completion stats
    completed = sum(1 for t in tasks if t.get('completed'))
    incomplete = len(tasks) - completed
    print(f"\nCompleted: {completed}")
    print(f"Incomplete: {incomplete}")

    # 7. Save detailed JSON output
    output_file = Path(__file__).parent / 'my_tasks_with_projects.json'
    with open(output_file, 'w') as f:
        json.dump(tasks, f, indent=2)
    print(f"\n💾 Full task data saved to: {output_file}")

if __name__ == "__main__":
    get_my_tasks_with_projects()
