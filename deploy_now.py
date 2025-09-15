#!/usr/bin/env python3
"""
One-click deployment script for ProcureSense with ngrok.
Handles port conflicts automatically.
"""

import subprocess
import time
import sys
import os
import requests
from pathlib import Path

def find_free_port(start_port=8001):
    """Find a free port starting from start_port."""
    import socket
    
    for port in range(start_port, start_port + 10):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('localhost', port))
                return port
        except OSError:
            continue
    
    return None

def kill_port_processes(port):
    """Kill any processes using the specified port."""
    try:
        # Find processes using the port
        result = subprocess.run(
            ['netstat', '-ano'], 
            capture_output=True, 
            text=True
        )
        
        lines = result.stdout.split('\n')
        pids_to_kill = []
        
        for line in lines:
            if f':{port}' in line and 'LISTENING' in line:
                parts = line.split()
                if len(parts) > 4:
                    pid = parts[-1]
                    if pid.isdigit():
                        pids_to_kill.append(pid)
        
        # Kill the processes
        for pid in pids_to_kill:
            try:
                subprocess.run(['taskkill', '/PID', pid, '/F'], 
                             capture_output=True)
                print(f"✅ Killed process {pid} using port {port}")
            except:
                pass
                
    except Exception as e:
        print(f"⚠️ Could not kill port processes: {e}")

def start_server(port):
    """Start the ProcureSense server on specified port."""
    
    # Add src to Python path
    src_path = Path(__file__).parent / "src"
    sys.path.insert(0, str(src_path))
    
    # Set environment variables
    os.environ.setdefault("LLM_PROVIDER", "ollama")
    os.environ.setdefault("OLLAMA_HOST", "localhost:11434")
    os.environ.setdefault("OLLAMA_MODEL", "llama3.1:8b")
    
    print(f"🚀 Starting ProcureSense Server on port {port}...")
    
    try:
        import uvicorn
        from src.api.app import create_app
        
        # Create app
        app = create_app()
        
        # Start server in background
        config = uvicorn.Config(
            app,
            host="0.0.0.0",
            port=port,
            reload=False,
            log_level="error"  # Minimal logging
        )
        
        server = uvicorn.Server(config)
        
        # Run server in a separate process
        import multiprocessing
        
        def run_server():
            server.run()
        
        process = multiprocessing.Process(target=run_server)
        process.start()
        
        # Wait for server to start
        print("⏳ Waiting for server to start...")
        for i in range(10):
            try:
                response = requests.get(f'http://localhost:{port}/health', timeout=2)
                if response.status_code == 200:
                    print(f"✅ Server started successfully on port {port}!")
                    return process, port
            except:
                pass
            time.sleep(1)
        
        print("❌ Server failed to start")
        process.terminate()
        return None, None
        
    except Exception as e:
        print(f"❌ Server startup failed: {e}")
        return None, None

def start_ngrok(port):
    """Start ngrok tunnel."""
    print(f"🌐 Starting ngrok tunnel for port {port}...")
    
    try:
        # Start ngrok
        process = subprocess.Popen(
            ['ngrok', 'http', str(port)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Wait for ngrok to start
        time.sleep(3)
        
        if process.poll() is None:
            print("✅ ngrok tunnel started!")
            return process
        else:
            print("❌ ngrok failed to start")
            return None
            
    except FileNotFoundError:
        print("❌ ngrok not found!")
        print("💡 Install ngrok from https://ngrok.com/")
        return None

def get_ngrok_url():
    """Get the public ngrok URL."""
    try:
        response = requests.get('http://localhost:4040/api/tunnels', timeout=5)
        if response.status_code == 200:
            tunnels = response.json()
            for tunnel in tunnels.get('tunnels', []):
                if tunnel['proto'] == 'https':
                    return tunnel['public_url']
        return None
    except:
        return None

def main():
    """Main deployment function."""
    print("🚀 ProcureSense One-Click Deployment")
    print("=" * 50)
    
    # Find free port
    port = find_free_port(8001)
    if not port:
        print("❌ No free ports available")
        return
    
    print(f"📍 Using port {port}")
    
    # Kill any existing processes on this port
    kill_port_processes(port)
    
    # Start server
    server_process, actual_port = start_server(port)
    if not server_process:
        return
    
    # Start ngrok
    ngrok_process = start_ngrok(actual_port)
    if not ngrok_process:
        server_process.terminate()
        return
    
    # Get public URL
    print("⏳ Getting public URL...")
    time.sleep(2)
    
    public_url = get_ngrok_url()
    if public_url:
        print("\n" + "🎉 DEPLOYMENT SUCCESSFUL!" + "\n")
        print("=" * 60)
        print("🌐 YOUR PROCURESENSE SYSTEM IS LIVE!")
        print("=" * 60)
        print(f"\n📱 SHARE THIS URL:")
        print(f"   🏠 Main App:      {public_url}/")
        print(f"   📚 API Docs:      {public_url}/docs")
        print(f"   💼 Business Case: {public_url}/static/business-case.html")
        print(f"   📖 Kiro Story:    {public_url}/static/kiro-story.html")
        print("\n💡 Keep this window open to maintain the deployment")
        print("   Press Ctrl+C to stop")
        print("=" * 60)
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Stopping deployment...")
    else:
        print("❌ Failed to get public URL")
    
    # Cleanup
    if server_process:
        server_process.terminate()
    if ngrok_process:
        ngrok_process.terminate()

if __name__ == "__main__":
    main()