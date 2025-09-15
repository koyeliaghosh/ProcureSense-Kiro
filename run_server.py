#!/usr/bin/env python3
"""
ProcureSense Server Startup Script

Robust script to start the ProcureSense FastAPI server with proper error handling.
"""

import uvicorn
import os
import sys
import traceback
import signal
from pathlib import Path

# Add src to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

# Global server reference for graceful shutdown
server = None

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    print(f"\n🛑 Received signal {signum}, shutting down gracefully...")
    if server:
        server.should_exit = True
    sys.exit(0)

def check_dependencies():
    """Check if all required dependencies are available."""
    required_modules = [
        'fastapi', 'uvicorn', 'pydantic', 'requests'
    ]
    
    missing = []
    for module in required_modules:
        try:
            __import__(module)
        except ImportError:
            missing.append(module)
    
    if missing:
        print(f"❌ Missing dependencies: {', '.join(missing)}")
        print("💡 Install with: pip install fastapi uvicorn pydantic requests")
        return False
    
    return True

def check_environment():
    """Check environment configuration."""
    print("🔍 Checking environment...")
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ required")
        return False
    
    print(f"✅ Python {sys.version.split()[0]}")
    
    # Check if src directory exists
    if not src_path.exists():
        print(f"❌ Source directory not found: {src_path}")
        return False
    
    print(f"✅ Source directory: {src_path}")
    
    return True

def main():
    """Start the ProcureSense server with robust error handling."""
    
    # Set up signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    print("🚀 ProcureSense Server Startup")
    print("=" * 50)
    
    # Environment checks
    if not check_environment():
        sys.exit(1)
    
    if not check_dependencies():
        sys.exit(1)
    
    # Set default environment variables
    os.environ.setdefault("LLM_PROVIDER", "ollama")
    os.environ.setdefault("OLLAMA_HOST", "localhost:11434")
    os.environ.setdefault("OLLAMA_MODEL", "llama3.1:8b")
    os.environ.setdefault("SERVER_HOST", "0.0.0.0")  # Changed to 0.0.0.0 for ngrok compatibility
    os.environ.setdefault("SERVER_PORT", "8000")
    
    host = os.environ.get("SERVER_HOST")
    port = int(os.environ.get("SERVER_PORT"))
    
    print(f"📍 Server Host: {host}")
    print(f"🔌 Server Port: {port}")
    print(f"🤖 LLM Provider: {os.environ.get('LLM_PROVIDER')}")
    print(f"🔗 LLM Host: {os.environ.get('OLLAMA_HOST')}")
    print()
    print("🌐 Access URLs:")
    print(f"   Main App: http://{host}:{port}/")
    print(f"   API Docs: http://{host}:{port}/docs")
    print(f"   Business Case: http://{host}:{port}/static/business-case.html")
    print(f"   Kiro Story: http://{host}:{port}/static/kiro-story.html")
    print()
    
    try:
        print("📦 Loading application...")
        
        # Import and create the app
        from src.api.app import create_app
        app = create_app()
        
        print("✅ Application loaded successfully!")
        print("🚀 Starting server...")
        print("   Press Ctrl+C to stop")
        print("=" * 50)
        
        # Create server config
        config = uvicorn.Config(
            app,
            host=host,
            port=port,
            reload=False,
            log_level="info",
            access_log=True,
            server_header=False,
            date_header=False
        )
        
        # Create and run server
        global server
        server = uvicorn.Server(config)
        server.run()
        
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        print(f"📍 Error details: {traceback.format_exc()}")
        print("💡 Make sure all dependencies are installed")
        print("   Try: pip install -r requirements.txt")
        sys.exit(1)
        
    except OSError as e:
        if "Address already in use" in str(e):
            print(f"❌ Port {port} is already in use!")
            print("💡 Try a different port or stop the existing server")
            print(f"   Set SERVER_PORT environment variable: set SERVER_PORT=8001")
        else:
            print(f"❌ Network Error: {e}")
        sys.exit(1)
        
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
        sys.exit(0)
        
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        print(f"📍 Full traceback: {traceback.format_exc()}")
        sys.exit(1)

if __name__ == "__main__":
    main()