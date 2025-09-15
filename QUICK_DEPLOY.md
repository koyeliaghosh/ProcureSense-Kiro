# 🚀 Quick ngrok Deployment Guide

## **2-Step Global Deployment**

### **Step 1: Start ProcureSense Server**
Open **Terminal 1** and run:
```cmd
python simple_server.py
```

Wait for:
```
🚀 Starting ProcureSense Server...
📍 Server will be available at: http://localhost:8000
```

**Keep this terminal open!**

### **Step 2: Start ngrok Tunnel**
Open **Terminal 2** and run:
```cmd
ngrok http 8000
```

You'll see:
```
Session Status                online
Forwarding                    https://abc123def.ngrok-free.app -> http://localhost:8000
```

## 🌐 **Your Global URLs:**
- **Main App**: `https://abc123def.ngrok-free.app/`
- **API Docs**: `https://abc123def.ngrok-free.app/docs`
- **Business Case**: `https://abc123def.ngrok-free.app/static/business-case.html`
- **Kiro Story**: `https://abc123def.ngrok-free.app/static/kiro-story.html`

## 📱 **Share Instantly!**
Copy the **https** URL and share with anyone worldwide!

## 🔧 **Troubleshooting**

### If ngrok is not installed:
1. Go to https://ngrok.com/
2. Sign up (free)
3. Download for Windows
4. Extract to `C:\ngrok\`
5. Get auth token from dashboard
6. Run: `ngrok config add-authtoken YOUR_TOKEN`

### If server won't start:
```cmd
python test_startup.py
```

### If port 8000 is busy:
Change port in `simple_server.py` to 8001, then use `ngrok http 8001`

## ⚡ **Total Time: ~1 minute**
Your AI procurement system will be globally accessible in under 60 seconds!