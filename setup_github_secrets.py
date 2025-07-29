#!/usr/bin/env python3
"""
GitHub Secrets Setup Helper
This script reads your ask.env file and provides the exact values to copy into GitHub Secrets.
"""

import os
from dotenv import load_dotenv

def main():
    print("🔧 GitHub Secrets Setup Helper")
    print("=" * 50)
    print()
    
    # Load environment variables
    if os.path.exists('ask.env'):
        load_dotenv('ask.env')
        print("✅ Found ask.env file")
    else:
        print("❌ ask.env file not found")
        print("Please make sure ask.env exists in the current directory")
        return
    
    print()
    print("📋 Copy these values to GitHub Secrets:")
    print("=" * 50)
    print()
    
    # Define all required secrets
    secrets = {
        # API Keys
        "GROQ_API_KEY": os.getenv("GROQ_API_KEY"),
        "TOGETHER_API_KEY": os.getenv("TOGETHER_API_KEY"),
        "REPLICATE_API_TOKEN": os.getenv("REPLICATE_API_TOKEN"),
        
        # Core Configuration
        "TEXT_PROVIDER": os.getenv("TEXT_PROVIDER", "groq"),
        "TEXT_MODEL": os.getenv("TEXT_MODEL", "llama3-8b-8192"),
        "NUM_SPREADS": os.getenv("NUM_SPREADS", "10"),
        "IMAGE_WIDTH": os.getenv("IMAGE_WIDTH", "1024"),
        "IMAGE_HEIGHT": os.getenv("IMAGE_HEIGHT", "1024"),
        "IMAGE_DPI": os.getenv("IMAGE_DPI", "300"),
        "CAPTION_POSITION": os.getenv("CAPTION_POSITION", "top-right"),
        "NUM_INFERENCE_STEPS": os.getenv("NUM_INFERENCE_STEPS", "30"),
        "GUIDANCE_SCALE": os.getenv("GUIDANCE_SCALE", "7.5"),
        "OUTPUT_PATH": os.getenv("OUTPUT_PATH", "output"),
        
        # Templates and Prompts
        "ZINE_TITLE_TEMPLATE": os.getenv("ZINE_TITLE_TEMPLATE", "ASK Volume {theme}"),
        "PROMPT_SYSTEM": os.getenv("PROMPT_SYSTEM", "You are a visionary architectural writer and provocateur. You create compelling, artistic image prompts that capture the essence of architectural concepts with vivid, poetic language."),
        "PROMPT_TEMPLATE": os.getenv("PROMPT_TEMPLATE", "Generate {n} architectural image prompts on theme: '{theme}'. Each prompt should be a single, evocative line that describes a visual scene with artistic flair. Focus on mood, atmosphere, and architectural poetry. Do not include explanations or numbered lists - just the prompts, one per line."),
        "CAPTION_SYSTEM": os.getenv("CAPTION_SYSTEM", "You are a masterful architectural poet and critic. You write profound, artistic captions that capture the deeper meaning and emotional resonance of architectural spaces."),
        "CAPTION_TEMPLATE": os.getenv("CAPTION_TEMPLATE", "Write exactly 6 lines, each containing exactly 6 words, that form a complete, meaningful caption for this architectural image: {prompt}. Each line should be a complete thought with poetic depth. The entire caption should tell a coherent story that reveals the architectural philosophy, emotional impact, and cultural significance of the space."),
        
        # Optional Configuration
        "FILTER_KEYWORDS": os.getenv("FILTER_KEYWORDS", "architecture,design,innovation"),
        "RSS_FEEDS": os.getenv("RSS_FEEDS", "https://feeds.bbci.co.uk/news/rss.xml,https://rss.cnn.com/rss/edition.rss"),
        "FALLBACK_THEME": os.getenv("FALLBACK_THEME", "Architecture & AI"),
        "CAPTION_FONT_SIZE": os.getenv("CAPTION_FONT_SIZE", "14"),
        "CAPTION_LINE_SPACING": os.getenv("CAPTION_LINE_SPACING", "18"),
        "GROQ_API_BASE": os.getenv("GROQ_API_BASE", "https://api.groq.com/openai/v1"),
        "TOGETHER_API_BASE": os.getenv("TOGETHER_API_BASE", "https://api.together.xyz/v1"),
        
        # Weekly Curator Configuration
        "WEEKLY_OUTPUT_PATH": os.getenv("WEEKLY_OUTPUT_PATH", "weekly_curated"),
        "WEEKLY_TITLE_TEMPLATE": os.getenv("WEEKLY_TITLE_TEMPLATE", "ASK Weekly Curated: {week_start} - {week_end}"),
        
        # Monthly Curator Configuration
        "MONTHLY_OUTPUT_PATH": os.getenv("MONTHLY_OUTPUT_PATH", "monthly_curated"),
        "MONTHLY_TITLE_TEMPLATE": os.getenv("MONTHLY_TITLE_TEMPLATE", "ASK Monthly Collection: {month_name} {year}"),
    }
    
    # Print secrets in a copy-paste friendly format
    for key, value in secrets.items():
        if value:
            print(f"🔑 {key}")
            print(f"   {value}")
            print()
        else:
            print(f"⚠️  {key} (not set in ask.env)")
            print()
    
    print("=" * 50)
    print()
    print("📝 Instructions:")
    print("1. Go to your GitHub repository")
    print("2. Settings → Secrets and variables → Actions")
    print("3. Click 'New repository secret'")
    print("4. Copy each key-value pair above")
    print("5. Save each secret")
    print()
    print("⚠️  Important:")
    print("- Don't include the '=' in the secret value")
    print("- Make sure to copy the exact value")
    print("- API keys should be the full key string")
    print()
    print("🚀 After setting secrets:")
    print("1. Push the .github/workflows/daily-zine-generation.yml file")
    print("2. Go to Actions tab")
    print("3. Test with 'Run workflow'")
    print()
    print("📚 For more details, see GITHUB_ACTIONS_SETUP.md")

if __name__ == "__main__":
    main() 