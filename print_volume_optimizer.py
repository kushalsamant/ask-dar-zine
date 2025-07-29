#!/usr/bin/env python3
"""
Print Volume Optimizer
Creates university-friendly, print-ready volumes instead of bulky PDFs.
"""

import os
import sys
import logging
import time
from datetime import datetime, timedelta
from pathlib import Path
import random
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, PageBreak, Spacer, Paragraph
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)

def get_env(var, default=None):
    return os.getenv(var, default)

class PrintVolumeOptimizer:
    def __init__(self):
        self.volume_configs = {
            'weekly': {
                'max_pages': 32,  # 8 sheets of paper (16 pages each side)
                'max_images': 8,   # 1 image per spread (2 pages) - smaller volumes
                'title_template': 'ASK Weekly Volume {week_number}',
                'subtitle': 'AI Architecture Research Collection'
            },
            'monthly': {
                'max_pages': 64,  # 16 sheets of paper (32 pages each side)
                'max_images': 16,  # 1 image per spread (2 pages) - smaller volumes
                'title_template': 'ASK Monthly Volume {month_name} {year}',
                'subtitle': 'Comprehensive AI Architecture Archive'
            },
            'quarterly': {
                'max_pages': 96,  # 24 sheets of paper (48 pages each side)
                'max_images': 24,  # 1 image per spread (2 pages) - smaller volumes
                'title_template': 'ASK Quarterly Volume Q{quarter} {year}',
                'subtitle': 'AI Architecture Research Quarterly'
            }
        }
    
    def calculate_optimal_volumes(self, total_images, volume_type='weekly'):
        """Calculate optimal volume distribution"""
        config = self.volume_configs[volume_type]
        max_images_per_volume = config['max_images']
        
        num_volumes = (total_images + max_images_per_volume - 1) // max_images_per_volume
        images_per_volume = total_images // num_volumes
        remainder = total_images % num_volumes
        
        volumes = []
        image_index = 0
        
        for i in range(num_volumes):
            # Distribute remainder evenly
            volume_images = images_per_volume + (1 if i < remainder else 0)
            volumes.append({
                'volume_number': i + 1,
                'image_count': volume_images,
                'page_count': volume_images * 2,  # 2 pages per image
                'start_index': image_index,
                'end_index': image_index + volume_images - 1
            })
            image_index += volume_images
        
        return volumes
    
    def select_images_for_volume(self, all_images, volume_config):
        """Select best images for a specific volume"""
        # Sort by quality score (you can implement your own scoring)
        scored_images = []
        for img in all_images:
            score = self.calculate_image_score(img)
            scored_images.append((score, img))
        
        # Sort by score (highest first)
        scored_images.sort(reverse=True)
        
        # Select top images for this volume
        selected = [img for score, img in scored_images[:volume_config['max_images']]]
        
        # Ensure style diversity
        selected = self.ensure_style_diversity(selected, volume_config['max_images'])
        
        return selected
    
    def calculate_image_score(self, image_info):
        """Calculate quality score for an image"""
        score = 0
        
        # Recency bonus (newer images get higher scores)
        days_old = (datetime.now() - image_info['date']).days
        recency_score = max(0, 30 - days_old)  # 30 points for today, 0 for 30+ days
        score += recency_score
        
        # Style diversity bonus
        style_bonus = 10  # Base bonus for each style
        score += style_bonus
        
        # Random factor for variety
        score += random.randint(0, 20)
        
        return score
    
    def ensure_style_diversity(self, selected_images, max_images):
        """Ensure diverse representation of styles"""
        if len(selected_images) <= max_images:
            return selected_images
        
        # Group by style
        style_groups = {}
        for img in selected_images:
            style = img['style']
            if style not in style_groups:
                style_groups[style] = []
            style_groups[style].append(img)
        
        # Calculate fair distribution
        num_styles = len(style_groups)
        max_per_style = max_images // num_styles
        remainder = max_images % num_styles
        
        final_selection = []
        
        # Add images from each style
        for i, (style, images) in enumerate(style_groups.items()):
            # Add extra images to first few styles if there's remainder
            allowed_count = max_per_style + (1 if i < remainder else 0)
            final_selection.extend(images[:allowed_count])
        
        return final_selection[:max_images]
    
    def create_volume_pdf(self, images, volume_info, volume_type):
        """Create a print-optimized volume PDF"""
        config = self.volume_configs[volume_type]
        
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"ASK_{volume_type}_volume_{volume_info['volume_number']}_{timestamp}.pdf"
        output_path = os.path.join("print_volumes", filename)
        
        # Create output directory
        os.makedirs("print_volumes", exist_ok=True)
        
        # Create PDF
        doc = SimpleDocTemplate(output_path, pagesize=A4)
        story = []
        
        # Title page
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=getSampleStyleSheet()['Title'],
            fontSize=24,
            spaceAfter=30,
            alignment=TA_CENTER
        )
        
        subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=getSampleStyleSheet()['Normal'],
            fontSize=14,
            spaceAfter=20,
            alignment=TA_CENTER
        )
        
        # Generate title
        if volume_type == 'weekly':
            week_number = datetime.now().isocalendar()[1]
            title = config['title_template'].format(week_number=week_number)
        elif volume_type == 'monthly':
            month_name = datetime.now().strftime("%B")
            year = datetime.now().year
            title = config['title_template'].format(month_name=month_name, year=year)
        elif volume_type == 'quarterly':
            quarter = (datetime.now().month - 1) // 3 + 1
            year = datetime.now().year
            title = config['title_template'].format(quarter=quarter, year=year)
        
        story.append(Paragraph(title, title_style))
        story.append(Paragraph(config['subtitle'], subtitle_style))
        story.append(Spacer(1, 50))
        
        # Volume info
        info_text = f"""
        Volume {volume_info['volume_number']} | {volume_info['image_count']} Images | {volume_info['page_count']} Pages
        Generated: {datetime.now().strftime('%B %d, %Y')}
        """
        story.append(Paragraph(info_text, getSampleStyleSheet()['Normal']))
        story.append(PageBreak())
        
        # Add images (placeholder for now)
        for i, image_info in enumerate(images, 1):
            story.append(Paragraph(f"Image {i}: {image_info['filename']}", getSampleStyleSheet()['Normal']))
            story.append(Paragraph(f"Style: {image_info['style']}", getSampleStyleSheet()['Normal']))
            story.append(Spacer(1, 20))
        
        # Build PDF
        doc.build(story)
        
        log.info(f"✅ Created {volume_type} volume {volume_info['volume_number']}: {filename}")
        return output_path

