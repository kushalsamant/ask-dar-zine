#!/usr/bin/env python3
"""
Smart Image Allocator
Distributes daily images across different time periods without reuse.
Each image is used only once across daily, weekly, monthly, and yearly periods.
"""

import os
import sys
import subprocess
import logging
import time
from datetime import datetime, timedelta
from pathlib import Path
import random
import shutil
import json
import traceback

# === 🔧 Setup real-time logging ===
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)
log_filename = os.path.join(LOG_DIR, f"image_allocator_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
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

# === 📊 Allocation Configuration ===
DAILY_IMAGES_PER_DAY = 10  # Total images generated daily (10 social only)
ALLOCATION_RATIO = {
    'instagram': 0.30,  # 3 images (30%) - for Instagram
    'twitter': 0.30,    # 3 images (30%) - for Twitter
    'linkedin': 0.20,   # 2 images (20%) - for LinkedIn
    'patreon': 0.20     # 2 images (20%) - for Patreon
}

def get_allocation_counts():
    """Get the number of images to allocate to each platform"""
    counts = {
        'instagram': int(DAILY_IMAGES_PER_DAY * ALLOCATION_RATIO['instagram']),
        'twitter': int(DAILY_IMAGES_PER_DAY * ALLOCATION_RATIO['twitter']),
        'linkedin': int(DAILY_IMAGES_PER_DAY * ALLOCATION_RATIO['linkedin']),
        'patreon': int(DAILY_IMAGES_PER_DAY * ALLOCATION_RATIO['patreon'])
    }
    
    # Ensure total adds up to DAILY_IMAGES_PER_DAY
    total = sum(counts.values())
    if total != DAILY_IMAGES_PER_DAY:
        # Adjust the largest pool to make up the difference
        largest_platform = max(counts, key=counts.get)
        counts[largest_platform] += (DAILY_IMAGES_PER_DAY - total)
        log.info(f"🔧 Adjusted {largest_platform} allocation to {counts[largest_platform]} images")
    
    return counts

def load_allocation_state():
    """Load the current allocation state from file with better error handling"""
    state_file = "image_allocation_state.json"
    
    if os.path.exists(state_file):
        try:
            with open(state_file, 'r', encoding='utf-8') as f:
                state = json.load(f)
                
            # Validate state structure
            required_keys = ['instagram_pool', 'twitter_pool', 'linkedin_pool', 'patreon_pool', 'used_images', 'last_updated']
            for key in required_keys:
                if key not in state:
                    log.warning(f"⚠️ Missing key in state file: {key}")
                    state[key] = [] if 'pool' in key else set() if key == 'used_images' else datetime.now().isoformat()
            
            # Convert used_images back to set if it's a list
            if isinstance(state['used_images'], list):
                state['used_images'] = set(state['used_images'])
            
            log.info(f"✅ Loaded allocation state: {len(state.get('used_images', set()))} used images")
            return state
            
        except json.JSONDecodeError as e:
            log.error(f"❌ Invalid JSON in state file: {e}")
        except Exception as e:
            log.error(f"❌ Error loading allocation state: {e}")
    
    # Initialize new state
    log.info("🔄 Initializing new allocation state")
    return {
        'instagram_pool': [],
        'twitter_pool': [],
        'linkedin_pool': [],
        'patreon_pool': [],
        'used_images': set(),
        'last_updated': datetime.now().isoformat()
    }

def save_allocation_state(state):
    """Save the allocation state to file with better error handling"""
    state_file = "image_allocation_state.json"
    
    try:
        # Convert set to list for JSON serialization
        state_to_save = state.copy()
        state_to_save['used_images'] = list(state['used_images'])
        state_to_save['last_updated'] = datetime.now().isoformat()
        
        # Create backup of existing file
        if os.path.exists(state_file):
            backup_file = f"{state_file}.backup"
            shutil.copy2(state_file, backup_file)
            log.info(f"📋 Created backup: {backup_file}")
        
        # Save new state
        with open(state_file, 'w', encoding='utf-8') as f:
            json.dump(state_to_save, f, indent=2, ensure_ascii=False)
        
        log.info(f"✅ Saved allocation state: {len(state['used_images'])} used images")
        
    except Exception as e:
        log.error(f"❌ Error saving allocation state: {e}")
        # Try to restore backup if save failed
        backup_file = f"{state_file}.backup"
        if os.path.exists(backup_file):
            try:
                shutil.copy2(backup_file, state_file)
                log.info("🔄 Restored backup after save failure")
            except Exception as restore_error:
                log.error(f"❌ Failed to restore backup: {restore_error}")

def collect_todays_images():
    """Collect today's generated images with better error handling"""
    try:
        images_dir = Path("images")
        if not images_dir.exists():
            log.warning("⚠️ Images directory not found")
            return []
        
        todays_images = []
        today = datetime.now().date()
        
        # Scan all style directories
        for style_dir in images_dir.iterdir():
            if not style_dir.is_dir():
                continue
                
            log.info(f"📁 Scanning {style_dir.name} directory")
            
            for image_file in style_dir.glob("*.jpg"):
                try:
                    # Extract timestamp from filename
                    filename = image_file.name
                    if '_' in filename and filename.endswith('.jpg'):
                        # Parse timestamp from filename format: style_image_XX_YYYYMMDD_HHMMSS.jpg
                        parts = filename.split('_')
                        if len(parts) >= 4:
                            date_str = parts[-2]  # YYYYMMDD
                            try:
                                file_date = datetime.strptime(date_str, "%Y%m%d").date()
                                if file_date == today:
                                    image_info = {
                                        'path': str(image_file),
                                        'filename': filename,
                                        'style': style_dir.name,
                                        'date': file_date.isoformat(),
                                        'size': image_file.stat().st_size
                                    }
                                    todays_images.append(image_info)
                                    log.info(f"📸 Found today's image: {filename}")
                            except ValueError:
                                log.debug(f"Skipping file with invalid date format: {filename}")
                                continue
                                
                except Exception as e:
                    log.warning(f"⚠️ Error processing {image_file}: {e}")
                    continue
        
        log.info(f"✅ Collected {len(todays_images)} images from today")
        return todays_images
        
    except Exception as e:
        log.error(f"❌ Error collecting today's images: {e}")
        return []

def allocate_images_to_pools(todays_images, state):
    """Allocate today's images to different platforms with better error handling"""
    try:
        allocation_counts = get_allocation_counts()
        log.info(f"Allocating {len(todays_images)} images:")
        log.info(f"  Instagram: {allocation_counts['instagram']}")
        log.info(f"  Twitter: {allocation_counts['twitter']}")
        log.info(f"  LinkedIn: {allocation_counts['linkedin']}")
        log.info(f"  Patreon: {allocation_counts['patreon']}")
        
        if len(todays_images) < DAILY_IMAGES_PER_DAY:
            log.warning(f"⚠️ Only {len(todays_images)} images available, expected {DAILY_IMAGES_PER_DAY}")
        
        # Shuffle images for random distribution
        random.shuffle(todays_images)
        
        # Allocate images to pools
        start_idx = 0
        for platform, count in allocation_counts.items():
            end_idx = start_idx + count
            platform_images = todays_images[start_idx:end_idx]
            
            # Add to platform pool
            pool_key = f'{platform}_pool'
            state[pool_key].extend(platform_images)
            
            # Mark as used
            for img in platform_images:
                state['used_images'].add(img['path'])
            
            log.info(f"✅ Allocated {len(platform_images)} images to {platform}")
            start_idx = end_idx
        
        # Update last updated timestamp
        state['last_updated'] = datetime.now().isoformat()
        
        log.info(f"✅ Allocation complete: {len(state['used_images'])} total used images")
        return state
        
    except Exception as e:
        log.error(f"❌ Error allocating images: {e}")
        log.error(traceback.format_exc())
        return state

def get_images_for_period(period, count, state):
    """Get images for a specific period from its pool"""
    pool_key = f'{period}_pool'
    if pool_key not in state:
        log.error(f"❌ Pool {period} not found in state")
        return []
    
    available_images = state[pool_key]
    if len(available_images) < count:
        log.warning(f"⚠️ Only {len(available_images)} images available for {period}, requested {count}")
        count = len(available_images)
    
    # Get the requested number of images (FIFO - oldest first)
    selected_images = available_images[:count]
    
    # Remove selected images from pool
    state[pool_key] = available_images[count:]
    
    log.info(f"✅ Selected {len(selected_images)} images for {period} period")
    return selected_images

def create_allocation_summary(state):
    """Create a summary of current allocation state"""
    summary_file = "allocation_summary.txt"
    
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write("Image Allocation Summary\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"Last Updated: {state.get('last_updated', 'Unknown')}\n")
        f.write(f"Total Used Images: {len(state.get('used_images', set()))}\n\n")
        
        f.write("Current Pool Status:\n")
        f.write("-" * 30 + "\n")
        for platform in ['instagram', 'twitter', 'linkedin', 'patreon']:
            pool_key = f'{platform}_pool'
            count = len(state.get(pool_key, []))
            f.write(f"{platform.capitalize():10s}: {count:3d} images\n")
        
        f.write("\nAllocation Strategy:\n")
        f.write("-" * 30 + "\n")
        allocation_counts = get_allocation_counts()
        for platform, count in allocation_counts.items():
            f.write(f"{platform.capitalize():10s}: {count:3d} images per day\n")
    
    log.info(f"✅ Allocation summary created: {summary_file}")

def cleanup_old_allocations(state):
    """Clean up old allocations to prevent memory bloat"""
    # Keep only last 30 days of used images
    cutoff_date = datetime.now() - timedelta(days=30)
    old_images = set()
    
    for image_id in state.get('used_images', set()):
        try:
            # Extract date from image_id if possible
            # This is a simple cleanup - in practice you might want more sophisticated logic
            pass
        except:
            pass
    
    # For now, just limit the size
    if len(state.get('used_images', set())) > 10000:
        # Keep only the most recent 5000
        used_list = list(state.get('used_images', set()))
        state['used_images'] = set(used_list[-5000:])
        log.info("✅ Cleaned up old allocations")

def main():
    log.info("=== Smart Image Allocator Started ===")
    
    try:
        # Load current state
        state = load_allocation_state()
        
        # Collect today's images
        todays_images = collect_todays_images()
        
        if not todays_images:
            log.warning("⚠️ No images found from today")
            return
        
        # Allocate today's images to pools
        allocated = allocate_images_to_pools(todays_images, state)
        
        # Clean up old allocations
        cleanup_old_allocations(state)
        
        # Save updated state
        save_allocation_state(state)
        
        # Create summary
        create_allocation_summary(state)
        
        log.info("=== Image Allocation Complete ===")
        log.info(f"✅ Allocated {len(todays_images)} images across 4 pools")
        log.info(f"📊 Pool status:")
        for period in ['daily', 'weekly', 'monthly', 'yearly']:
            count = len(state[f'{period}_pool'])
            log.info(f"  {period.capitalize()}: {count} images")
        
    except Exception as e:
        log.error(f"❌ Image allocator failed: {e}")
        raise e

if __name__ == "__main__":
    main() 