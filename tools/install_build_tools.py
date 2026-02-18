import subprocess
import sys

def main():
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "build"])

if __name__ == "__main__":
    main()