def main():
    """Main function to demonstrate volume optimization"""
    log.info("🚀 Starting Print Volume Optimization...")
    
    optimizer = PrintVolumeOptimizer()
    
    # Example scenarios
    scenarios = [
        ("Weekly (10 selected from 560)", 10, 'weekly'),
        ("Monthly (32 selected from 1680)", 32, 'monthly'),
        ("Quarterly (96 selected from 5040)", 96, 'quarterly')
    ]
    
    for scenario_name, total_images, volume_type in scenarios:
        log.info(f"\n📊 {scenario_name}:")
        log.info(f"   Total images: {total_images}")
        
        # Calculate optimal volumes
        volumes = optimizer.calculate_optimal_volumes(total_images, volume_type)
        
        log.info(f"📚 Volume Distribution:")
        for volume in volumes:
            log.info(f"   Volume {volume['volume_number']}: {volume['image_count']} images, {volume['page_count']} pages")
        
        total_pages = sum(v['page_count'] for v in volumes)
        log.info(f"📈 Total: {len(volumes)} volumes, {total_pages} pages")
        
        # Compare with old system
        old_pages = total_images * 2  # 2 pages per image
        page_reduction = ((old_pages - total_pages) / old_pages) * 100
        
        log.info(f"🎯 Optimization Results:")
        log.info(f"   Old system: {old_pages} pages (bulky)")
        log.info(f"   New system: {total_pages} pages (print-friendly)")
        log.info(f"   Reduction: {page_reduction:.1f}% smaller")
    
    log.info("\n✅ Print volume optimization complete!")

if __name__ == "__main__":
    main() 