#!/usr/bin/env python3
"""
Global Deployment Script for ProcureSense
Prepares the system for cloud deployment
"""

import os
import sys
from pathlib import Path

def create_production_files():
    """Create production deployment files"""
    
    # Create Procfile for Heroku
    procfile_content = """web: python run_server.py
worker: python -m uvicorn src.api.app:create_app --factory --host 0.0.0.0 --port $PORT"""
    
    with open("Procfile", "w") as f:
        f.write(procfile_content)
    
    # Create requirements.txt for production
    requirements_content = """fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
pydantic-settings==2.1.0
python-dotenv==1.0.0
httpx==0.25.2
pytest==7.4.3
pytest-asyncio==0.21.1
requests==2.31.0"""
    
    with open("requirements.txt", "w") as f:
        f.write(requirements_content)
    
    # Create runtime.txt for Python version
    with open("runtime.txt", "w") as f:
        f.write("python-3.11.6")
    
    # Create app.json for easy deployment
    app_json_content = """{
  "name": "ProcureSense",
  "description": "AI-Powered Procurement Co-Pilot with Enterprise Policy Compliance",
  "repository": "https://github.com/your-username/procuresense",
  "logo": "https://your-domain.com/logo.png",
  "keywords": ["ai", "procurement", "fastapi", "python"],
  "stack": "heroku-22",
  "buildpacks": [
    {
      "url": "heroku/python"
    }
  ],
  "env": {
    "LLM_PROVIDER": {
      "description": "LLM provider (ollama, openai, anthropic)",
      "value": "openai"
    },
    "OPENAI_API_KEY": {
      "description": "OpenAI API key for LLM integration",
      "required": false
    },
    "SERVER_HOST": {
      "description": "Server host",
      "value": "0.0.0.0"
    },
    "SERVER_PORT": {
      "description": "Server port",
      "value": "8000"
    }
  },
  "formation": {
    "web": {
      "quantity": 1,
      "size": "basic"
    }
  },
  "addons": [],
  "scripts": {
    "postdeploy": "echo 'ProcureSense deployed successfully!'"
  }
}"""
    
    with open("app.json", "w") as f:
        f.write(app_json_content)
    
    print("✅ Production deployment files created!")
    print("📁 Files created:")
    print("  - Procfile (Heroku process definition)")
    print("  - requirements.txt (Python dependencies)")
    print("  - runtime.txt (Python version)")
    print("  - app.json (Heroku app configuration)")

def update_server_for_production():
    """Update server configuration for production deployment"""
    
    # Read current server file
    with open("run_server.py", "r") as f:
        content = f.read()
    
    # Add production configuration
    production_config = '''
    # Production configuration
    port = int(os.environ.get("PORT", os.environ.get("SERVER_PORT", "8000")))
    host = os.environ.get("SERVER_HOST", "0.0.0.0")
    
    print(f"🌐 Production mode: Running on {host}:{port}")
    '''
    
    # Update the uvicorn.run call
    updated_content = content.replace(
        'host=os.environ.get("SERVER_HOST", "localhost"),\n            port=int(os.environ.get("SERVER_PORT", "8000")),',
        'host=host,\n            port=port,'
    )
    
    # Add the production config before uvicorn.run
    updated_content = updated_content.replace(
        'try:\n        # Import and create the app',
        f'try:{production_config}\n        # Import and create the app'
    )
    
    with open("run_server.py", "w") as f:
        f.write(updated_content)
    
    print("✅ Server updated for production deployment!")

def create_deployment_guide():
    """Create deployment guide"""
    
    guide_content = """# 🌐 Global Deployment Guide for ProcureSense

## Quick Deployment Options

### 1. Heroku (Recommended for Demo)
```bash
# Install Heroku CLI: https://devcenter.heroku.com/articles/heroku-cli

# Login to Heroku
heroku login

# Create app
heroku create your-procuresense-app

# Set environment variables
heroku config:set LLM_PROVIDER=openai
heroku config:set OPENAI_API_KEY=your-api-key-here

# Deploy
git add .
git commit -m "Deploy ProcureSense"
git push heroku main

# Open your app
heroku open
```

Your app will be available at: `https://your-procuresense-app.herokuapp.com`

### 2. Railway (Modern & Fast)
```bash
# Connect GitHub repo to Railway
# Visit: https://railway.app
# Click "Deploy from GitHub"
# Select your repository
# Railway auto-deploys!
```

### 3. DigitalOcean App Platform
```bash
# Visit: https://cloud.digitalocean.com/apps
# Click "Create App"
# Connect your GitHub repository
# DigitalOcean handles the rest!
```

### 4. Vercel (Serverless)
```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
vercel

# Follow the prompts
```

## Environment Variables for Production

Set these in your deployment platform:

```bash
LLM_PROVIDER=openai
OPENAI_API_KEY=your-openai-api-key
SERVER_HOST=0.0.0.0
SERVER_PORT=8000
```

## Custom Domain

After deployment, you can add a custom domain:
- `https://procuresense.yourdomain.com`
- `https://demo.procuresense.com`

## Security for Production

1. **API Keys**: Use environment variables, never commit keys
2. **HTTPS**: All platforms provide automatic HTTPS
3. **CORS**: Configure allowed origins in production
4. **Rate Limiting**: Enable in production settings

## Monitoring

Most platforms provide:
- ✅ Automatic scaling
- ✅ Health monitoring  
- ✅ Log aggregation
- ✅ Performance metrics

Your ProcureSense system will be globally accessible and production-ready! 🚀
"""
    
    with open("GLOBAL_DEPLOYMENT.md", "w") as f:
        f.write(guide_content)
    
    print("✅ Global deployment guide created!")

def main():
    """Main deployment preparation"""
    print("🌐 Preparing ProcureSense for Global Deployment")
    print("=" * 50)
    
    create_production_files()
    print()
    update_server_for_production()
    print()
    create_deployment_guide()
    
    print("\n🎉 Ready for Global Deployment!")
    print("\n📋 Next Steps:")
    print("1. Choose a deployment platform (Heroku, Railway, DigitalOcean)")
    print("2. Set up environment variables (API keys)")
    print("3. Deploy using the instructions in GLOBAL_DEPLOYMENT.md")
    print("4. Share your global URL with anyone!")
    
    print(f"\n🔗 Your app will be accessible worldwide at:")
    print(f"   https://your-app-name.herokuapp.com")
    print(f"   https://your-app-name.railway.app")
    print(f"   https://your-app-name.ondigitalocean.app")

if __name__ == "__main__":
    main()