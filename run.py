#!/usr/bin/env python3
"""
Direct runner that ensures the virtual environment is used.
This script can be run from anywhere and will use the correct Python.
"""

import sys
import subprocess
from pathlib import Path

# Get the directory where this script is located
script_dir = Path(__file__).parent.absolute()

# Path to the virtual environment's Python
venv_python = script_dir / "venv" / "bin" / "python"

if not venv_python.exists():
    print(f"Error: Virtual environment Python not found at {venv_python}")
    print("Please create a virtual environment first: python3 -m venv venv")
    sys.exit(1)

# Run the verbose main module with the venv Python
cmd = [str(venv_python), "-m", "src.main_verbose"] + sys.argv[1:]
sys.exit(subprocess.call(cmd))