
import subprocess
import sys
import os
from pathlib import Path
import shutil

def ensure_venv(venv, python):
    if not venv.exists():
        print("Creating venv...")
        subprocess.check_call([sys.executable, "-m", "venv", str(venv)])
    else:
        print("venv already exists.")
    return python

def build_latest_wheel(root):
    dist = root / "dist"
    venv = root / "venv"
    python = venv / "Scripts" / "python.exe"
    # Ensure build tools are present
    subprocess.check_call([str(python), "-m", "pip", "install", "--upgrade", "setuptools", "wheel"])
    if dist.exists():
        print("Removing old wheels...")
        for f in dist.glob("*.whl"):
            f.unlink()
    print("Building latest wheel...")
    subprocess.check_call([str(python), "setup.py", "bdist_wheel"], cwd=root)
    wheels = sorted(dist.glob("choppa-*.whl"), key=os.path.getmtime, reverse=True)
    if not wheels:
        print("No wheel built!")
        sys.exit(1)
    return wheels[0]

def install_packages(python, wheel, root):
    subprocess.check_call([str(python), "-m", "pip", "install", "--upgrade", "pip"])
    subprocess.check_call([str(python), "-m", "pip", "install", wheel])
    reqs = root / "requirements.txt"
    if reqs.exists():
        subprocess.check_call([str(python), "-m", "pip", "install", "-r", str(reqs)])
    else:
        subprocess.check_call([str(python), "-m", "pip", "install", "regex", "xmlschema"])

def run_tests(python, root):
    print("Running test_choppa.py...")
    subprocess.check_call([str(python), str(root / "choppa" / "test_choppa.py")])

def run_diff_stats(python, root):
    print("\nDiff stats:")
    subprocess.check_call([str(python), str(root / "diff_stats.py")])

def main():
    root = Path(__file__).parent.resolve()
    venv = root / "venv"
    python = venv / "Scripts" / "python.exe"
    ensure_venv(venv, python)
    wheel = build_latest_wheel(root)
    print(f"Using wheel: {wheel}")
    install_packages(python, wheel, root)
    run_tests(python, root)
    run_diff_stats(python, root)

if __name__ == "__main__":
    main()
