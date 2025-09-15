# 🌐 Global Deployment Guide for ProcureSense

## Quick Deployment Options

### 1. Heroku (Recommended for Demo)
```bash
# Install Heroku CLI: https://devcenter.heroku.com/articles/heroku-cli

# Login to Heroku
heroku login

# Create app
heroku create your-procuresense-app

# Set environment variables (optional - system works without LLM)
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
# Visit: https://railway.app
# Click "Deploy from GitHub"
# Connect your GitHub repository
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
```

## One-Click Deploy Buttons

Add these to your README for instant deployment:

[![Deploy to Heroku](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy)

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/new/template)

## Environment Variables for Production

Set these in your deployment platform (all optional):

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

## Global Access

Once deployed, your ProcureSense system will be accessible worldwide:
- ✅ Anyone can access your URL
- ✅ No installation required for users
- ✅ Works on all devices (mobile, tablet, desktop)
- ✅ Professional HTTPS domain
- ✅ Automatic scaling and uptime

Your ProcureSense system will be globally accessible and production-ready! 🚀