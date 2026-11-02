"""
================================================================================
Pharmacy Management System - Root Launcher
================================================================================
Convenience launcher to run the desktop application from the repository root.
Usage:
    py run.py
================================================================================
"""

import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from pharmacy_management.main import main

if __name__ == "__main__":
    main()

