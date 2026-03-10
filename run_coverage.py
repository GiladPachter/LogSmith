"""
This runner:
- erases old coverage
- runs pytest with thread‑aware coverage
- merges coverage from worker threads
- generates a clean HTML report


After execution:
    open htmlcov/index.html

"""

import os
import sys
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent

def run(*args):
    """Run a coverage command using the active Python interpreter."""
    return subprocess.run([sys.executable, "-m", "coverage", *args], check=False)

def main():
    os.chdir(ROOT)

    # Clean old coverage data
    run("erase")

    # Run pytest (pytest.ini already enables coverage)
    subprocess.run([sys.executable, "-m", "pytest"], check=False)

    # Combine (may say "No data to combine" — harmless)
    run("combine")

    # Generate HTML report
    run("html")

    # Optional: generate XML for CI or badges
    run("xml")

    # Optional: print summary to console
    run("report")

    print("\nCoverage report generated at: coverage_html/index.html")

if __name__ == "__main__":
    main()
