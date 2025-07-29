#!/usr/bin/env python3
"""
Yearly Image Curator
Selects the best images from the entire year and creates a yearly PDF.
Runs on the last day of the year.
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
log_filename = os.path.join(LOG_DIR, f"yearly_curator_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
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
CAPTION_POSITION = get_env("CAPTION_POSITION", "bottom")
CAPTION_FONT_SIZE = int(get_env("CAPTION_FONT_SIZE", "14"))
CAPTION_LINE_SPACING = int(get_env("CAPTION_LINE_SPACING", "18"))

def get_year_range():
    """Get the date range for the current year"""
    current_year = datetime.now().year
    year_start = datetime(current_year, 1, 1)
    year_end = datetime(current_year, 12, 31)
    
    return year_start, year_end

def collect_yearly_images():
    """Collect images from the yearly pool using the allocator"""
    try:
        from image_allocator import load_allocation_state, get_images_for_period
        
        # Load allocation state
        state = load_allocation_state()
        
        # Get images from yearly pool (need 365 for yearly PDF)
        yearly_images = get_images_for_period('yearly', 365, state)
        
        # Save updated state
        from image_allocator import save_allocation_state
        save_allocation_state(state)
        
        log.info(f"Collected {len(yearly_images)} images from yearly pool")
        return yearly_images
        
    except ImportError:
        log.warning("Image allocator not available, falling back to old method")
        return collect_yearly_images_fallback()

def collect_yearly_images_fallback():
    """Fallback method: collect images from the current year"""
    year_start, year_end = get_year_range()
    log.info(f"Collecting images from {year_start.strftime('%Y-%m-%d')} to {year_end.strftime('%Y-%m-%d')}")
    
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
                        
                        # Check if image is from this year
                        if year_start <= image_date <= year_end:
                            all_images.append({
                                'path': image_file,
                                'style': style_dir.name,
                                'date': image_date,
                                'filename': image_file.name
                            })
                            log.info(f"Found yearly image: {image_file.name}")
                except Exception as e:
                    log.warning(f"Could not parse date from {image_file.name}: {e}")
    
    log.info(f"Collected {len(all_images)} images from this year")
    return all_images

def select_best_yearly_images(images, num_images=365):
    """Select the best images from the entire year"""
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
        
        # Limit each style to max 50 images for diversity
        if style_counts[style] < 50:
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
    for i, img in enumerate(selected[:10], 1):  # Show first 10
        log.info(f"  {i}. {img['style']} - {img['filename']}")
    if len(selected) > 10:
        log.info(f"  ... and {len(selected) - 10} more")
    
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
        
        fallback_caption = f"Yearly collection from {style} style, generated on {date_str}, part of our comprehensive AI architecture research"
        return fallback_caption
        
    except Exception as e:
        log.warning(f"Could not load caption for {image['filename']}: {e}")
        # Return a basic fallback caption
        style = image['style'].replace('_', ' ').title()
        return f"Yearly collection {style} architectural concept"

def generate_yearly_captions(selected_images):
    """Generate captions for the selected images"""
    captions = []
    
    for i, image in enumerate(selected_images, 1):
        # Load the original caption for this image
        original_caption = load_captions_for_image(image)
        captions.append(original_caption)
    
    return captions

def create_yearly_pdf(selected_images, captions):
    """Create yearly PDF for digital sales"""
    try:
        from digital_pdf_creator import DigitalPDFCreator
        
        creator = DigitalPDFCreator()
        pdf_path = creator.create_yearly_pdf(selected_images, captions)
        
        log.info(f"✅ Created yearly PDF: {pdf_path}")
        return pdf_path
        
    except ImportError:
        log.warning("Digital PDF creator not available, falling back to basic PDF")
        return create_yearly_pdf_fallback(selected_images, captions)

def create_yearly_pdf_fallback(selected_images, captions):
    """Fallback: Create basic yearly PDF"""
    year_start, year_end = get_year_range()
    
    # Generate filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"ASK_yearly_{year_start.year}_{timestamp}.pdf"
    output_path = os.path.join("digital_pdfs", filename)
    
    # Create output directory
    os.makedirs("digital_pdfs", exist_ok=True)
    
    # Create PDF
    c = canvas.Canvas(output_path, pagesize=A4)
    w, h = A4
    
    log.info(f"Creating yearly PDF: {output_path}")
    
    # Add title page
    c.setFont("Helvetica-Bold", 24)
    c.drawCentredString(w/2, h/2 + 50, "ASK Yearly Collection")
    c.setFont("Helvetica", 16)
    c.drawCentredString(w/2, h/2, f"{year_start.year}")
    c.setFont("Helvetica", 12)
    c.drawCentredString(w/2, h/2 - 30, f"Complete AI Architecture Research Year")
    c.drawCentredString(w/2, h/2 - 50, f"{len(selected_images)} images from {year_start.strftime('%B %d')} to {year_end.strftime('%B %d, %Y')}")
    c.showPage()
    
    # Add images
    for i, (image, caption) in enumerate(zip(selected_images, captions)):
        try:
            # Add image info
            c.setFont("Helvetica", 16)
            c.drawCentredString(w/2, h/2 + 30, f"Image {i+1}: {image['style']}")
            c.setFont("Helvetica", 12)
            c.drawCentredString(w/2, h/2, f"Generated: {image['date'].strftime('%Y-%m-%d')}")
            c.drawCentredString(w/2, h/2 - 30, f"Caption: {caption[:50]}...")
            c.showPage()
            
        except Exception as e:
            log.error(f"Failed to add image {image['filename']}: {e}")
    
    c.save()
    log.info(f"✅ Yearly PDF created: {output_path}")
    return output_path

def create_yearly_summary(selected_images):
    """Create a summary of the yearly selection"""
    year_start, year_end = get_year_range()
    
    summary_file = os.path.join("digital_pdfs", f"yearly_summary_{year_start.year}.txt")
    
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write("ASK Yearly Collection Summary\n")
        f.write("=" * 60 + "\n\n")
        f.write(f"Year: {year_start.year}\n")
        f.write(f"Period: {year_start.strftime('%Y-%m-%d')} to {year_end.strftime('%Y-%m-%d')}\n")
        f.write(f"Total images selected: {len(selected_images)}\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("Style Distribution:\n")
        f.write("-" * 40 + "\n")
        style_counts = {}
        for image in selected_images:
            style = image['style']
            style_counts[style] = style_counts.get(style, 0) + 1
        
        for style, count in style_counts.items():
            f.write(f"{style:20s}: {count:3d} images\n")
        
        f.write("\nMonthly Distribution:\n")
        f.write("-" * 40 + "\n")
        monthly_counts = {}
        for image in selected_images:
            month = image['date'].strftime("%B")
            monthly_counts[month] = monthly_counts.get(month, 0) + 1
        
        for month in ['January', 'February', 'March', 'April', 'May', 'June', 
                     'July', 'August', 'September', 'October', 'November', 'December']:
            if month in monthly_counts:
                f.write(f"{month:15s}: {monthly_counts[month]:3d} images\n")
    
    log.info(f"Yearly summary created: {summary_file}")

def main():
    log.info("=== Yearly Image Curator Started ===")
    
    try:
        # Collect all images from this year
        yearly_images = collect_yearly_images()
        
        if not yearly_images:
            log.warning("No images found from this year")
            return
        
        # Select the best 365 images
        selected_images = select_best_yearly_images(yearly_images, 365)
        
        if not selected_images:
            log.warning("No images selected")
            return
        
        # Generate captions
        captions = generate_yearly_captions(selected_images)
        
        # Create yearly PDF
        pdf_path = create_yearly_pdf(selected_images, captions)
        
        # Create summary
        create_yearly_summary(selected_images)
        
        log.info("=== Yearly Curator Complete ===")
        log.info(f"✅ Created yearly PDF: {pdf_path}")
        log.info(f"📊 Selected {len(selected_images)} images from {len(yearly_images)} candidates")
        
    except Exception as e:
        log.error(f"❌ Yearly curator failed: {e}")
        raise e

if __name__ == "__main__":
    main() 