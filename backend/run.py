#!/usr/bin/env python3
"""Run the application."""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.main import app

if __name__ == "__main__":
    import uvicorn

    print("Starting FrozenFoodBot Backend...")
    print("Bot will start automatically")
    print("FastAPI will be available at http://localhost:8000")
    print("API docs at http://localhost:8000/docs")
    print("\nPress Ctrl+C to stop\n")

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )