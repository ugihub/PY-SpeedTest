"""
PyInstaller runtime hook for speedtest-cli compatibility.
speedtest-cli uses '__builtin__' (Python 2 name) which doesn't exist in Python 3.
This hook creates an alias so it works correctly when bundled.
"""

import builtins
import sys

# Create alias: __builtin__ -> builtins (Python 2 -> Python 3 compatibility)
sys.modules["__builtin__"] = builtins
