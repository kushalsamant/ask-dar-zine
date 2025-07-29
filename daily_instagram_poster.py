#!/usr/bin/env python3
"""
Daily Instagram Poster
Posts 3 images daily to Instagram from the Instagram pool.
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
import traceback

# === 🔧 Setup real-time logging ===
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)
log_filename = os.path.join(LOG_DIR, f"instagram_poster_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(log_filename, mode='w', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
log = logging.getLogger(__name__)

# === 🛠️ Auto-install missing dependencies ===
REQUIRED_LIBS = ['python-dotenv']

def install_missing_libs():
    """Install missing dependencies with better error handling"""
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
                subprocess.check_call([sys.executable, "-m", "pip", "install", lib], 
                                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                log.info(f"✅ Installed: {lib}")
            except subprocess.CalledProcessError as e:
                log.error(f"❌ Failed to install {lib}: {e}")
                sys.exit(1)
    else:
        log.info("✅ All dependencies are already installed")

install_missing_libs()

# === Now import everything ===
try:
    from dotenv import load_dotenv
    log.info("✅ All imports successful")
except ImportError as e:
    log.error(f"❌ Import error: {e}")
    sys.exit(1)

# === 📥 Load environment variables ===
load_dotenv('ask.env')

def get_env(var, default=None, required=False):
    """Get environment variable with better error handling"""
    value = os.getenv(var, default)
    if required and not value:
        log.error(f"❌ Required environment variable '{var}' is missing. Exiting.")
        sys.exit(1)
    return value

def load_allocation_state():
    """Load the current allocation state from file with better error handling"""
    state_file = "image_allocation_state.json"
    
    if os.path.exists(state_file):
        try:
            with open(state_file, 'r', encoding='utf-8') as f:
                state = json.load(f)
            
            # Validate state structure
            if 'instagram_pool' not in state:
                log.warning("⚠️ Instagram pool not found in state file")
                state['instagram_pool'] = []
            
            log.info(f"✅ Loaded allocation state: {len(state.get('instagram_pool', []))} Instagram images")
            return state
            
        except json.JSONDecodeError as e:
            log.error(f"❌ Invalid JSON in state file: {e}")
        except Exception as e:
            log.error(f"❌ Error loading allocation state: {e}")
    
    log.warning("⚠️ Using empty allocation state")
    return {'instagram_pool': []}

def save_allocation_state(state):
    """Save the allocation state to file with better error handling"""
    state_file = "image_allocation_state.json"
    
    try:
        # Create backup of existing file
        if os.path.exists(state_file):
            backup_file = f"{state_file}.backup"
            import shutil
            shutil.copy2(state_file, backup_file)
            log.info(f"📋 Created backup: {backup_file}")
        
        # Save new state
        with open(state_file, 'w', encoding='utf-8') as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
        
        log.info(f"✅ Saved allocation state: {len(state.get('instagram_pool', []))} Instagram images remaining")
        
    except Exception as e:
        log.error(f"❌ Error saving allocation state: {e}")

def get_instagram_images(state, count=3):
    """Get images from Instagram pool with better error handling"""
    try:
        instagram_pool = state.get('instagram_pool', [])
        
        if len(instagram_pool) < count:
            log.warning(f"⚠️ Only {len(instagram_pool)} images available in Instagram pool, requested {count}")
            count = len(instagram_pool)
        
        if count == 0:
            log.warning("⚠️ No images available in Instagram pool")
            return [], state
        
        # Get the requested number of images (FIFO - oldest first)
        selected_images = instagram_pool[:count]
        
        # Remove selected images from pool
        state['instagram_pool'] = instagram_pool[count:]
        
        log.info(f"✅ Selected {len(selected_images)} images from Instagram pool")
        return selected_images, state
        
    except Exception as e:
        log.error(f"❌ Error getting Instagram images: {e}")
        return [], state

def load_caption_for_image(image_path):
    """Load caption for an image with better error handling"""
    try:
        # Extract style and image number from path
        path_parts = Path(image_path).parts
        if len(path_parts) < 2:
            log.warning(f"⚠️ Invalid image path structure: {image_path}")
            return "Architecture speaks through silent spaces"
        
        style = path_parts[-2]  # images/style/image.jpg
        filename = path_parts[-1]
        
        # Look for caption in captions directory
        captions_dir = Path("captions")
        if not captions_dir.exists():
            log.warning("⚠️ Captions directory not found")
            return "Architecture speaks through silent spaces"
        
        # Try to find caption file for this style
        caption_file = captions_dir / f"{style}_captions.txt"
        if not caption_file.exists():
            log.warning(f"⚠️ Caption file not found: {caption_file}")
            return "Architecture speaks through silent spaces"
        
        # Read caption file
        with open(caption_file, 'r', encoding='utf-8') as f:
            captions = f.readlines()
        
        if not captions:
            log.warning(f"⚠️ Empty caption file: {caption_file}")
            return "Architecture speaks through silent spaces"
        
        # Extract image number from filename and get corresponding caption
        try:
            # Parse image number from filename: style_image_XX_YYYYMMDD_HHMMSS.jpg
            parts = filename.split('_')
            if len(parts) >= 3:
                image_num = int(parts[2]) - 1  # Convert to 0-based index
                if 0 <= image_num < len(captions):
                    caption = captions[image_num].strip()
                    if caption:
                        log.info(f"✅ Loaded caption for {filename}")
                        return caption
        except (ValueError, IndexError) as e:
            log.warning(f"⚠️ Could not parse image number from {filename}: {e}")
        
        # Fallback to first caption
        fallback_caption = captions[0].strip() if captions else "Architecture speaks through silent spaces"
        log.info(f"🔄 Using fallback caption for {filename}")
        return fallback_caption
        
    except Exception as e:
        log.error(f"❌ Error loading caption for {image_path}: {e}")
        return "Architecture speaks through silent spaces"

def create_instagram_caption(image_info, base_caption):
    """Create Instagram-optimized caption with hashtags"""
    try:
        # Instagram hashtags for architecture and design
        hashtags = [
            "#architecture", "#design", "#architecturalphotography", "#modernarchitecture",
            "#architecturedesign", "#architectural", "#buildingdesign", "#architecturalart",
            "#architecturalstyle", "#architecturalphotography", "#architecturaldrawing",
            "#architecturalconcept", "#architecturalvision", "#architecturalinspiration"
        ]
        
        # Create caption with line breaks and hashtags
        caption = f"{base_caption}\n\n"
        caption += "🏗️ Exploring the intersection of form, function, and artistic vision.\n"
        caption += "📐 Where mathematics meets creativity in built environments.\n\n"
        caption += " ".join(hashtags)
        
        log.info(f"✅ Created Instagram caption ({len(caption)} chars)")
        return caption
        
    except Exception as e:
        log.error(f"❌ Error creating Instagram caption: {e}")
        return base_caption

def simulate_instagram_posting(images):
    """Simulate posting to Instagram with better error handling"""
    try:
        posts = []
        
        for i, image_info in enumerate(images, 1):
            try:
                image_path = image_info['path']
                
                # Verify image file exists
                if not os.path.exists(image_path):
                    log.error(f"❌ Image file not found: {image_path}")
                    continue
                
                # Load caption
                base_caption = load_caption_for_image(image_path)
                instagram_caption = create_instagram_caption(image_info, base_caption)
                
                # Simulate posting delay
                time.sleep(random.uniform(1, 3))
                
                post_info = {
                    'platform': 'Instagram',
                    'image_path': image_path,
                    'caption': instagram_caption,
                    'timestamp': datetime.now().isoformat(),
                    'post_number': i,
                    'file_size': os.path.getsize(image_path)
                }
                
                posts.append(post_info)
                log.info(f"✅ Simulated Instagram post {i}: {os.path.basename(image_path)}")
                
            except Exception as e:
                log.error(f"❌ Error processing image {i}: {e}")
                continue
        
        log.info(f"✅ Completed Instagram posting simulation: {len(posts)} posts")
        return posts
        
    except Exception as e:
        log.error(f"❌ Error in Instagram posting simulation: {e}")
        return []

def save_posting_summary(posts, platform):
    """Save posting summary with better error handling"""
    try:
        if not posts:
            log.warning("⚠️ No posts to save")
            return
        
        # Create posts directory
        posts_dir = Path("posts")
        posts_dir.mkdir(exist_ok=True)
        
        # Save summary
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        summary_file = posts_dir / f"{platform.lower()}_posts_{timestamp}.json"
        
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(posts, f, indent=2, ensure_ascii=False)
        
        log.info(f"✅ Saved {platform} posting summary: {summary_file}")
        
        # Create human-readable summary
        text_summary_file = posts_dir / f"{platform.lower()}_posts_{timestamp}.txt"
        with open(text_summary_file, 'w', encoding='utf-8') as f:
            f.write(f"{platform} Posting Summary - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 60 + "\n\n")
            
            for i, post in enumerate(posts, 1):
                f.write(f"Post {i}:\n")
                f.write(f"  Image: {os.path.basename(post['image_path'])}\n")
                f.write(f"  Size: {post['file_size']} bytes\n")
                f.write(f"  Caption: {post['caption'][:100]}...\n")
                f.write(f"  Time: {post['timestamp']}\n")
                f.write("-" * 40 + "\n\n")
        
        log.info(f"✅ Saved {platform} text summary: {text_summary_file}")
        
    except Exception as e:
        log.error(f"❌ Error saving posting summary: {e}")

def main():
    """Main function with comprehensive error handling"""
    try:
        log.info("🚀 Starting Instagram posting process...")
        
        # Load allocation state
        state = load_allocation_state()
        
        # Get Instagram images
        images, state = get_instagram_images(state, count=3)
        
        if not images:
            log.warning("⚠️ No images to post to Instagram")
            return
        
        # Simulate posting
        posts = simulate_instagram_posting(images)
        
        if posts:
            # Save posting summary
            save_posting_summary(posts, "Instagram")
            
            # Save updated allocation state
            save_allocation_state(state)
            
            log.info(f"🎉 Instagram posting complete: {len(posts)} posts")
        else:
            log.warning("⚠️ No posts were created")
        
    except Exception as e:
        log.error(f"❌ Instagram posting failed: {e}")
        log.error(traceback.format_exc())

if __name__ == "__main__":
    main() 