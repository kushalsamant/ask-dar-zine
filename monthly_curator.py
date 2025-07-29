#!/usr/bin/env python3
"""
Monthly Image Curator
Collects all images generated in the current month and creates a comprehensive monthly PDF.
Runs on the last day of the month at 4:00 AM.
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
import calendar

# === 🔧 Setup real-time logging ===
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)
log_filename = os.path.join(LOG_DIR, f"monthly_curator_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
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
MONTHLY_OUTPUT_PATH = get_env("MONTHLY_OUTPUT_PATH", "monthly_curated")
MONTHLY_TITLE_TEMPLATE = get_env("MONTHLY_TITLE_TEMPLATE", "ASK Monthly Collection: {month_name} {year}")
CAPTION_POSITION = get_env("CAPTION_POSITION", "bottom")
CAPTION_FONT_SIZE = int(get_env("CAPTION_FONT_SIZE", "12"))
CAPTION_LINE_SPACING = int(get_env("CAPTION_LINE_SPACING", "16"))

def get_month_range():
    """Get the date range for the current month"""
    today = datetime.now()
    first_day = today.replace(day=1)
    last_day = today.replace(day=calendar.monthrange(today.year, today.month)[1])
    
    return first_day, last_day

def collect_monthly_images():
    """Collect images from the monthly pool using the allocator"""
    try:
        from image_allocator import load_allocation_state, get_images_for_period
        
        # Load allocation state
        state = load_allocation_state()
        
        # Get images from monthly pool (need 32 for monthly PDF)
        monthly_images = get_images_for_period('monthly', 32, state)
        
        # Save updated state
        from image_allocator import save_allocation_state
        save_allocation_state(state)
        
        log.info(f"Collected {len(monthly_images)} images from monthly pool")
        return monthly_images
        
    except ImportError:
        log.warning("Image allocator not available, falling back to old method")
        return collect_monthly_images_fallback()

def collect_monthly_images_fallback():
    """Fallback method: collect images from the past month"""
    month_start, month_end = get_month_range()
    log.info(f"Collecting images from {month_start.strftime('%Y-%m-%d')} to {month_end.strftime('%Y-%m-%d')}")
    
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
                        
                        # Check if image is from this month
                        if month_start <= image_date <= month_end:
                            all_images.append({
                                'path': image_file,
                                'style': style_dir.name,
                                'date': image_date,
                                'filename': image_file.name
                            })
                            log.info(f"Found monthly image: {image_file.name}")
                except Exception as e:
                    log.warning(f"Could not parse date from {image_file.name}: {e}")
    
    log.info(f"Collected {len(all_images)} images from this month")
    return all_images

def organize_images_by_style(images):
    """Organize images by style for better presentation"""
    style_groups = {}
    
    for image in images:
        style = image['style']
        if style not in style_groups:
            style_groups[style] = []
        style_groups[style].append(image)
    
    # Sort images within each style by date
    for style in style_groups:
        style_groups[style].sort(key=lambda x: x['date'])
    
    return style_groups

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
        
        fallback_caption = f"Monthly collection from {style} style, generated on {date_str}, part of our comprehensive AI architecture archive"
        return fallback_caption
        
    except Exception as e:
        log.warning(f"Could not load caption for {image['filename']}: {e}")
        # Return a basic fallback caption
        style = image['style'].replace('_', ' ').title()
        return f"Monthly collection {style} architectural concept"

def generate_monthly_captions(image, style_count, total_count):
    """Generate captions for monthly images"""
    # Load the original caption for this image
    original_caption = load_captions_for_image(image)
    
    # Add monthly collection context
    style = image['style'].replace('_', ' ').title()
    date_str = image['date'].strftime("%B %d, %Y")
    
    caption_lines = [
        f"Monthly collection image {total_count}",
        f"Style: {style} ({style_count} total)",
        f"Generated on {date_str}",
        f"Day {image['day_of_month']} of {image['date'].strftime('%B %Y')}",
        f"Part of our AI architecture exploration",
        f"ASK: Architecture, Space, Knowledge"
    ]
    
    return '\n'.join(caption_lines)

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

def create_monthly_pdf(style_groups):
    """Create monthly PDF for digital sales"""
    try:
        from digital_pdf_creator import DigitalPDFCreator
        
        creator = DigitalPDFCreator()
        
        # Flatten all images into a single list with captions
        all_images = []
        all_captions = []
        for style, images in style_groups.items():
            for image in images:
                image['style'] = style  # Ensure style is set
                all_images.append(image)
                # Generate caption for this image
                caption = generate_monthly_captions(image, len(images), len(all_images))
                all_captions.append(caption)
        
        pdf_path = creator.create_monthly_pdf(all_images, all_captions)
        
        log.info(f"✅ Created monthly PDF: {pdf_path}")
        return pdf_path
        
    except ImportError:
        log.warning("Digital PDF creator not available, falling back to basic PDF")
        return create_monthly_pdf_fallback(style_groups)

def create_monthly_pdf_fallback(style_groups):
    """Fallback: Create single monthly PDF if volume optimizer is not available"""
    os.makedirs(MONTHLY_OUTPUT_PATH, exist_ok=True)
    
    first_day, last_day = get_month_range()
    month_name = first_day.strftime("%B")
    year = first_day.year
    
    title = MONTHLY_TITLE_TEMPLATE.format(month_name=month_name, year=year)
    safe_title = title.replace(" ", "_").replace(":", "_").replace("&", "and")
    fname = os.path.join(MONTHLY_OUTPUT_PATH, f"{safe_title}.pdf")
    
    c = canvas.Canvas(fname, pagesize=A4)
    w, h = A4
    
    log.info(f"Creating monthly PDF: {fname}")
    
    # Add title page
    c.setFont("Helvetica-Bold", 28)
    c.drawCentredString(w/2, h/2 + 80, "ASK Monthly Collection")
    c.setFont("Helvetica", 20)
    c.drawCentredString(w/2, h/2 + 40, f"{month_name} {year}")
    c.setFont("Helvetica", 14)
    c.drawCentredString(w/2, h/2, f"Complete collection of AI-generated architectural images")
    c.drawCentredString(w/2, h/2 - 20, f"Generated from {first_day.strftime('%B %d')} to {last_day.strftime('%B %d, %Y')}")
    
    # Add statistics
    total_images = sum(len(images) for images in style_groups.values())
    c.setFont("Helvetica", 12)
    c.drawCentredString(w/2, h/2 - 50, f"Total Images: {total_images}")
    c.drawCentredString(w/2, h/2 - 70, f"Styles: {len(style_groups)}")
    c.drawCentredString(w/2, h/2 - 90, "Architecture & AI Futures")
    c.showPage()
    
    # Add style index page
    c.setFont("Helvetica-Bold", 18)
    c.drawCentredString(w/2, h - 50, "Style Index")
    c.setFont("Helvetica", 12)
    
    y_position = h - 100
    for i, (style, images) in enumerate(style_groups.items(), 1):
        style_name = style.replace('_', ' ').title()
        c.drawString(50, y_position, f"{i}. {style_name}: {len(images)} images")
        y_position -= 25
        
        if y_position < 100:  # Start new column
            y_position = h - 100
            c.drawString(w/2 + 560, y_position, f"{i}. {style_name}: {len(images)} images")
            y_position -= 25
    
    c.showPage()
    
    # Add images organized by style
    total_count = 0
    for style, images in style_groups.items():
        # Add style header page
        c.setFont("Helvetica-Bold", 24)
        style_name = style.replace('_', ' ').title()
        c.drawCentredString(w/2, h/2 + 30, style_name)
        c.setFont("Helvetica", 16)
        c.drawCentredString(w/2, h/2, f"{len(images)} images")
        c.setFont("Helvetica", 12)
        c.drawCentredString(w/2, h/2 - 30, f"Generated throughout {month_name} {year}")
        c.showPage()
        
        # Add images for this style
        for i, image in enumerate(images):
            total_count += 1
            try:
                # Full bleed image
                c.drawImage(str(image['path']), -20, -20, width=w+40, height=h+40)
                
                # Add caption
                caption = generate_monthly_captions(image, len(images), total_count)
                place_caption(c, caption, CAPTION_POSITION, w, h)
                
                c.showPage()
                log.info(f"Added image {total_count}/{sum(len(imgs) for imgs in style_groups.values())}: {image['filename']}")
                
            except Exception as e:
                log.error(f"Failed to add image {image['filename']}: {e}")
                # Add placeholder page
                c.setFont("Helvetica", 16)
                c.drawCentredString(w/2, h/2, f"Image {total_count}: {style}")
                c.setFont("Helvetica", 12)
                c.drawCentredString(w/2, h/2 - 30, f"Generated: {image['date'].strftime('%Y-%m-%d')}")
                c.showPage()
    
    c.save()
    log.info(f"✅ Monthly PDF created: {fname}")
    return fname

def create_monthly_summary(style_groups):
    """Create a comprehensive summary of the monthly collection"""
    first_day, last_day = get_month_range()
    
    summary_file = os.path.join(MONTHLY_OUTPUT_PATH, f"monthly_summary_{first_day.strftime('%Y%m')}.txt")
    
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write("ASK Monthly Collection Summary\n")
        f.write("=" * 60 + "\n\n")
        f.write(f"Month: {first_day.strftime('%B %Y')}\n")
        f.write(f"Period: {first_day.strftime('%Y-%m-%d')} to {last_day.strftime('%Y-%m-%d')}\n")
        f.write(f"Total images: {sum(len(images) for images in style_groups.values())}\n")
        f.write(f"Styles represented: {len(style_groups)}\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("Style Breakdown:\n")
        f.write("-" * 40 + "\n")
        for style, images in style_groups.items():
            style_name = style.replace('_', ' ').title()
            f.write(f"{style_name:20s}: {len(images):3d} images\n")
        f.write("\n")
        
        f.write("Daily Distribution:\n")
        f.write("-" * 40 + "\n")
        daily_counts = {}
        for images in style_groups.values():
            for image in images:
                day = image['date'].day
                daily_counts[day] = daily_counts.get(day, 0) + 1
        
        for day in sorted(daily_counts.keys()):
            f.write(f"Day {day:2d}: {daily_counts[day]:3d} images\n")
        f.write("\n")
        
        f.write("Detailed Image List:\n")
        f.write("-" * 40 + "\n")
        total_count = 0
        for style, images in style_groups.items():
            f.write(f"\n{style.replace('_', ' ').title()}:\n")
            for i, image in enumerate(images, 1):
                total_count += 1
                f.write(f"  {total_count:3d}. {image['filename']}\n")
                f.write(f"       Generated: {image['date'].strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    log.info(f"Monthly summary created: {summary_file}")

def main():
    log.info("=== Monthly Image Curator Started ===")
    
    try:
        # Collect all images from this month
        monthly_images = collect_monthly_images()
        
        if not monthly_images:
            log.warning("No images found from this month")
            return
        
        # Organize images by style
        style_groups = organize_images_by_style(monthly_images)
        
        if not style_groups:
            log.warning("No style groups created")
            return
        
        # Create monthly PDF
        pdf_path = create_monthly_pdf(style_groups)
        
        # Create summary
        create_monthly_summary(style_groups)
        
        log.info("=== Monthly Curator Complete ===")
        log.info(f"✅ Created monthly PDF: {pdf_path}")
        log.info(f"📊 Organized {sum(len(images) for images in style_groups.values())} images into {len(style_groups)} styles")
        
    except Exception as e:
        log.error(f"❌ Monthly curator failed: {e}")
        raise e

if __name__ == "__main__":
    main() 