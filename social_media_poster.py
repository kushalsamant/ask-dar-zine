#!/usr/bin/env python3
"""
Social Media Auto-Poster
Automatically posts generated images to social media platforms.
"""

import os
import sys
import logging
import time
from datetime import datetime
from pathlib import Path
import random

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)

def get_env(var, default=None):
    return os.getenv(var, default)

class SocialMediaPoster:
    def __init__(self):
        self.platforms = {
            'instagram': self.post_to_instagram,
            'twitter': self.post_to_twitter,
            'linkedin': self.post_to_linkedin
        }
    
    def generate_caption(self, image_path, style_name):
        """Generate platform-specific captions"""
        style_display = style_name.replace('_', ' ').title()
        
        # Base caption
        base_caption = f"🎨 AI-generated architectural concept in {style_display} style\n\n"
        
        # Platform-specific additions
        platform_additions = {
            'instagram': f"#AIArt #Architecture #Design #Innovation #FutureOfDesign #AIArchitecture #DigitalArt #CreativeTech #ArchitecturalDesign #AI",
            'twitter': f"#AIArt #Architecture #Design #Innovation #FutureOfDesign #AIArchitecture #DigitalArt #CreativeTech #ArchitecturalDesign #AI",
            'linkedin': f"#AIArt #Architecture #Design #Innovation #FutureOfDesign #AIArchitecture #DigitalArt #CreativeTech #ArchitecturalDesign #AI #ProfessionalDevelopment"
        }
        
        return base_caption + platform_additions.get('instagram', '')
    
    def post_to_instagram(self, image_path, caption):
        """Post to Instagram (placeholder for API integration)"""
        log.info(f"📸 Instagram: Would post {image_path}")
        log.info(f"📝 Caption: {caption[:100]}...")
        # TODO: Integrate with Instagram API
        return True
    
    def post_to_twitter(self, image_path, caption):
        """Post to Twitter/X (placeholder for API integration)"""
        log.info(f"🐦 Twitter: Would post {image_path}")
        log.info(f"📝 Caption: {caption[:100]}...")
        # TODO: Integrate with Twitter API
        return True
    
    def post_to_linkedin(self, image_path, caption):
        """Post to LinkedIn (placeholder for API integration)"""
        log.info(f"💼 LinkedIn: Would post {image_path}")
        log.info(f"📝 Caption: {caption[:100]}...")
        # TODO: Integrate with LinkedIn API
        return True
    
    def select_images_for_posting(self, max_images=3):
        """Select random images from today's generation for posting"""
        images_dir = Path("images")
        if not images_dir.exists():
            log.warning("No images directory found")
            return []
        
        all_images = []
        for style_dir in images_dir.iterdir():
            if style_dir.is_dir():
                for image_file in style_dir.glob("*.jpg"):
                    # Check if image is from today
                    if self.is_image_from_today(image_file):
                        all_images.append({
                            'path': image_file,
                            'style': style_dir.name,
                            'filename': image_file.name
                        })
        
        # Select random images
        selected = random.sample(all_images, min(max_images, len(all_images)))
        log.info(f"Selected {len(selected)} images for posting")
        return selected
    
    def is_image_from_today(self, image_file):
        """Check if image was generated today"""
        try:
            # Parse timestamp from filename
            parts = image_file.stem.split('_')
            if len(parts) >= 4:
                timestamp_str = f"{parts[-2]}_{parts[-1]}"
                image_date = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                today = datetime.now()
                return image_date.date() == today.date()
        except:
            pass
        return False
    
    def post_images(self, platforms=None, max_images=3):
        """Post images to specified platforms"""
        if platforms is None:
            platforms = ['instagram', 'twitter', 'linkedin']
        
        selected_images = self.select_images_for_posting(max_images)
        if not selected_images:
            log.warning("No images found for posting")
            return
        
        for image_info in selected_images:
            image_path = image_info['path']
            style_name = image_info['style']
            
            caption = self.generate_caption(image_path, style_name)
            
            for platform in platforms:
                if platform in self.platforms:
                    try:
                        success = self.platforms[platform](image_path, caption)
                        if success:
                            log.info(f"✅ Posted to {platform}: {image_path.name}")
                        else:
                            log.error(f"❌ Failed to post to {platform}: {image_path.name}")
                        
                        # Add delay between platforms
                        time.sleep(2)
                        
                    except Exception as e:
                        log.error(f"❌ Error posting to {platform}: {e}")
                
                # Add delay between images
                time.sleep(5)

def main():
    """Main function to run social media posting"""
    log.info("🚀 Starting social media auto-posting...")
    
    poster = SocialMediaPoster()
    
    # Get configuration
    max_images = int(get_env("SOCIAL_MAX_IMAGES", "3"))
    platforms = get_env("SOCIAL_PLATFORMS", "instagram,twitter,linkedin").split(',')
    
    log.info(f"📊 Configuration: {max_images} images to {', '.join(platforms)}")
    
    # Post images
    poster.post_images(platforms=platforms, max_images=max_images)
    
    log.info("✅ Social media posting complete!")

if __name__ == "__main__":
    main() 