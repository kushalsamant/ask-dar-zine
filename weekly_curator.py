#!/usr/bin/env python3
"""
Weekly Image Curator
Selects the best 10 images from the past week and creates a curated PDF.
Runs every Thursday at 4:00 AM.
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

# === 🔧 Setup real-time logging ===
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)
log_filename = os.path.join(LOG_DIR, f"weekly_curator_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
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
REQUIRED_LIBS = ['python-dotenv', 'reportlab', 'Pillow']

def install_missing_libs():
    missing_libs = []
    for lib in REQUIRED_LIBS:
        try:
            if lib == 'python-dotenv':
                __import__('dotenv')
            elif lib == 'Pillow':
                __import__('PIL')
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
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from PIL import Image
import random

# === 📥 Load environment variables ===
load_dotenv('ask.env')

def get_env(var, default=None, required=False):
    value = os.getenv(var, default)
    if required and not value:
        log.error(f"Required environment variable '{var}' is missing. Exiting.")
        sys.exit(1)
    return value

# === 📊 Configuration ===
WEEKLY_OUTPUT_PATH = get_env("WEEKLY_OUTPUT_PATH", "weekly_curated")
WEEKLY_TITLE_TEMPLATE = get_env("WEEKLY_TITLE_TEMPLATE", "ASK Weekly Curated: {week_start} - {week_end}")
CAPTION_POSITION = get_env("CAPTION_POSITION", "bottom")
CAPTION_FONT_SIZE = int(get_env("CAPTION_FONT_SIZE", "14"))
CAPTION_LINE_SPACING = int(get_env("CAPTION_LINE_SPACING", "18"))

def get_week_range():
    """Get the date range for the past week (Monday to Sunday)"""
    today = datetime.now()
    
    # Find the most recent Monday
    days_since_monday = today.weekday()
    monday = today - timedelta(days=days_since_monday)
    sunday = monday + timedelta(days=6)
    
    return monday, sunday

def collect_weekly_images():
    """Collect all images generated in the past week"""
    monday, sunday = get_week_range()
    log.info(f"Collecting images from {monday.strftime('%Y-%m-%d')} to {sunday.strftime('%Y-%m-%d')}")
    
    all_images = []
    images_dir = Path("images")
    
    if not images_dir.exists():
        log.warning("Images directory not found")
        return all_images
    
    # Walk through all style directories
    for style_dir in images_dir.iterdir():
        if style_dir.is_dir():
            log.info(f"Scanning {style_dir.name} directory")
            
            for image_file in style_dir.glob("*.jpg"):
                try:
                    # Parse timestamp from filename
                    # Expected format: style_image_01_YYYYMMDD_HHMMSS.jpg
                    parts = image_file.stem.split('_')
                    if len(parts) >= 4:
                        timestamp_str = f"{parts[-2]}_{parts[-1]}"
                        image_date = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                        
                        # Check if image is from this week
                        if monday <= image_date <= sunday:
                            all_images.append({
                                'path': image_file,
                                'style': style_dir.name,
                                'date': image_date,
                                'filename': image_file.name
                            })
                            log.info(f"Found weekly image: {image_file.name}")
                except Exception as e:
                    log.warning(f"Could not parse date from {image_file.name}: {e}")
    
    log.info(f"Collected {len(all_images)} images from this week")
    return all_images

def select_best_images(images, num_images=10):
    """Select the best images using various criteria"""
    if len(images) <= num_images:
        log.info(f"Only {len(images)} images found, using all of them")
        return images
    
    log.info(f"Selecting best {num_images} images from {len(images)} candidates")
    
    # Sort by date (newest first) to prioritize recent images
    images.sort(key=lambda x: x['date'], reverse=True)
    
    # Selection strategy: mix of styles and recency
    selected = []
    style_counts = {}
    
    # First pass: ensure diversity of styles
    for image in images:
        style = image['style']
        if style not in style_counts:
            style_counts[style] = 0
        
        # Limit each style to max 2 images for diversity
        if style_counts[style] < 2:
            selected.append(image)
            style_counts[style] += 1
            if len(selected) >= num_images:
                break
    
    # If we still need more images, add the most recent ones
    if len(selected) < num_images:
        remaining = [img for img in images if img not in selected]
        remaining.sort(key=lambda x: x['date'], reverse=True)
        selected.extend(remaining[:num_images - len(selected)])
    
    # Sort final selection by date
    selected.sort(key=lambda x: x['date'], reverse=True)
    
    log.info(f"Selected {len(selected)} images:")
    for i, img in enumerate(selected, 1):
        log.info(f"  {i}. {img['style']} - {img['filename']}")
    
    return selected

def load_captions_for_image(image):
    """Load the original caption for an image from stored captions"""
    try:
        captions_file = os.path.join("captions", f"{image['style']}_captions.txt")
        if os.path.exists(captions_file):
            with open(captions_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
            # Parse the image number from filename
            # Expected format: style_image_01_YYYYMMDD_HHMMSS.jpg
            parts = image['filename'].split('_')
            if len(parts) >= 3:
                image_num = int(parts[2])
                if image_num <= len(lines):
                    # Extract the caption (remove "Image X: " prefix)
                    caption_line = lines[image_num - 1].strip()
                    if caption_line.startswith(f"Image {image_num}: "):
                        return caption_line[len(f"Image {image_num}: "):]
        
        # Fallback caption if original not found
        style = image['style'].replace('_', ' ').title()
        date_str = image['date'].strftime("%B %d, %Y")
        
        fallback_caption = f"Weekly curated selection from {style} style, generated on {date_str}, part of our AI architecture exploration series"
        return fallback_caption
        
    except Exception as e:
        log.warning(f"Could not load caption for {image['filename']}: {e}")
        # Return a basic fallback caption
        style = image['style'].replace('_', ' ').title()
        return f"Weekly curated {style} architectural concept"

def generate_weekly_captions(selected_images):
    """Generate captions for the selected images"""
    captions = []
    
    for i, image in enumerate(selected_images, 1):
        # Load the original caption for this image
        original_caption = load_captions_for_image(image)
        captions.append(original_caption)
    
    return captions

def place_caption(c, cap, pos, w, h):
    """Place caption on PDF page"""
    text = cap.split('\n')
    c.setFont("Helvetica-Bold", CAPTION_FONT_SIZE)
    c.setFillColorRGB(0, 0, 0)
    
    # Calculate total height of caption block
    total_height = len(text) * CAPTION_LINE_SPACING
    
    if pos == "bottom":
        start_y = 60
        # Add subtle background for better readability
        c.setFillColorRGB(0.95, 0.95, 0.95)
        c.rect(30, start_y - 10, w - 60, total_height + 20, fill=1)
        c.setFillColorRGB(0, 0, 0)
        
        for i, line in enumerate(text):
            c.drawString(40, start_y + i * CAPTION_LINE_SPACING, line)
    elif pos == "top-right":
        start_y = h - 120
        for i, line in enumerate(text):
            c.drawRightString(w - 40, start_y - i * CAPTION_LINE_SPACING, line)
    elif pos == "center":
        start_y = (h + total_height) / 2
        for i, line in enumerate(text):
            c.drawCentredString(w / 2, start_y - i * CAPTION_LINE_SPACING, line)

def create_weekly_pdf(selected_images, captions):
    """Create the weekly curated PDF"""
    os.makedirs(WEEKLY_OUTPUT_PATH, exist_ok=True)
    
    monday, sunday = get_week_range()
    week_start = monday.strftime("%Y-%m-%d")
    week_end = sunday.strftime("%Y-%m-%d")
    
    title = WEEKLY_TITLE_TEMPLATE.format(week_start=week_start, week_end=week_end)
    safe_title = title.replace(" ", "_").replace(":", "_").replace("&", "and")
    fname = os.path.join(WEEKLY_OUTPUT_PATH, f"{safe_title}.pdf")
    
    c = canvas.Canvas(fname, pagesize=A4)
    w, h = A4
    
    log.info(f"Creating weekly PDF: {fname}")
    
    # Add title page
    c.setFont("Helvetica-Bold", 24)
    c.drawCentredString(w/2, h/2 + 50, "ASK Weekly Curated")
    c.setFont("Helvetica", 16)
    c.drawCentredString(w/2, h/2, f"Week of {week_start} - {week_end}")
    c.setFont("Helvetica", 12)
    c.drawCentredString(w/2, h/2 - 30, f"Best {len(selected_images)} images from our daily generation")
    c.drawCentredString(w/2, h/2 - 50, "Architecture & AI Futures")
    c.showPage()
    
    # Add image pages
    for i, (image, caption) in enumerate(zip(selected_images, captions)):
        try:
            # Full bleed image
            c.drawImage(str(image['path']), -20, -20, width=w+40, height=h+40)
            
            # Add caption
            place_caption(c, caption, CAPTION_POSITION, w, h)
            
            c.showPage()
            log.info(f"Added image {i+1}/{len(selected_images)}: {image['filename']}")
            
        except Exception as e:
            log.error(f"Failed to add image {image['filename']}: {e}")
            # Add placeholder page
            c.setFont("Helvetica", 16)
            c.drawCentredString(w/2, h/2, f"Image {i+1}: {image['style']}")
            c.setFont("Helvetica", 12)
            c.drawCentredString(w/2, h/2 - 30, f"Generated: {image['date'].strftime('%Y-%m-%d')}")
            c.showPage()
    
    c.save()
    log.info(f"✅ Weekly PDF created: {fname}")
    return fname

def create_weekly_summary(selected_images):
    """Create a summary of the weekly selection"""
    monday, sunday = get_week_range()
    
    summary_file = os.path.join(WEEKLY_OUTPUT_PATH, f"weekly_summary_{monday.strftime('%Y%m%d')}.txt")
    
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write("ASK Weekly Curated Summary\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"Week: {monday.strftime('%Y-%m-%d')} to {sunday.strftime('%Y-%m-%d')}\n")
        f.write(f"Total images selected: {len(selected_images)}\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("Selected Images:\n")
        f.write("-" * 30 + "\n")
        
        style_counts = {}
        for i, image in enumerate(selected_images, 1):
            style = image['style']
            style_counts[style] = style_counts.get(style, 0) + 1
            
            f.write(f"{i:2d}. {style:15s} - {image['filename']}\n")
            f.write(f"     Generated: {image['date'].strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("\nStyle Distribution:\n")
        f.write("-" * 30 + "\n")
        for style, count in style_counts.items():
            f.write(f"{style:15s}: {count} images\n")
    
    log.info(f"Weekly summary created: {summary_file}")

def main():
    log.info("=== Weekly Image Curator Started ===")
    
    try:
        # Collect all images from this week
        weekly_images = collect_weekly_images()
        
        if not weekly_images:
            log.warning("No images found from this week")
            return
        
        # Select the best 10 images
        selected_images = select_best_images(weekly_images, 10)
        
        if not selected_images:
            log.warning("No images selected")
            return
        
        # Generate captions
        captions = generate_weekly_captions(selected_images)
        
        # Create weekly PDF
        pdf_path = create_weekly_pdf(selected_images, captions)
        
        # Create summary
        create_weekly_summary(selected_images)
        
        log.info("=== Weekly Curator Complete ===")
        log.info(f"✅ Created: {pdf_path}")
        log.info(f"📊 Selected {len(selected_images)} images from {len(weekly_images)} candidates")
        
    except Exception as e:
        log.error(f"❌ Weekly curator failed: {e}")
        raise e

if __name__ == "__main__":
    main() 