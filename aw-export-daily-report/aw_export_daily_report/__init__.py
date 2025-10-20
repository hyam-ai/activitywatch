"""
ActivityWatch Daily Report Exporter
Custom module for exporting unified AFK + window tracking data
"""

from aw_export_daily_report.data_fetcher import ActivityDataFetcher
from aw_export_daily_report.report_formatter import DailyReportFormatter

__version__ = "0.1.0"
__all__ = ["ActivityDataFetcher", "DailyReportFormatter", "main"]


def main():
    """Main CLI entry point"""
    from aw_export_daily_report.__main__ import cli
    cli()
