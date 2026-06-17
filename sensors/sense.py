#!/usr/bin/env python3
"""
DevForge Sensing System - Unified CLI entry point.
Run diagnostics, view dashboard, and get health insights.

Usage:
    python sensors/sense.py                    # Run full diagnostic + show dashboard
    python sensors/sense.py monitor           # Run full diagnostic only
    python sensors/sense.py dashboard         # Show dashboard only
    python sensors/sense.py dashboard --fixes # Show dashboard with fix suggestions
"""

import sys
import subprocess
from pathlib import Path

def run_monitor():
    """Run monitoring system."""
    print("\n🔍 Starting DevForge Sensing System...\n")
    result = subprocess.run([sys.executable, "sensors/monitor.py"], cwd=Path(__file__).parent.parent)
    return result.returncode

def run_dashboard(args: list = None):
    """Run dashboard."""
    cmd = [sys.executable, "sensors/dashboard.py"]
    if args:
        cmd.extend(args)
    return subprocess.run(cmd, cwd=Path(__file__).parent.parent).returncode

def main():
    """CLI entrypoint."""
    if len(sys.argv) < 2:
        # Default: run monitor + dashboard
        print("\n" + "="*70)
        print("DevForge Sensing System - Full Diagnostic + Dashboard")
        print("="*70)

        # Run monitor
        returncode = run_monitor()

        # Then run dashboard
        print("\n")
        run_dashboard(["--summary"])

        sys.exit(returncode)

    elif sys.argv[1] == "monitor":
        sys.exit(run_monitor())

    elif sys.argv[1] == "dashboard":
        args = sys.argv[2:] if len(sys.argv) > 2 else ["--summary"]
        sys.exit(run_dashboard(args))

    elif sys.argv[1] in ["-h", "--help"]:
        print(__doc__)

    else:
        print(f"Unknown command: {sys.argv[1]}")
        print(__doc__)
        sys.exit(1)

if __name__ == "__main__":
    main()
