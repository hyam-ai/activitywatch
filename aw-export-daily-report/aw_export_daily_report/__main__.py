"""
Command-line interface for daily report exporter
"""

import click
from datetime import datetime, timedelta
from .data_fetcher import ActivityDataFetcher
from .report_formatter import DailyReportFormatter


@click.group()
def cli():
    """ActivityWatch Daily Report Exporter"""
    pass


@cli.command()
@click.option('--date', default=None, help='Date to export (YYYY-MM-DD), defaults to today')
@click.option('--format', 'output_format', default='text',
              type=click.Choice(['json', 'text', 'markdown', 'csv']),
              help='Output format')
@click.option('--output', '-o', default=None, help='Output filename (optional)')
@click.option('--print', 'print_output', is_flag=True, help='Print to stdout instead of file')
def export(date, output_format, output, print_output):
    """
    Export unified daily activity report

    Examples:
        aw-export-daily-report export
        aw-export-daily-report export --format markdown --print
        aw-export-daily-report export --date 2025-10-15 --format json -o report.json
    """
    # Parse date
    if date:
        try:
            target_date = datetime.strptime(date, '%Y-%m-%d')
        except ValueError:
            click.echo(f"Error: Invalid date format. Use YYYY-MM-DD")
            return
    else:
        target_date = datetime.now()

    click.echo(f"Fetching data for {target_date.strftime('%Y-%m-%d')}...")

    # Fetch data
    fetcher = ActivityDataFetcher()
    try:
        unified_data = fetcher.get_unified_daily_data(target_date)
    except Exception as e:
        click.echo(f"Error fetching data: {e}")
        return

    if not unified_data:
        click.echo("No data found for the specified date.")
        return

    click.echo(f"Found {len(unified_data)} events. Generating report...")

    # Format report
    formatter = DailyReportFormatter(unified_data)

    if print_output:
        # Print to stdout
        if output_format == 'json':
            content = formatter.format_as_json()
        elif output_format == 'markdown':
            content = formatter.format_as_markdown()
        elif output_format == 'csv':
            content = formatter.format_as_csv()
        else:  # text
            content = formatter.format_as_text_summary()

        click.echo("\n" + content)
    else:
        # Export to file
        try:
            filename = formatter.export_to_file(output_format, output)
            click.echo(f"✓ Report exported to: {filename}")
        except Exception as e:
            click.echo(f"Error exporting report: {e}")


@cli.command()
def test():
    """Test connection to ActivityWatch server and show available buckets"""
    click.echo("Testing connection to ActivityWatch...")

    fetcher = ActivityDataFetcher()

    try:
        buckets = fetcher.get_buckets()
        click.echo(f"✓ Connected successfully!")
        click.echo(f"\nFound {len(buckets)} bucket(s):")

        for bucket_id, bucket_info in buckets.items():
            click.echo(f"  • {bucket_id} ({bucket_info['type']})")

        try:
            window_bucket = fetcher.find_window_bucket()
            click.echo(f"\n✓ Window watcher bucket: {window_bucket}")
        except ValueError as e:
            click.echo(f"\n✗ {e}")

        try:
            afk_bucket = fetcher.find_afk_bucket()
            click.echo(f"✓ AFK watcher bucket: {afk_bucket}")
        except ValueError as e:
            click.echo(f"✗ {e}")

    except Exception as e:
        click.echo(f"✗ Connection failed: {e}")
        click.echo("\nMake sure ActivityWatch server is running on http://localhost:5600")


@cli.command()
@click.option('--date', default=None, help='Date to show stats for (YYYY-MM-DD)')
def stats(date):
    """Show quick statistics for a day"""
    # Parse date
    if date:
        try:
            target_date = datetime.strptime(date, '%Y-%m-%d')
        except ValueError:
            click.echo(f"Error: Invalid date format. Use YYYY-MM-DD")
            return
    else:
        target_date = datetime.now()

    fetcher = ActivityDataFetcher()
    unified_data = fetcher.get_unified_daily_data(target_date)

    if not unified_data:
        click.echo("No data found for the specified date.")
        return

    formatter = DailyReportFormatter(unified_data)
    stats = formatter.calculate_stats()

    click.echo(f"\nStatistics for {target_date.strftime('%Y-%m-%d')}:")
    click.echo(f"  Total time: {stats['total_time_hours']:.2f}h")
    click.echo(f"  Active time: {stats['active_time_hours']:.2f}h ({stats['active_percentage']:.1f}%)")
    click.echo(f"  AFK time: {stats['afk_time_hours']:.2f}h")
    click.echo(f"\nTop 3 apps:")
    for i, (app, duration) in enumerate(stats['top_apps'][:3], 1):
        hours = duration / 3600
        click.echo(f"  {i}. {app}: {hours:.2f}h")




@cli.command()
@click.option('--host', default='0.0.0.0', help='Host to bind to')
@click.option('--port', default=9999, help='Port to run on')
@click.option('--debug/--no-debug', default=True, help='Enable debug mode')
def web(host, port, debug):
    """
    Start the web UI server for activity review
    
    Examples:
        aw-export-daily-report web
        aw-export-daily-report web --port 3000
        aw-export-daily-report web --host localhost --port 9999
    """
    from .web_server import run_server
    run_server(host=host, port=port, debug=debug)


if __name__ == '__main__':
    cli()