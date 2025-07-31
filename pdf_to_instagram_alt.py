#!/usr/bin/env python3
"""
PDF to Instagram Converter (Alternative)
Extract PDF pages as PNG images optimized for Instagram posting
Uses PyMuPDF instead of pdf2image to avoid Poppler dependency
"""

import os
import sys
from pathlib import Path
import fitz  # PyMuPDF
from PIL import Image
import argparse
import logging
import io

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
log = logging.getLogger()

def get_latest_pdf():
    """Get the most recent PDF file from daily_pdfs directory"""
    pdf_dir = Path("daily_pdfs")
    if not pdf_dir.exists():
        log.error("❌ daily_pdfs directory not found")
        return None
    
    pdf_files = list(pdf_dir.glob("*.pdf"))
    if not pdf_files:
        log.error("❌ No PDF files found in daily_pdfs directory")
        return None
    
    # Get the most recent PDF
    latest_pdf = max(pdf_files, key=lambda x: x.stat().st_mtime)
    log.info(f"📄 Found latest PDF: {latest_pdf.name}")
    return latest_pdf

def convert_pdf_to_instagram_images(pdf_path, output_dir="instagram_images", dpi=300):
    """Convert PDF pages to Instagram-optimized PNG images"""
    
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    log.info(f"🔄 Converting PDF to Instagram images...")
    log.info(f"📁 Output directory: {output_path}")
    
    try:
        # Open PDF with PyMuPDF
        doc = fitz.open(pdf_path)
        
        # Instagram dimensions (square format)
        instagram_size = (1080, 1080)  # Instagram square post
        
        converted_images = []
        
        for page_num in range(len(doc)):
            log.info(f"📄 Processing page {page_num+1}/{len(doc)}")
            
            # Get page
            page = doc.load_page(page_num)
            
            # Calculate zoom factor for desired DPI
            zoom = dpi / 72  # PyMuPDF uses 72 DPI as base
            mat = fitz.Matrix(zoom, zoom)
            
            # Render page to image
            pix = page.get_pixmap(matrix=mat)
            
            # Convert to PIL Image
            img_data = pix.tobytes("png")
            image = Image.open(io.BytesIO(img_data))
            
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Resize to Instagram dimensions while maintaining aspect ratio
            # Calculate scaling to fit within Instagram square
            img_width, img_height = image.size
            scale = min(instagram_size[0] / img_width, instagram_size[1] / img_height)
            
            new_width = int(img_width * scale)
            new_height = int(img_height * scale)
            
            # Resize image
            resized_image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Create square canvas with white background
            square_image = Image.new('RGB', instagram_size, 'white')
            
            # Center the resized image on the square canvas
            x_offset = (instagram_size[0] - new_width) // 2
            y_offset = (instagram_size[1] - new_height) // 2
            square_image.paste(resized_image, (x_offset, y_offset))
            
            # Save as PNG
            output_filename = f"instagram_page_{page_num+1:02d}.png"
            output_file = output_path / output_filename
            square_image.save(output_file, 'PNG', quality=95)
            
            converted_images.append(output_file)
            log.info(f"✅ Saved: {output_filename} ({square_image.size[0]}x{square_image.size[1]})")
        
        doc.close()
        log.info(f"🎉 Successfully converted {len(converted_images)} pages to Instagram format")
        return converted_images
        
    except Exception as e:
        log.error(f"❌ Error converting PDF: {e}")
        return None

def create_instagram_story_images(pdf_path, output_dir="instagram_stories", dpi=300):
    """Convert PDF pages to Instagram Story format (9:16 aspect ratio)"""
    
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    log.info(f"🔄 Converting PDF to Instagram Story images...")
    log.info(f"📁 Output directory: {output_path}")
    
    try:
        # Open PDF with PyMuPDF
        doc = fitz.open(pdf_path)
        
        # Instagram Story dimensions (9:16 aspect ratio)
        story_size = (1080, 1920)  # Instagram story format
        
        converted_images = []
        
        for page_num in range(len(doc)):
            log.info(f"📄 Processing page {page_num+1}/{len(doc)} for story format")
            
            # Get page
            page = doc.load_page(page_num)
            
            # Calculate zoom factor for desired DPI
            zoom = dpi / 72  # PyMuPDF uses 72 DPI as base
            mat = fitz.Matrix(zoom, zoom)
            
            # Render page to image
            pix = page.get_pixmap(matrix=mat)
            
            # Convert to PIL Image
            img_data = pix.tobytes("png")
            image = Image.open(io.BytesIO(img_data))
            
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Resize to Instagram Story dimensions while maintaining aspect ratio
            img_width, img_height = image.size
            scale = min(story_size[0] / img_width, story_size[1] / img_height)
            
            new_width = int(img_width * scale)
            new_height = int(img_height * scale)
            
            # Resize image
            resized_image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Create story canvas with white background
            story_image = Image.new('RGB', story_size, 'white')
            
            # Center the resized image on the story canvas
            x_offset = (story_size[0] - new_width) // 2
            y_offset = (story_size[1] - new_height) // 2
            story_image.paste(resized_image, (x_offset, y_offset))
            
            # Save as PNG
            output_filename = f"instagram_story_{page_num+1:02d}.png"
            output_file = output_path / output_filename
            story_image.save(output_file, 'PNG', quality=95)
            
            converted_images.append(output_file)
            log.info(f"✅ Saved: {output_filename} ({story_image.size[0]}x{story_image.size[1]})")
        
        doc.close()
        log.info(f"🎉 Successfully converted {len(converted_images)} pages to Instagram Story format")
        return converted_images
        
    except Exception as e:
        log.error(f"❌ Error converting PDF: {e}")
        return None

def main():
    parser = argparse.ArgumentParser(description="Convert PDF to Instagram-optimized images")
    parser.add_argument('--pdf', type=str, help='Path to specific PDF file (optional)')
    parser.add_argument('--output', type=str, default='instagram_images', help='Output directory')
    parser.add_argument('--dpi', type=int, default=300, help='DPI for conversion')
    parser.add_argument('--story', action='store_true', help='Create Instagram Story format (9:16) instead of square posts')
    parser.add_argument('--both', action='store_true', help='Create both square posts and story format')
    
    args = parser.parse_args()
    
    # Get PDF file
    if args.pdf:
        pdf_path = Path(args.pdf)
        if not pdf_path.exists():
            log.error(f"❌ PDF file not found: {args.pdf}")
            return
    else:
        pdf_path = get_latest_pdf()
        if not pdf_path:
            return
    
    log.info(f"📄 Processing PDF: {pdf_path.name}")
    
    # Convert based on options
    if args.story:
        # Create Instagram Story format
        create_instagram_story_images(pdf_path, "instagram_stories", args.dpi)
    elif args.both:
        # Create both formats
        log.info("🔄 Creating both square posts and story format...")
        create_instagram_story_images(pdf_path, "instagram_stories", args.dpi)
        convert_pdf_to_instagram_images(pdf_path, "instagram_images", args.dpi)
    else:
        # Create square posts (default)
        convert_pdf_to_instagram_images(pdf_path, args.output, args.dpi)
    
    log.info("🎉 Conversion complete!")

if __name__ == "__main__":
    main() 