#!/usr/bin/env python3
"""
DevForge Sensing Dashboard - Quick view of system health with history.
"""

import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
import sys

class SensingDashboard:
    """Display and analyze sensor readings over time."""

    def __init__(self):
        self.sensors_dir = Path(__file__).parent
        self.reports_dir = self.sensors_dir / "reports"
        self.reports_dir.mkdir(exist_ok=True)

    def save_report(self, report: Dict[str, Any]):
        """Save report with timestamp."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.reports_dir / f"report_{timestamp}.json"
        with open(report_file, "w") as f:
            json.dump(report, f, indent=2)

    def load_latest_report(self) -> Dict[str, Any]:
        """Load latest report."""
        latest_file = self.sensors_dir / "latest_report.json"
        if latest_file.exists():
            return json.loads(latest_file.read_text())
        return None

    def get_health_trend(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get last N reports to show trend."""
        reports = sorted(self.reports_dir.glob("report_*.json"))[-limit:]
        return [json.loads(f.read_text()) for f in reports]

    def display_summary(self):
        """Display quick health summary."""
        report = self.load_latest_report()
        if not report:
            print("❌ No sensor reports found. Run: python sensors/monitor.py")
            return

        summary = report.get("summary", {})
        status = report.get("overall_status", "unknown")

        icon = "✅" if status == "healthy" else "⚠️" if status == "warning" else "❌"

        print("\n" + "="*70)
        print(f"DevForge Health Status: {icon} {status.upper()}")
        print("="*70)
        print(f"Healthy:  {summary.get('healthy', 0)}/6")
        print(f"Warnings: {summary.get('warning', 0)}/6")
        print(f"Critical: {summary.get('critical', 0)}/6")
        print(f"Last scan: {report.get('timestamp', 'unknown')}")
        print("="*70)

        # Show issues
        for reading in report.get("readings", []):
            if reading["status"] != "healthy":
                icon = "⚠️" if reading["status"] == "warning" else "❌"
                print(f"\n{icon} {reading['sensor_name']}")
                print(f"   {reading['message']}")

    def display_details(self, sensor_name: str = None):
        """Display detailed report."""
        report = self.load_latest_report()
        if not report:
            print("❌ No sensor reports found.")
            return

        print("\n" + "="*70)
        print("DETAILED SENSOR REPORT")
        print("="*70)

        for reading in report.get("readings", []):
            if sensor_name and sensor_name.lower() not in reading["sensor_name"].lower():
                continue

            icon = "✅" if reading["status"] == "healthy" else "⚠️" if reading["status"] == "warning" else "❌"
            print(f"\n{icon} {reading['sensor_name']}")
            print(f"   Status: {reading['status']}")
            print(f"   Message: {reading['message']}")

            if reading.get("auto_fix_attempted"):
                print(f"   🔧 Auto-fix attempted: {reading.get('fix_status', 'N/A')}")

            if reading.get("details"):
                print(f"   Details:")
                for key, value in reading["details"].items():
                    if isinstance(value, list):
                        print(f"      • {key}:")
                        for item in value:
                            print(f"        - {item}")
                    else:
                        print(f"      • {key}: {value}")

    def suggest_fixes(self):
        """Suggest fixes based on report."""
        report = self.load_latest_report()
        if not report:
            return

        fixes = {
            "Backend not running": [
                "1. Start backend: python main.py",
                "2. Or run all sensors to auto-start: python sensors/monitor.py"
            ],
            "Frontend not running": [
                "1. Start frontend: npm run dev",
                "2. Will run on http://localhost:3000"
            ],
            "node_modules not installed": [
                "1. Install dependencies: npm install",
                "2. Or run full setup: npm install && python -m pip install -r requirements.txt"
            ],
            "Python dependencies missing": [
                "1. Install Python deps: pip install -r requirements.txt",
                "2. Or use: pip install fastapi uvicorn requests pydantic"
            ],
            "Missing directory": [
                "1. Your project structure is incomplete",
                "2. Restore from git: git status"
            ]
        }

        print("\n" + "="*70)
        print("💡 SUGGESTED FIXES")
        print("="*70)

        for reading in report.get("readings", []):
            if reading["status"] != "healthy":
                message = reading["message"]
                for trigger, fix_steps in fixes.items():
                    if trigger.lower() in message.lower():
                        print(f"\n🔧 {reading['sensor_name']}:")
                        for step in fix_steps:
                            print(f"   {step}")
                        break
                else:
                    # Generic message
                    print(f"\n❓ {reading['sensor_name']}:")
                    print(f"   {message}")
                    print(f"   Details: {json.dumps(reading.get('details', {}), indent=2)}")

    def show_trends(self):
        """Show historical trends."""
        reports = self.get_health_trend()
        if len(reports) < 2:
            print("📊 Not enough reports for trend analysis. Run monitor.py multiple times.")
            return

        print("\n" + "="*70)
        print("📊 HEALTH TRENDS (Last 10 scans)")
        print("="*70)

        for i, report in enumerate(reports[-10:]):
            summary = report.get("summary", {})
            status_icon = "✅" if report.get("overall_status") == "healthy" else "⚠️" if report.get("overall_status") == "warning" else "❌"
            timestamp = report.get("timestamp", "")[-8:]  # Last 8 chars (time)
            healthy = summary.get("healthy", 0)
            print(f"{status_icon} {timestamp} | Health: {healthy}/6")


def main():
    """CLI for dashboard."""
    import argparse

    parser = argparse.ArgumentParser(description="DevForge Sensing Dashboard")
    parser.add_argument("--summary", action="store_true", default=True, help="Show health summary (default)")
    parser.add_argument("--details", nargs="?", const=True, metavar="SENSOR", help="Show detailed report (optionally for specific sensor)")
    parser.add_argument("--fixes", action="store_true", help="Show suggested fixes")
    parser.add_argument("--trends", action="store_true", help="Show health trends")
    parser.add_argument("--full", action="store_true", help="Show everything")

    args = parser.parse_args()

    dashboard = SensingDashboard()

    if args.full:
        dashboard.display_summary()
        dashboard.display_details()
        dashboard.suggest_fixes()
        dashboard.show_trends()
    elif args.details is not None:
        sensor_name = args.details if isinstance(args.details, str) else None
        dashboard.display_details(sensor_name)
    elif args.fixes:
        dashboard.suggest_fixes()
    elif args.trends:
        dashboard.show_trends()
    else:
        dashboard.display_summary()
        print("\nRun with --help for more options:")
        print("  python sensors/dashboard.py --details     # Show all details")
        print("  python sensors/dashboard.py --details Backend  # Show specific sensor")
        print("  python sensors/dashboard.py --fixes       # Show suggested fixes")
        print("  python sensors/dashboard.py --trends      # Show health trends")
        print("  python sensors/dashboard.py --full        # Show everything")


if __name__ == "__main__":
    main()
