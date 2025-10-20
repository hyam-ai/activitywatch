"""
Flask web server for daily activity review UI
"""

from flask import Flask, render_template, jsonify, request, send_from_directory
from flask_cors import CORS
from datetime import datetime, timedelta
from pathlib import Path
import os
import sys
import json
import requests
from dotenv import load_dotenv

from aw_export_daily_report.data_fetcher import ActivityDataFetcher
from aw_export_daily_report.timeline_analyzer import TimelineAnalyzer
from aw_export_daily_report.config import SettingsManager

# Detect if running as PyInstaller bundle or in dev mode
if getattr(sys, 'frozen', False):
    # Running as PyInstaller bundle
    # Templates are in: Contents/Resources/aw_export_daily_report/web/
    base_path = Path(sys._MEIPASS)
    template_folder = base_path / 'aw_export_daily_report' / 'web'
    static_folder = base_path / 'aw_export_daily_report' / 'web' / 'static'
else:
    # Running in dev mode
    base_path = Path(__file__).parent.parent
    template_folder = base_path / 'web'
    static_folder = base_path / 'web' / 'static'

app = Flask(__name__,
            template_folder=str(template_folder),
            static_folder=str(static_folder))
CORS(app)


@app.route('/')
def index():
    """Serve the review page"""
    return render_template('index.html')


@app.route('/settings')
def settings_page():
    """Serve the settings page"""
    return render_template('settings.html')


