#!/usr/bin/env python3
"""
Cloud-optimized ProcureSense server for Render deployment.
"""

import os
import sys
from pathlib import Path

# Add src to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

# Set environment variables for cloud deployment
os.environ.setdefault("LLM_PROVIDER", "mock")  # Use mock for cloud demo
os.environ.setdefault("OLLAMA_HOST", "localhost:11434")
os.environ.setdefault("OLLAMA_MODEL", "llama3.1:8b")

# Import after setting environment
from src.api.app import create_app

# Create the FastAPI app
app = create_app()

# For local testing
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)