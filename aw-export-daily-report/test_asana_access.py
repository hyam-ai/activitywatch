#!/usr/bin/env python3
"""
Get all tasks assigned to me with their projects
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
        print("\nPlease create a .env file with:")
        print("ASANA_PERSONAL_ACCESS_TOKEN=your_token_here")
        print("\nGet your token at: https://app.asana.com/0/my-apps")
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
    print("\n2. Fetching incomplete tasks assigned to me...")
    response = requests.get(
        f"{BASE_URL}/tasks",
        headers=headers,
        params={
            'assignee': 'me',
            'workspace': workspace_gid,
            # Don't use 'completed' parameter - it breaks projects field in API response
            'opt_fields': 'name,completed,due_on,projects.name,memberships.project.name,memberships.section.name,num_subtasks',
            'limit': 100  # Adjust as needed
        }
    )

    if response.status_code != 200:
        print(f"❌ API request failed: {response.status_code}")
        print(response.text)
        return

    tasks = response.json()['data']
    
    # Filter out any completed tasks (client-side filtering)
    tasks = [task for task in tasks if not task.get('completed', False)]
    
    print(f"✅ Found {len(tasks)} incomplete task(s) assigned to you")
    
    # 3. Fetch subtasks for tasks that have them
    print("\n3. Fetching subtasks...")
    all_tasks = []
    for task in tasks:
        all_tasks.append(task)
        
        # Check if task has subtasks
        num_subtasks = task.get('num_subtasks', 0)
        if num_subtasks > 0:
            subtasks_response = requests.get(
                f"{BASE_URL}/tasks/{task['gid']}/subtasks",
                headers=headers,
                params={
                    'opt_fields': 'name,completed,due_on,projects.name,memberships.project.name,memberships.section.name'
                }
            )
            
            if subtasks_response.status_code == 200:
                subtasks = subtasks_response.json()['data']
                # Filter incomplete subtasks
                incomplete_subtasks = [st for st in subtasks if not st.get('completed', False)]
                
                # Inherit parent's projects and memberships for subtasks without them
                for subtask in incomplete_subtasks:
                    if not subtask.get('projects'):
                        subtask['projects'] = task.get('projects', [])
                    if not subtask.get('memberships'):
                        subtask['memberships'] = task.get('memberships', [])
                
                all_tasks.extend(incomplete_subtasks)
    
    tasks = all_tasks
    print(f"✅ Total tasks + subtasks: {len(tasks)}")
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
    print(f"Total incomplete tasks: {len(tasks)}")
    print(f"Projects with your tasks: {len(tasks_by_project)}")
    print(f"Tasks without project: {len(tasks_without_project)}")

    # 7. Save detailed JSON output
    output_file = Path(__file__).parent / 'my_tasks_with_projects.json'
    with open(output_file, 'w') as f:
        json.dump(tasks, f, indent=2)
    print(f"\n💾 Full task data saved to: {output_file}")

if __name__ == "__main__":
    get_my_tasks_with_projects()