#!/usr/bin/env python3
"""
Disha Development Server Runner

Run the backend locally with a single, clean command:
    python dev.py
    # or: ./dev.py

Handles:
  - Automatic PYTHONPATH resolution
  - Hot reload restricted to code directories (api, agents, tools, storage)
  - Exclusion of data/ cache files and frontend/ to prevent restart loops
"""

import sys
from pathlib import Path

# Ensure repository root is on sys.path
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import uvicorn

def main():
    uvicorn.run(
        "api.server:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        reload_dirs=["api", "agents", "tools", "storage"],
        reload_excludes=["data/*", "frontend/*", "*.json", "logs/*"],
    )

if __name__ == "__main__":
    main()
