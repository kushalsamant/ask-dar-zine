#!/usr/bin/env python3
"""
Daily LinkedIn Poster
Posts 2 images daily to LinkedIn from the LinkedIn pool.
"""

import os
import sys
import subprocess
import logging
import time
from datetime import datetime
from pathlib import Path
import json
import random

# === 🔧 Setup real-time logging ===
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)
log_filename = os.path.join(LOG_DIR, f"linkedin_poster_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(log_filename, mode='w', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
log = logging.getLogger()

# === 🛠️ Auto-install missing dependencies ===
REQUIRED_LIBS = ['python-dotenv']

def install_missing_libs():
    missing_libs = []
    for lib in REQUIRED_LIBS:
        try:
            if lib == 'python-dotenv':
                __import__('dotenv')
            else:
                __import__(lib)
        except ImportError:
            missing_libs.append(lib)
    
    if missing_libs:
        log.info(f"Installing missing dependencies: {', '.join(missing_libs)}")
        for lib in missing_libs:
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", lib])
                log.info(f"Installed: {lib}")
            except subprocess.CalledProcessError as e:
                log.error(f"Failed to install {lib}: {e}")
                sys.exit(1)
    else:
        log.info("All dependencies are already installed")

install_missing_libs()

# === Now import everything ===
from dotenv import load_dotenv

# === 📥 Load environment variables ===
load_dotenv('ask.env')

def get_env(var, default=None, required=False):
    value = os.getenv(var, default)
    if required and not value:
        log.error(f"Required environment variable '{var}' is missing. Exiting.")
        sys.exit(1)
    return value

def load_allocation_state():
    """Load the current allocation state from file"""
    state_file = "image_allocation_state.json"
    if os.path.exists(state_file):
        try:
            with open(state_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            log.warning(f"Could not load allocation state: {e}")
    
    return {}

def get_linkedin_images(state, count=2):
    """Get images from LinkedIn pool"""
    linkedin_pool = state.get('linkedin_pool', [])
    
    if len(linkedin_pool) < count:
        log.warning(f"Only {len(linkedin_pool)} images available in LinkedIn pool, requested {count}")
        count = len(linkedin_pool)
    
    if count == 0:
        log.warning("No images available in LinkedIn pool")
        return []
    
    # Get the requested number of images (FIFO - oldest first)
    selected_images = linkedin_pool[:count]
    
    # Remove selected images from pool
    state['linkedin_pool'] = linkedin_pool[count:]
    
    log.info(f"Selected {len(selected_images)} images for LinkedIn posting")
    return selected_images

def load_caption_for_image(image_path):
    """Load caption for a specific image"""
    try:
        # Extract style and image number from path
        # Expected format: images/style/image_01_YYYYMMDD_HHMMSS.jpg
        path_parts = Path(image_path).parts
        if len(path_parts) >= 3:
            style = path_parts[-2]  # style directory
            filename = path_parts[-1]  # image filename
            
            # Extract image number from filename
            # Expected format: style_image_01_YYYYMMDD_HHMMSS.jpg
            filename_parts = filename.split('_')
            if len(filename_parts) >= 3:
                image_num = filename_parts[2]  # 01, 02, etc.
                
                # Load caption from captions file
                captions_file = f"captions/{style}_captions.txt"
                if os.path.exists(captions_file):
                    with open(captions_file, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                    
                    # Find the caption for this image number
                    for line in lines:
                        if line.startswith(f"Image {image_num}:"):
                            caption = line.replace(f"Image {image_num}:", "").strip()
                            return caption
                
                # Fallback: return a generic caption
                return f"Amazing {style} style artwork - exploring the intersection of technology and creativity"
        
        return "Exploring the future through art and technology"
    except Exception as e:
        log.warning(f"Could not load caption for {image_path}: {e}")
        return "Discovering new perspectives through AI-generated art"

def create_linkedin_caption(image_info, base_caption):
    """Create LinkedIn-optimized caption (professional tone)"""
    # LinkedIn hashtags for professional tech content
    hashtags = [
        "#ArtificialIntelligence", "#Technology", "#Innovation", "#DigitalTransformation",
        "#AI", "#MachineLearning", "#TechInnovation", "#FutureOfWork", "#DigitalArt",
        "#CreativeTechnology", "#TechLeadership", "#InnovationManagement"
    ]
    
    # Select random hashtags
    selected_hashtags = random.sample(hashtags, min(10, len(hashtags)))
    
    # Create LinkedIn caption (professional tone)
    caption = f"{base_caption}\n\n"
    caption += "🎨 Exploring the intersection of artificial intelligence and creative expression\n"
    caption += "🔬 Daily insights from our research-driven approach to AI-generated art\n"
    caption += "💼 How AI is reshaping creative industries and professional workflows\n"
    caption += "📈 Join the conversation on the future of technology and creativity\n\n"
    caption += " ".join(selected_hashtags)
    
    return caption

def simulate_linkedin_posting(images):
    """Simulate posting to LinkedIn (replace with actual API integration)"""
    log.info("💼 Simulating LinkedIn posting...")
    
    posts = []
    for i, image_info in enumerate(images, 1):
        image_path = image_info['path']
        style = image_info['style']
        
        # Load caption
        base_caption = load_caption_for_image(image_path)
        linkedin_caption = create_linkedin_caption(image_info, base_caption)
        
        # Simulate posting
        post_info = {
            'platform': 'LinkedIn',
            'image_path': image_path,
            'style': style,
            'caption': linkedin_caption,
            'posted_at': datetime.now().isoformat(),
            'post_number': i
        }
        
        posts.append(post_info)
        
        log.info(f"💼 LinkedIn Post {i}: {style} style image")
        log.info(f"   Caption: {base_caption[:50]}...")
        
        # Simulate posting delay
        time.sleep(1)
    
    return posts

def save_posting_summary(posts, platform):
    """Save posting summary to file"""
    summary_dir = "patreon_posts"  # Reuse existing directory
    os.makedirs(summary_dir, exist_ok=True)
    
    today = datetime.now().strftime('%Y%m%d')
    summary_file = os.path.join(summary_dir, f"{platform.lower()}_posts_{today}.json")
    
    summary = {
        'platform': platform,
        'date': today,
        'total_posts': len(posts),
        'posts': posts,
        'generated_at': datetime.now().isoformat()
    }
    
    try:
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        log.info(f"📄 {platform} posting summary saved to {summary_file}")
    except Exception as e:
        log.error(f"Failed to save {platform} posting summary: {e}")

def main():
    log.info("=== Daily LinkedIn Poster Started ===")
    
    try:
        # Load allocation state
        state = load_allocation_state()
        
        if not state:
            log.error("No allocation state found. Run image_allocator.py first.")
            return
        
        # Get LinkedIn images
        linkedin_images = get_linkedin_images(state, count=2)
        
        if not linkedin_images:
            log.warning("No images available for LinkedIn posting")
            return
        
        # Simulate LinkedIn posting
        posts = simulate_linkedin_posting(linkedin_images)
        
        # Save posting summary
        save_posting_summary(posts, 'LinkedIn')
        
        # Save updated state
        try:
            with open("image_allocation_state.json", 'w', encoding='utf-8') as f:
                json.dump(state, f, indent=2, ensure_ascii=False)
            log.info("Updated allocation state saved")
        except Exception as e:
            log.error(f"Failed to save allocation state: {e}")
        
        log.info(f"✅ LinkedIn posting complete: {len(posts)} posts")
        
    except Exception as e:
        log.error(f"❌ LinkedIn posting failed: {e}")

if __name__ == "__main__":
    main() 