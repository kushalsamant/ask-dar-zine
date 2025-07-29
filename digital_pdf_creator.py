#!/usr/bin/env python3
"""
Digital PDF Creator
Creates PDFs optimized for digital sales and distribution.
"""

import os
import sys
import logging
import time
from datetime import datetime
from pathlib import Path
import json
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, PageBreak, Spacer, Paragraph
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)

def get_env(var, default=None):
    return os.getenv(var, default)

class DigitalPDFCreator:
    def __init__(self):
        self.pdf_configs = {
            'weekly': {
                'max_images': 10,  # 10 best images from the week
                'price': 2.99,
                'title_template': 'ASK Weekly Collection - Week {week_number}',
                'subtitle': 'AI Architecture Research'
            },
            'monthly': {
                'max_images': 32,  # 32 best images from the month
                'price': 7.99,
                'title_template': 'ASK Monthly Collection - {month_name} {year}',
                'subtitle': 'Comprehensive AI Architecture Archive'
            },
            'quarterly': {
                'max_images': 96,  # 96 best images from the quarter
                'price': 19.99,
                'title_template': 'ASK Quarterly Collection - Q{quarter} {year}',
                'subtitle': 'AI Architecture Research Quarterly'
            },
            'yearly': {
                'max_images': 365,  # 365 best images from the year
                'price': 49.99,
                'title_template': 'ASK Yearly Collection - {year}',
                'subtitle': 'Complete AI Architecture Research Year'
            }
        }
    
    def create_weekly_pdf(self, selected_images, captions):
        """Create weekly PDF for digital sales"""
        config = self.pdf_configs['weekly']
        
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        week_number = datetime.now().isocalendar()[1]
        filename = f"ASK_weekly_{week_number}_{timestamp}.pdf"
        output_path = os.path.join("digital_pdfs", filename)
        
        # Create output directory
        os.makedirs("digital_pdfs", exist_ok=True)
        
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
        
        title = config['title_template'].format(week_number=week_number)
        story.append(Paragraph(title, title_style))
        story.append(Paragraph(config['subtitle'], subtitle_style))
        story.append(Spacer(1, 50))
        
        # Volume info
        info_text = f"""
        {len(selected_images)} Images | Generated: {datetime.now().strftime('%B %d, %Y')}
        Digital Edition - Perfect for screens and tablets
        """
        story.append(Paragraph(info_text, getSampleStyleSheet()['Normal']))
        story.append(PageBreak())
        
        # Add images and captions
        for i, (image_info, caption) in enumerate(zip(selected_images, captions), 1):
            story.append(Paragraph(f"Image {i}: {image_info['filename']}", getSampleStyleSheet()['Normal']))
            story.append(Paragraph(f"Style: {image_info['style']}", getSampleStyleSheet()['Normal']))
            story.append(Paragraph(f"Caption: {caption}", getSampleStyleSheet()['Normal']))
            story.append(Spacer(1, 20))
        
        # Build PDF
        doc.build(story)
        
        log.info(f"✅ Created weekly PDF: {filename}")
        return output_path
    
    def create_monthly_pdf(self, selected_images, captions):
        """Create monthly PDF for digital sales"""
        config = self.pdf_configs['monthly']
        
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        month_name = datetime.now().strftime("%B")
        year = datetime.now().year
        filename = f"ASK_monthly_{month_name}_{year}_{timestamp}.pdf"
        output_path = os.path.join("digital_pdfs", filename)
        
        # Create output directory
        os.makedirs("digital_pdfs", exist_ok=True)
        
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
        
        title = config['title_template'].format(month_name=month_name, year=year)
        story.append(Paragraph(title, title_style))
        story.append(Paragraph(config['subtitle'], subtitle_style))
        story.append(Spacer(1, 50))
        
        # Volume info
        info_text = f"""
        {len(selected_images)} Images | Generated: {datetime.now().strftime('%B %d, %Y')}
        Digital Edition - Perfect for screens and tablets
        """
        story.append(Paragraph(info_text, getSampleStyleSheet()['Normal']))
        story.append(PageBreak())
        
        # Add images and captions
        for i, (image_info, caption) in enumerate(zip(selected_images, captions), 1):
            story.append(Paragraph(f"Image {i}: {image_info['filename']}", getSampleStyleSheet()['Normal']))
            story.append(Paragraph(f"Style: {image_info['style']}", getSampleStyleSheet()['Normal']))
            story.append(Paragraph(f"Caption: {caption}", getSampleStyleSheet()['Normal']))
            story.append(Spacer(1, 20))
        
        # Build PDF
        doc.build(story)
        
        log.info(f"✅ Created monthly PDF: {filename}")
        return output_path

    def create_yearly_pdf(self, selected_images, captions):
        """Create yearly PDF for digital sales"""
        config = self.pdf_configs['yearly']
        
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        year = datetime.now().year
        filename = f"ASK_yearly_{year}_{timestamp}.pdf"
        output_path = os.path.join("digital_pdfs", filename)
        
        # Create output directory
        os.makedirs("digital_pdfs", exist_ok=True)
        
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
        
        title = config['title_template'].format(year=year)
        story.append(Paragraph(title, title_style))
        story.append(Paragraph(config['subtitle'], subtitle_style))
        story.append(Spacer(1, 50))
        
        # Volume info
        info_text = f"""
        {len(selected_images)} Images | Generated: {datetime.now().strftime('%B %d, %Y')}
        Digital Edition - Perfect for screens and tablets
        """
        story.append(Paragraph(info_text, getSampleStyleSheet()['Normal']))
        story.append(PageBreak())
        
        # Add images and captions
        for i, (image_info, caption) in enumerate(zip(selected_images, captions), 1):
            story.append(Paragraph(f"Image {i}: {image_info['filename']}", getSampleStyleSheet()['Normal']))
            story.append(Paragraph(f"Style: {image_info['style']}", getSampleStyleSheet()['Normal']))
            story.append(Paragraph(f"Caption: {caption}", getSampleStyleSheet()['Normal']))
            story.append(Spacer(1, 20))
        
        # Build PDF
        doc.build(story)
        
        log.info(f"✅ Created yearly PDF: {filename}")
        return output_path

def main():
    """Main function to demonstrate digital PDF creation"""
    log.info("🚀 Starting Digital PDF Creation...")
    
    creator = DigitalPDFCreator()
    
    # Example usage
    log.info("📊 Digital PDF configurations:")
    for pdf_type, config in creator.pdf_configs.items():
        log.info(f"   {pdf_type.title()}: {config['max_images']} images, ${config['price']:.2f}")
    
    log.info("✅ Digital PDF creator ready!")

if __name__ == "__main__":
    main() 