#!/usr/bin/env python3
"""
Deploy ProcureSense to GitHub Pages - FREE hosting for judges
"""

import os
import shutil

def setup_github_pages():
    """Setup GitHub Pages deployment"""
    
    print("🚀 Setting up GitHub Pages deployment...")
    
    # Create docs folder for GitHub Pages
    if not os.path.exists('docs'):
        os.makedirs('docs')
    
    # Copy interactive demo as index.html
    shutil.copy('interactive_demo.html', 'docs/index.html')
    
    # Copy other demo files
    demo_files = [
        'static_demo.html',
        'demo.html'
    ]
    
    for file in demo_files:
        if os.path.exists(file):
            shutil.copy(file, f'docs/{file}')
    
    # Copy static assets if they exist
    if os.path.exists('src/static'):
        if not os.path.exists('docs/static'):
            os.makedirs('docs/static')
        for file in os.listdir('src/static'):
            shutil.copy(f'src/static/{file}', f'docs/static/{file}')
    
    print("✅ Files copied to docs/ folder")
    print("\n📋 Next steps:")
    print("1. git add docs/")
    print("2. git commit -m 'Add GitHub Pages deployment'")
    print("3. git push origin main")
    print("4. Go to GitHub → Settings → Pages → Source: Deploy from branch → main → /docs")
    print("\n🌐 Your demo will be available at:")
    print("https://koyeliaghosh.github.io/ProcureSense-Kiro/")

if __name__ == "__main__":
    setup_github_pages()