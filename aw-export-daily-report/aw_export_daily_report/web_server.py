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
from collections import defaultdict

from aw_export_daily_report.data_fetcher import ActivityDataFetcher
from aw_export_daily_report.timeline_analyzer import TimelineAnalyzer
from aw_export_daily_report.config import SettingsManager
from aw_export_daily_report.asana_client import AsanaClient

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
        
        # Check if email changed
        old_settings = manager.load_settings()
        old_email = old_settings.get('user', {}).get('email', '')
        new_email = settings.get('user', {}).get('email', '')
        email_changed = old_email != new_email
        
        success, errors = manager.save_settings(settings)
        
        if success:
            return jsonify({
                'success': True,
                'email_changed': email_changed
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


@app.route('/api/asana/tasks', methods=['GET'])
def get_asana_tasks():
    """
    Get Asana tasks for user by email
    
    Query params:
        email: User email address (required)
        refresh: Force cache refresh (optional, default: false)
        
    Returns:
        JSON with tasks list or error
    """
    try:
        # Get email from query params
        email = request.args.get('email')
        force_refresh = request.args.get('refresh', 'false').lower() == 'true'
        
        if not email:
            return jsonify({
                'success': False,
                'error': 'Email parameter is required',
                'tasks': [],
                'cached': False
            }), 400
        
        # Load settings
        settings_manager = SettingsManager()
        
        # Check if Asana is enabled
        if not settings_manager.is_asana_enabled():
            return jsonify({
                'success': False,
                'error': 'Asana integration is not enabled in settings',
                'tasks': [],
                'cached': False
            }), 400
        
        # Get Asana token
        token = settings_manager.get_asana_token()
        
        if not token:
            return jsonify({
                'success': False,
                'error': 'Asana token not configured in settings',
                'tasks': [],
                'cached': False
            }), 400
        
        # Check cache first (unless force refresh)
        if not force_refresh:
            cached_tasks = settings_manager.get_cached_tasks(email, ttl_seconds=1800)  # 30 minutes
            if cached_tasks is not None:
                print(f"✓ Returning {len(cached_tasks)} cached tasks for {email}")
                return jsonify({
                    'success': True,
                    'user_email': email,
                    'tasks': cached_tasks,
                    'cached': True,
                    'error': None
                })
        
        # Cache miss or force refresh - fetch from Asana API
        print(f"⟳ Fetching fresh tasks from Asana API for {email}...")
        
        # Initialize Asana client
        asana_client = AsanaClient(token)
        
        # Get task filters
        filters = settings_manager.get_asana_filters()
        
        # Fetch tasks
        result = asana_client.get_filtered_tasks(email, filters)
        
        # Cache user GID if successful
        if result['success'] and result.get('user_gid'):
            settings_manager.set_asana_user_gid(result['user_gid'])
        
        # Cache tasks if successful
        if result['success'] and result.get('tasks'):
            settings_manager.set_cached_tasks(email, result['tasks'])
            print(f"✓ Cached {len(result['tasks'])} tasks for {email}")
        
        # Add cached flag to response
        result['cached'] = False
        
        return jsonify(result)
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e),
            'tasks': [],
            'cached': False
        }), 500


@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})



def aggregate_by_duration(unified_data):
    """
    Aggregate activities grouped by app, sorted by duration
    
    Args:
        unified_data: List of activity events with app, title, duration, afk fields
        
    Returns:
        Dict with apps list: [{app, total_duration, activities: [{title, duration}]}]
    """
    MIN_ACTIVITY_SECONDS = 60  # Filter out activities shorter than 1 minute for summary display
    AFK_THRESHOLD_SECONDS = 120  # Only exclude AFK periods >= 2 minutes (matches timeline_analyzer)
    
    # Filter active events only (matches timeline_analyzer logic)
    active_events = [
        event for event in unified_data
        if not (event.get('afk', False) and float(event.get('duration', 0)) >= AFK_THRESHOLD_SECONDS)
        and event.get('app', '') != 'loginwindow'
        and float(event.get('duration', 0)) >= MIN_ACTIVITY_SECONDS
    ]
    
    # Group by app, then aggregate activities within each app
    apps_data = defaultdict(lambda: defaultdict(float))
    
    for event in active_events:
        app = event.get('app', 'Unknown')
        title = event.get('title', 'Unknown')
        duration = float(event.get('duration', 0))
        
        apps_data[app][title] += duration
    
    # Structure data: calculate app totals and sort
    apps_list = []
    
    for app, activities_dict in apps_data.items():
        # Convert activities to list and sort by duration
        activities = [
            {'title': title, 'duration': duration}
            for title, duration in activities_dict.items()
        ]
        activities.sort(key=lambda x: x['duration'], reverse=True)
        
        # Calculate total duration for this app
        total_duration = sum(a['duration'] for a in activities)
        
        apps_list.append({
            'app': app,
            'total_duration': total_duration,
            'activities': activities
        })
    
    # Sort apps by total duration (descending)
    apps_list.sort(key=lambda x: x['total_duration'], reverse=True)
    
    return apps_list


@app.route('/api/summary/<date>')
def get_summary(date):
    """
    Get activity summary grouped by app, sorted by duration
    
    Args:
        date: YYYY-MM-DD format
        
    Returns:
        JSON with apps and their activities sorted by duration descending
    """
    try:
        # Parse date
        target_date = datetime.strptime(date, '%Y-%m-%d')
        
        # Fetch data
        fetcher = ActivityDataFetcher()
        unified_data = fetcher.get_unified_daily_data(target_date)
        
        if not unified_data:
            return jsonify({'error': 'No data found for date'}), 404
        
        # Aggregate and group by app
        apps_data = aggregate_by_duration(unified_data)
        
        # Calculate total active time
        total_duration = sum(app['total_duration'] for app in apps_data)
        
        return jsonify({
            'date': date,
            'apps': apps_data,
            'total_active_time': total_duration
        })
        
    except ValueError as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Invalid date format: {e}'}), 400
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


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