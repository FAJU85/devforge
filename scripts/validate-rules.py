#!/usr/bin/env python3
"""
DevForge Static Rules Validator

Checks for anti-patterns documented in CLAUDE.md and STATIC_CHECKS_GUIDE.md
without requiring Semgrep installation.

Usage:
    python scripts/validate-rules.py [--fix] [--verbose]
"""

import os
import re
import sys
from pathlib import Path
from typing import List, Tuple

# ANSI colors
RED = '\033[91m'
YELLOW = '\033[93m'
GREEN = '\033[92m'
RESET = '\033[0m'

class RuleValidator:
    def __init__(self, root_dir: str = "."):
        self.root = Path(root_dir)
        self.issues: List[Tuple[str, str, int, str]] = []
        self.verbose = False

    def log(self, message: str, level: str = "INFO"):
        """Log a message based on verbosity level."""
        if level == "ERROR" or level == "WARNING" or self.verbose:
            print(message)

    def check_fabricated_metrics(self, filepath: Path, content: str) -> int:
        """Check for hardcoded metrics without command execution."""
        count = 0

        # Patterns that indicate fake metrics
        fake_metric_patterns = [
            r'print\(["\'].*?(\d+\.?\d*\s*%|improved by \d+)',  # "improved by 45%"
            r'return\s*{[^}]*"(latency|throughput|improvement)"[^}]*:\s*\d+',  # hardcoded numbers
            r'print\(["\'].*?(latency|throughput|cache hit|error rate).*?\d+',  # metric claims
        ]

        for pattern in fake_metric_patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                line_no = content[:match.start()].count('\n') + 1
                # Check if the number comes from an actual command
                context_start = max(0, match.start() - 200)
                context = content[context_start:match.start()]

                if not any(cmd in context for cmd in ['subprocess.run', 'os.popen', '.execute(', 'time.time()']):
                    self.issues.append((
                        str(filepath),
                        "avoid-fake-metrics",
                        line_no,
                        f"Hardcoded metric: {match.group(0)[:50]}... (must come from command)"
                    ))
                    count += 1

        return count

    def check_unverified_claims(self, filepath: Path, content: str) -> int:
        """Check for claims without verification commands."""
        count = 0

        # Patterns for unverified "done" claims
        claim_patterns = [
            (r'print\(["\']✅.*?complete', "emoji-laden 'complete' claim without verification"),
            (r'print\(["\'].*?working["\']', "claiming 'working' without verification"),
            (r'return\s*{[^}]*"status"\s*:\s*"done"', "returning 'done' status without verification"),
        ]

        for pattern, reason in claim_patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                line_no = content[:match.start()].count('\n') + 1

                # Check if verification follows (pytest, curl, python -c, etc.)
                context_after = content[match.end():min(len(content), match.end() + 500)]
                verification_commands = [
                    'pytest', 'test_', 'curl http', 'python -c "import',
                    'subprocess.run', 'execute', 'assert'
                ]

                if not any(cmd in context_after for cmd in verification_commands):
                    self.issues.append((
                        str(filepath),
                        "verify-before-claiming-complete",
                        line_no,
                        f"Claim without verification: {match.group(0)[:50]}..."
                    ))
                    count += 1

        return count

    def check_silent_failures(self, filepath: Path, content: str) -> int:
        """Check for exception handling without error logging."""
        count = 0

        # Pattern: try/except with pass or empty except
        pattern = r'except\s+(\w+\s+as\s+\w+)?:\s*(pass|continue|return\s*None|return\s*False)'

        matches = re.finditer(pattern, content)
        for match in matches:
            line_no = content[:match.start()].count('\n') + 1
            self.issues.append((
                str(filepath),
                "no-silent-failures",
                line_no,
                f"Silent exception handler: {match.group(0)[:50]} (must log error)"
            ))
            count += 1

        return count

    def check_orphaned_imports(self, filepath: Path, content: str) -> int:
        """Check for imports that aren't verified to be wired."""
        count = 0

        # Only check api/* files for potentially orphaned imports
        if 'api/' not in str(filepath) or filepath.name == '__init__.py':
            return 0

        # Pattern: New service imports without being used in main.py
        pattern = r'^from\s+(api\.|services\.)\s+import'

        matches = re.finditer(pattern, content, re.MULTILINE)
        for match in matches:
            line_no = content[:match.start()].count('\n') + 1

            # This is a warning to check main.py
            if 'try:' not in content[max(0, match.start()-100):match.start()]:
                self.issues.append((
                    str(filepath),
                    "no-orphaned-imports",
                    line_no,
                    f"Import without try/except: {match.group(0)} (verify it's in main.py)"
                ))
                count += 1

        return count

    def check_state_confusion(self, filepath: Path, content: str) -> int:
        """Check for imprecise state terminology."""
        count = 0

        # Vague status terms
        vague_patterns = [
            (r'print\(["\'].*?\b(done|complete|working|ready)["\']', "Vague state term"),
            (r'print\(["\']✓.*?["\']', "Emoji instead of precise state"),
        ]

        for pattern, reason in vague_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                line_no = content[:match.start()].count('\n') + 1

                # Check if it uses precise terms: written, wired, verified
                if not any(term in match.group(0) for term in ['written', 'wired', 'verified']):
                    self.issues.append((
                        str(filepath),
                        "distinguish-states",
                        line_no,
                        f"Imprecise state: {match.group(0)[:40]}... (use: written/wired/verified)"
                    ))
                    count += 1

        return count

    def validate_file(self, filepath: Path) -> int:
        """Run all validations on a single file."""
        if not filepath.is_file():
            return 0

        # Skip certain files
        if any(x in str(filepath) for x in ['.git', '__pycache__', 'node_modules', '.next']):
            return 0

        # Only check Python and JS files
        if filepath.suffix not in ['.py', '.js', '.ts', '.tsx']:
            return 0

        try:
            content = filepath.read_text(encoding='utf-8')
        except Exception:
            return 0

        count = 0
        count += self.check_fabricated_metrics(filepath, content)
        count += self.check_unverified_claims(filepath, content)
        count += self.check_silent_failures(filepath, content)
        count += self.check_orphaned_imports(filepath, content)
        count += self.check_state_confusion(filepath, content)

        return count

    def validate_all(self) -> int:
        """Validate all eligible files in the repository."""
        total_issues = 0

        print(f"\n{GREEN}DevForge Static Rules Validator{RESET}\n")

        for filepath in self.root.rglob('*'):
            if self.validate_file(filepath):
                total_issues += self.validate_file(filepath)

        return total_issues

    def report(self):
        """Print validation report."""
        if not self.issues:
            print(f"{GREEN}✅ All validations passed!{RESET}\n")
            return 0

        # Group by rule
        by_rule = {}
        for filepath, rule, line_no, msg in self.issues:
            if rule not in by_rule:
                by_rule[rule] = []
            by_rule[rule].append((filepath, line_no, msg))

        # Print grouped report
        for rule, issues in sorted(by_rule.items()):
            severity = "WARNING" if "unverified" in rule or "fake" in rule else "INFO"
            color = YELLOW if severity == "WARNING" else YELLOW

            print(f"{color}{severity}: {rule}{RESET} ({len(issues)} issues)\n")

            for filepath, line_no, msg in issues[:5]:  # Limit to first 5 per rule
                print(f"  {filepath}:{line_no}")
                print(f"    {msg}\n")

            if len(issues) > 5:
                print(f"  ... and {len(issues) - 5} more\n")

        return len(self.issues)


def main():
    import argparse

    parser = argparse.ArgumentParser(description="DevForge Static Rules Validator")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    parser.add_argument("--fix", action="store_true", help="Auto-fix issues (where supported)")

    args = parser.parse_args()

    validator = RuleValidator()
    validator.verbose = args.verbose

    validator.validate_all()
    exit_code = validator.report()

    print(f"\n{'='*60}")
    if exit_code > 0:
        print(f"{RED}Found {exit_code} issues{RESET}")
        print(f"Run 'python scripts/validate-rules.py --verbose' for details")
        return 1
    else:
        print(f"{GREEN}All static checks passed!{RESET}")
        return 0


if __name__ == "__main__":
    sys.exit(main())
