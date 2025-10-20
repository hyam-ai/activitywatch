"""
Flask web server for daily activity review UI
"""

from flask import Flask, render_template, jsonify, request, send_from_directory
from flask_cors import CORS
from datetime import datetime, timedelta
from pathlib import Path
import os
import json
import requests
from dotenv import load_dotenv

from .data_fetcher import ActivityDataFetcher
from .timeline_analyzer import TimelineAnalyzer

app = Flask(__name__,
            template_folder='../web',
            static_folder='../web/static')
CORS(app)


@app.route('/')
def index():
    """Serve the review page"""
    return render_template('index.html')


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

        # Send to N8N webhook
        webhook_url = "https://wins-n8n.zeabur.app/webhook/ai-tracker"
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
    Get all incomplete Asana tasks assigned to the current user
    
    Returns:
        JSON with tasks grouped by project
    """
    try:
        # Load environment variables
        env_path = Path(__file__).parent.parent / '.env'
        load_dotenv(env_path)
        
        ASANA_TOKEN = os.getenv('ASANA_PERSONAL_ACCESS_TOKEN')
        BASE_URL = "https://app.asana.com/api/1.0"
        
        if not ASANA_TOKEN:
            return jsonify({'error': 'ASANA_PERSONAL_ACCESS_TOKEN not found in .env file'}), 500
        
        headers = {
            "Authorization": f"Bearer {ASANA_TOKEN}"
        }
        
        # 1. Get workspace GID
        response = requests.get(f"{BASE_URL}/workspaces", headers=headers)
        workspaces = response.json()['data']
        
        if not workspaces:
            return jsonify({'error': 'No workspaces found'}), 404
        
        workspace_gid = workspaces[0]['gid']
        
        # 2. Get all tasks assigned to me with project details
        response = requests.get(
            f"{BASE_URL}/tasks",
            headers=headers,
            params={
                'assignee': 'me',
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


@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})


def run_server(host='0.0.0.0', port=8080, debug=True):
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

    app.run(host=host, port=port, debug=debug)