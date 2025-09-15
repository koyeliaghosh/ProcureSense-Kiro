#!/usr/bin/env python3
"""
Simple ProcureSense server for stable deployment.
"""

import sys
import os
from pathlib import Path

# Add src to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

def main():
    """Start the server with minimal configuration."""
    
    # Set environment variables
    os.environ.setdefault("LLM_PROVIDER", "ollama")
    os.environ.setdefault("OLLAMA_HOST", "localhost:11434")
    os.environ.setdefault("OLLAMA_MODEL", "llama3.1:8b")
    
    # Get port from environment (Render sets PORT)
    port = int(os.environ.get("PORT", 8001))
    
    print("🚀 Starting ProcureSense Server...")
    print(f"📍 Server will be available at: http://0.0.0.0:{port}")
    print(f"📚 API Documentation: http://0.0.0.0:{port}/docs")
    print(f"💼 Business Case: http://0.0.0.0:{port}/static/business-case.html")
    print(f"📖 Kiro Story: http://0.0.0.0:{port}/static/kiro-story.html")
    print()
    print("Press Ctrl+C to stop the server")
    print("=" * 50)
    
    try:
        import uvicorn
        from src.api.app import create_app
        
        # Create app
        app = create_app()
        
        # Run server with simple config
        uvicorn.run(
            app,
            host="0.0.0.0",  # Allow external connections
            port=port,  # Use environment PORT or default
            reload=False,
            log_level="warning"  # Reduce log noise
        )
        
    except KeyboardInterrupt:
        print("\n🛑 Server stopped")
    except Exception as e:
        print(f"❌ Error: {e}")
        print("💡 Make sure dependencies are installed: pip install fastapi uvicorn pydantic requests")

if __name__ == "__main__":
    main()