@app.route('/api/activity/<date>')
def get_activity(date):
    """
    Get activity data for a specific date

    Args:
        date: YYYY-MM-DD format

    Returns:
        JSON with categorized activity data
    """
    try:
        # Parse date
        target_date = datetime.strptime(date, '%Y-%m-%d')

        # Fetch data
        fetcher = ActivityDataFetcher()
        unified_data = fetcher.get_unified_daily_data(target_date)

        if not unified_data:
            return jsonify({'error': 'No data found for date'}), 404

        # Use timeline analyzer for web UI
        analyzer = TimelineAnalyzer(unified_data)
        data = analyzer.analyze()

        return jsonify(data)

    except ValueError as e:
        return jsonify({'error': f'Invalid date format: {e}'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/activity/today')
def get_today():
    """Get today's activity"""
    today = datetime.now().strftime('%Y-%m-%d')
    return get_activity(today)


@app.route('/api/activity/yesterday')
def get_yesterday():
    """Get yesterday's activity"""
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    return get_activity(yesterday)


@app.route('/api/timeline/<date>')
def get_timeline(date):
    """
    Get timeline-based activity data for a specific date

    Args:
        date: YYYY-MM-DD format

    Returns:
        JSON with timeline blocks showing main and supporting activities
    """
    try:
        # Parse date
        target_date = datetime.strptime(date, '%Y-%m-%d')

        # Fetch data
        fetcher = ActivityDataFetcher()
        unified_data = fetcher.get_unified_daily_data(target_date)

        if not unified_data:
            return jsonify({'error': 'No data found for date'}), 404

        # Analyze timeline
        analyzer = TimelineAnalyzer(unified_data)
        timeline_data = analyzer.analyze()

        return jsonify(timeline_data)

    except ValueError as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Invalid date format: {e}'}), 400
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/timeline/yesterday')
def get_timeline_yesterday():
    """Get yesterday's timeline"""
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    return get_timeline(yesterday)


@app.route('/api/submit', methods=['POST'])
def submit_activity():
    """
    Submit selected activities and save to analysis folder
    
    Expected payload:
    {
        "user": {"email": "user@example.com"},
        "timeline": [
            {
                "activity": "...",
                "start_time_utc": "...",
                "end_time_utc": "...",
                "duration_seconds": 123,
                "notes": "...",
                "sub_tasks": [...]
            }
        ]
    }
    """
    try:
        data = request.json
        
        # Create analysis folder if it doesn't exist
        project_root = Path(__file__).parent.parent
        analysis_dir = project_root / 'analysis'
        analysis_dir.mkdir(exist_ok=True)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = analysis_dir / f'export_{timestamp}.json'
        
        # Save JSON file
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"✓ Export saved to: {filename}")

        # Send to N8N webhook (only if enabled in settings)
        settings_manager = SettingsManager()
        settings = settings_manager.load_settings()
        webhook_enabled = settings.get('integrations', {}).get('n8n', {}).get('enabled', True)
        webhook_url = settings.get('integrations', {}).get('n8n', {}).get('webhook_url', '')
        
        webhook_status = "disabled"
        
        if webhook_enabled and webhook_url:
            try:
                import requests
                webhook_response = requests.post(
                    webhook_url,
                    json=data,
                    headers={'Content-Type': 'application/json'},
                    timeout=10
                )
                webhook_response.raise_for_status()
                print(f"✓ Data sent to webhook: {webhook_url}")
                webhook_status = "success"
            except Exception as webhook_error:
                print(f"✗ Webhook failed: {webhook_error}")
                webhook_status = f"failed: {str(webhook_error)}"
        else:
            print("ℹ Webhook disabled in settings")

        return jsonify({
            'success': True,
            'message': 'Activity report submitted successfully',
            'saved_to': str(filename),
            'webhook_status': webhook_status
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/asana/tasks')
def get_asana_tasks():
    """
    Get all incomplete Asana tasks assigned to the user (by email from settings)
    
    Returns:
        JSON with tasks grouped by project
    """
    try:
        # Load environment variables - handle both dev and PyInstaller bundle
        if getattr(sys, 'frozen', False):
            # Running as PyInstaller bundle
            env_path = Path(sys._MEIPASS) / 'aw_export_daily_report' / '.env'
        else:
            # Running in dev mode
            env_path = Path(__file__).parent.parent / '.env'

        load_dotenv(env_path)
        
        ASANA_TOKEN = os.getenv('ASANA_PERSONAL_ACCESS_TOKEN')
        BASE_URL = "https://app.asana.com/api/1.0"
        
        if not ASANA_TOKEN:
            return jsonify({'error': 'ASANA_PERSONAL_ACCESS_TOKEN not found in .env file'}), 500
        
        headers = {
            "Authorization": f"Bearer {ASANA_TOKEN}"
        }
        
        # Load settings to get user email and cached GID
        settings_manager = SettingsManager()
        settings = settings_manager.load_settings()
        user_email = settings.get('user', {}).get('email', '')
        cached_gid = settings.get('user', {}).get('asana_gid')
        
        if not user_email:
            return jsonify({'error': 'User email not configured in settings'}), 400
        
        # 1. Get workspace GID
        response = requests.get(f"{BASE_URL}/workspaces", headers=headers)
        workspaces = response.json()['data']
        
        if not workspaces:
            return jsonify({'error': 'No workspaces found'}), 404
        
        workspace_gid = workspaces[0]['gid']
        
        # 2. Get or lookup user GID from email
        user_gid = cached_gid
        
        # If no cached GID or email changed, lookup user by email
        if not user_gid:
            print(f"Looking up Asana user GID for email: {user_email}")
            users_response = requests.get(
                f"{BASE_URL}/workspaces/{workspace_gid}/users",
                headers=headers,
                params={
                    'opt_fields': 'name,email'  # Request email field
                }
            )
            
            if users_response.status_code == 200:
                workspace_users = users_response.json()['data']
                # Find user by email
                matching_user = next(
                    (u for u in workspace_users if u.get('email', '').lower() == user_email.lower()),
                    None
                )
                
                if matching_user:
                    user_gid = matching_user['gid']
                    # Cache the GID for future requests
                    settings_manager.set_user_asana_gid(user_gid)
                    print(f"✓ Found and cached user GID: {user_gid}")
                else:
                    return jsonify({'error': f'No Asana user found with email: {user_email}'}), 404
            else:
                return jsonify({'error': f'Failed to fetch workspace users: {users_response.status_code}'}), 500
        
        # 3. Get all tasks assigned to this user with project details
        response = requests.get(
            f"{BASE_URL}/tasks",
            headers=headers,
            params={
                'assignee': user_gid,  # Use GID instead of 'me'
                'workspace': workspace_gid,
                'opt_fields': 'name,completed,due_on,projects.name,memberships.project.name,memberships.section.name,num_subtasks',
                'limit': 100
            }
        )
        
        if response.status_code != 200:
            return jsonify({'error': f'Asana API request failed: {response.status_code}'}), 500
        
        tasks = response.json()['data']
        
        # Filter out completed tasks (client-side filtering)
        tasks = [task for task in tasks if not task.get('completed', False)]
        
        # 3. Fetch subtasks for tasks that have them
        all_tasks = []
        for task in tasks:
            all_tasks.append(task)
            
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
                    incomplete_subtasks = [st for st in subtasks if not st.get('completed', False)]
                    
                    # Inherit parent's projects and memberships for subtasks without them
                    for subtask in incomplete_subtasks:
                        if not subtask.get('projects'):
                            subtask['projects'] = task.get('projects', [])
                        if not subtask.get('memberships'):
                            subtask['memberships'] = task.get('memberships', [])
                    
                    all_tasks.extend(incomplete_subtasks)
        
        tasks = all_tasks
        
        # 4. Organize tasks by project
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
        
        # 5. Format response
        return jsonify({
            'tasks_by_project': tasks_by_project,
            'tasks_without_project': tasks_without_project,
            'total_tasks': len(tasks)
        })
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/settings', methods=['GET'])
def get_settings():
    """
    Get current user settings

    Returns:
        JSON with user settings (email, timezone, work_schedule, integrations)
    """
    try:
        manager = SettingsManager()
        settings = manager.load_settings()
        return jsonify(settings)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/settings', methods=['POST'])
def save_settings():
    """Save user settings with validation"""
    try:
        settings = request.json
        manager = SettingsManager()
        
        # Check if email changed - invalidate cached Asana GID
        old_settings = manager.load_settings()
        old_email = old_settings.get('user', {}).get('email', '')
        new_email = settings.get('user', {}).get('email', '')
        
        if old_email != new_email:
            # Email changed - clear cached Asana GID to force re-lookup
            settings['user']['asana_gid'] = None
            print(f"Email changed from '{old_email}' to '{new_email}' - clearing cached Asana GID")
        
        success, errors = manager.save_settings(settings)
        
        if success:
            return jsonify({
                'success': True,
                'email_changed': old_email != new_email  # Signal to frontend
            })
        else:
            return jsonify({
                'success': False,
                'errors': errors
            })
    except Exception as e:
        return jsonify({
            'success': False,
            'errors': [str(e)]
        }), 500


@app.route('/api/timezones', methods=['GET'])
def get_timezones():
    """
    Get list of common timezones for dropdown

    Returns:
        List of IANA timezone strings
    """
    # Common timezones for dropdown
    timezones = [
        "Europe/Berlin",
        "Europe/Istanbul",
        "Europe/London",
        "Europe/Paris",
        "Europe/Amsterdam",
        "Europe/Madrid",
        "Europe/Rome",
        "America/New_York",
        "America/Chicago",
        "America/Los_Angeles",
        "America/Toronto",
        "Asia/Tokyo",
        "Asia/Shanghai",
        "Asia/Singapore",
        "Australia/Sydney",
        "UTC"
    ]
    return jsonify(timezones)


@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})


def run_server(host='0.0.0.0', port=9999, debug=False):
    """Run the Flask development server"""
    print(f"""
╔══════════════════════════════════════════════════════════╗
║  ActivityWatch Daily Review Server                      ║
╚══════════════════════════════════════════════════════════╝

🌐 Server running at: http://{host}:{port}
📊 Review page: http://localhost:{port}
🔌 API endpoints:
   - GET  /api/activity/today
   - GET  /api/activity/yesterday
   - GET  /api/activity/<date>
   - GET  /api/timeline/yesterday  [NEW - Timeline view]
   - GET  /api/timeline/<date>     [NEW - Timeline view]
   - POST /api/submit

Press Ctrl+C to stop the server
    """)

    # Disable reloader for PyInstaller bundles (causes crashes)
    app.run(host=host, port=port, debug=debug, use_reloader=False)