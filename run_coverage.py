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

    # Run pytest with coverage
    run("run", "--rcfile=coverage.ini", "-m", "pytest", "-q")

    # Combine thread coverage data
    run("combine")

    # Generate HTML report
    run("html")

    print("\nCoverage report generated at: htmlcov/index.html")

if __name__ == "__main__":
    main()
