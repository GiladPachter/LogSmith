import subprocess
import sys
from pathlib import Path

def main():
    project_root = Path(__file__).resolve().parents[1]
    subprocess.check_call([sys.executable, "-m", "build", str(project_root)])

if __name__ == "__main__":
    main()
