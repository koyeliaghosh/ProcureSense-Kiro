#!/usr/bin/env python3
"""
Complete deployment script for ProcureSense with ngrok.

This script handles:
1. Server startup verification
2. ngrok tunnel creation
3. URL sharing and monitoring
"""

import subprocess
import time
import sys
import os
import json
import requests
from pathlib import Path

def check_ngrok():
    """Check if ngrok is installed and configured."""
    try:
        result = subprocess.run(['ngrok', 'version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ ngrok found: {result.stdout.strip()}")
            return True
        else:
            print("❌ ngrok not found or not working")
            return False
    except FileNotFoundError:
        print("❌ ngrok not found in PATH")
        return False

def get_ngrok_tunnels():
    """Get active ngrok tunnels."""
    try:
        response = requests.get('http://localhost:4040/api/tunnels', timeout=5)
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None

def start_ngrok_tunnel(port=8000):
    """Start ngrok tunnel for the specified port."""
    print(f"🚀 Starting ngrok tunnel for port {port}...")
    
    try:
        # Start ngrok in background
        process = subprocess.Popen(
            ['ngrok', 'http', str(port)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Wait a moment for ngrok to start
        time.sleep(3)
        
        # Check if ngrok started successfully
        if process.poll() is None:
            print("✅ ngrok tunnel started successfully!")
            return process
        else:
            stdout, stderr = process.communicate()
            print(f"❌ ngrok failed to start: {stderr.decode()}")
            return None
            
    except Exception as e:
        print(f"❌ Failed to start ngrok: {e}")
        return None

def get_public_urls():
    """Get the public URLs from ngrok."""
    max_attempts = 10
    for attempt in range(max_attempts):
        tunnels = get_ngrok_tunnels()
        if tunnels and 'tunnels' in tunnels:
            urls = {}
            for tunnel in tunnels['tunnels']:
                if tunnel['proto'] == 'https':
                    urls['https'] = tunnel['public_url']
                elif tunnel['proto'] == 'http':
                    urls['http'] = tunnel['public_url']
            
            if urls:
                return urls
        
        time.sleep(1)
    
    return None

def display_deployment_info(urls):
    """Display deployment information and URLs."""
    print("\n" + "🎉 DEPLOYMENT SUCCESSFUL!" + "\n")
    print("=" * 60)
    print("🌐 YOUR PROCURESENSE SYSTEM IS NOW LIVE GLOBALLY!")
    print("=" * 60)
    
    https_url = urls.get('https', '')
    
    print(f"\n📱 SHARE THESE URLS WITH ANYONE:")
    print(f"   🏠 Main App:      {https_url}/")
    print(f"   📚 API Docs:      {https_url}/docs")
    print(f"   💼 Business Case: {https_url}/static/business-case.html")
    print(f"   📖 Kiro Story:    {https_url}/static/kiro-story.html")
    
    print(f"\n🔧 MANAGEMENT URLS:")
    print(f"   📊 ngrok Status:  http://localhost:4040")
    print(f"   🏥 Health Check:  {https_url}/health")
    
    print(f"\n💡 TIPS:")
    print(f"   • Use the HTTPS URL for sharing (more secure)")
    print(f"   • Keep this terminal open to maintain the tunnel")
    print(f"   • Press Ctrl+C to stop the deployment")
    print(f"   • The URL will change if you restart ngrok")
    
    print("\n" + "=" * 60)
    print("🚀 Ready to demo your AI procurement system!")
    print("=" * 60)

def monitor_deployment():
    """Monitor the deployment and handle shutdown."""
    try:
        print("\n⏳ Monitoring deployment... (Press Ctrl+C to stop)")
        while True:
            time.sleep(30)  # Check every 30 seconds
            
            # Check if server is still running
            try:
                response = requests.get('http://localhost:8000/health', timeout=5)
                if response.status_code != 200:
                    print("⚠️ Server health check failed")
            except:
                print("❌ Server appears to be down!")
                break
            
            # Check if ngrok is still running
            tunnels = get_ngrok_tunnels()
            if not tunnels:
                print("❌ ngrok tunnel appears to be down!")
                break
                
    except KeyboardInterrupt:
        print("\n🛑 Stopping deployment...")
        return

def main():
    """Main deployment function."""
    print("🚀 ProcureSense Global Deployment with ngrok")
    print("=" * 50)
    
    # Check prerequisites
    if not check_ngrok():
        print("\n💡 To install ngrok:")
        print("   1. Go to https://ngrok.com/")
        print("   2. Sign up for free account")
        print("   3. Download ngrok for Windows")
        print("   4. Extract to a folder (e.g., C:\\ngrok\\)")
        print("   5. Add to PATH or run from that folder")
        print("   6. Get auth token from dashboard")
        print("   7. Run: ngrok config add-authtoken YOUR_TOKEN")
        sys.exit(1)
    
    # Check if server is running
    print("\n🔍 Checking if ProcureSense server is running...")
    try:
        response = requests.get('http://localhost:8000/health', timeout=5)
        if response.status_code == 200:
            print("✅ ProcureSense server is running!")
        else:
            print("❌ Server is not responding correctly")
            print("💡 Start the server first: python run_server.py")
            sys.exit(1)
    except requests.exceptions.RequestException:
        print("❌ ProcureSense server is not running")
        print("💡 Start the server first: python run_server.py")
        print("   In a separate terminal, run: python run_server.py")
        sys.exit(1)
    
    # Start ngrok tunnel
    ngrok_process = start_ngrok_tunnel(8000)
    if not ngrok_process:
        sys.exit(1)
    
    # Get public URLs
    print("⏳ Getting public URLs...")
    urls = get_public_urls()
    if not urls:
        print("❌ Failed to get ngrok URLs")
        ngrok_process.terminate()
        sys.exit(1)
    
    # Display deployment info
    display_deployment_info(urls)
    
    # Monitor deployment
    try:
        monitor_deployment()
    finally:
        print("🧹 Cleaning up...")
        if ngrok_process:
            ngrok_process.terminate()
        print("✅ Deployment stopped")

if __name__ == "__main__":
    main()