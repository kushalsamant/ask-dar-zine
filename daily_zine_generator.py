#!/usr/bin/env python3
"""
Daily Zine Generator - Streamlined Flow
1. Scrape web for architectural content
2. Use web content to make 1 theme daily
3. Use theme to create 50 prompts
4. Use prompts to make 50 full-bleed images in ONE style only
5. Use prompts to make captions (6 lines, 6 words each)
6. Place captions with readability improvements
7. Stitch into ONE PDF
"""

import os
import sys
import subprocess
import logging
import time
import random
import json
import requests
import base64
from datetime import datetime
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

# === 🔧 Setup real-time logging ===
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)
log_filename = os.path.join(LOG_DIR, f"daily_zine_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
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
REQUIRED_LIBS = ['python-dotenv', 'reportlab', 'Pillow', 'beautifulsoup4']

def install_missing_libs():
    missing_libs = []
    for lib in REQUIRED_LIBS:
        try:
            if lib == 'python-dotenv':
                __import__('dotenv')
            elif lib == 'Pillow':
                __import__('PIL')
            elif lib == 'beautifulsoup4':
                __import__('bs4')
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
import concurrent.futures

# === 📥 Load environment variables ===
load_dotenv('ask.env')

def get_env(var, default=None, required=False):
    value = os.getenv(var, default)
    if required and not value:
        log.error(f"Required environment variable '{var}' is missing. Exiting.")
        sys.exit(1)
    return value

# === 📊 Configuration ===
TEXT_PROVIDER = get_env('TEXT_PROVIDER', 'groq')
TEXT_MODEL = get_env('TEXT_MODEL', 'llama3-8b-8192')
GROQ_API_KEY = get_env('GROQ_API_KEY', required=True)
GROQ_API_BASE = get_env('GROQ_API_BASE', 'https://api.groq.com/openai/v1')
TOGETHER_API_KEY = get_env('TOGETHER_API_KEY', required=True)
TOGETHER_API_BASE = get_env('TOGETHER_API_BASE', 'https://api.together.xyz/v1')

IMAGE_PROVIDER = get_env('IMAGE_PROVIDER', 'together')
IMAGE_MODEL = get_env('IMAGE_MODEL', 'black-forest-labs/flux-1-schnell')
IMAGE_WIDTH = int(get_env('IMAGE_WIDTH', '1024'))
IMAGE_HEIGHT = int(get_env('IMAGE_HEIGHT', '1024'))
INFERENCE_STEPS = int(get_env('INFERENCE_STEPS', '10'))
GUIDANCE_SCALE = float(get_env('GUIDANCE_SCALE', '7.5'))

PROMPT_SYSTEM = get_env('PROMPT_SYSTEM', 'You are a visionary architectural writer and provocateur. You create compelling, artistic image prompts that capture the essence of architectural concepts with vivid, poetic language.')
PROMPT_TEMPLATE = get_env('PROMPT_TEMPLATE', 'Generate exactly {n} architectural image prompts on theme: \'{theme}\'. Each prompt should be a single, evocative line that describes a visual scene with artistic flair. Focus on mood, atmosphere, and architectural poetry. Do not include explanations or numbered lists - just the prompts, one per line.')

CAPTION_SYSTEM = get_env('CAPTION_SYSTEM', 'You are a masterful architectural poet and critic. You write profound, artistic captions that capture the deeper meaning and emotional resonance of architectural spaces.')
CAPTION_TEMPLATE = get_env('CAPTION_TEMPLATE', 'Write exactly 6 lines, each containing exactly 6 words, that form a complete, meaningful caption for this architectural image: {prompt}. Each line should be a complete thought with poetic depth. The entire caption should tell a coherent story that reveals the architectural philosophy, emotional impact, and cultural significance of the space.')

# Style configuration for the selected style
STYLE_CONFIG = {
    'futuristic': {
        'model': 'black-forest-labs/flux-1-schnell',
        'prompt_suffix': ', futuristic architecture, sci-fi aesthetic, glowing lights, sleek surfaces, advanced technology, architectural innovation',
        'negative_prompt': 'traditional, classical, rustic, old, vintage, historical, medieval, gothic'
    }
}

# === 🎨 Style Selection ===
STYLES = ['futuristic', 'minimalist', 'sketch', 'abstract', 'technical', 'watercolor', 'anime', 'photorealistic']

def get_daily_style():
    """Get the style for today based on date"""
    today = datetime.now()
    day_of_year = today.timetuple().tm_yday
    style_index = day_of_year % len(STYLES)
    selected_style = STYLES[style_index]
    time.sleep(1)  # Rate limiting
    return selected_style

# === 🌐 Web Scraping ===
def scrape_architectural_content():
    """Scrape architectural content for theme generation"""
    try:
        from web_scraper import WebScraper
        scraper = WebScraper()
        articles = scraper.scrape_all_sources()
        
        if articles:
            # Extract themes from article titles
            themes = []
            for article in articles[:20]:  # Use top 20 articles
                title = article.get('title', '')
                if len(title) > 10:
                    themes.append(title)
            
            if themes:
                selected_theme = random.choice(themes)
                log.info(f"🎯 Selected theme from web scraping: {selected_theme}")
                time.sleep(1)  # Rate limiting
                return selected_theme
        
        # Fallback theme
        fallback_theme = get_env('FALLBACK_THEME', 'Modern Architecture')
        log.info(f"🎯 Using fallback theme: {fallback_theme}")
        time.sleep(1)  # Rate limiting
        return fallback_theme
        
    except Exception as e:
        log.error(f"❌ Web scraping failed: {e}")
        fallback_theme = get_env('FALLBACK_THEME', 'Modern Architecture')
        log.info(f"🎯 Using fallback theme: {fallback_theme}")
        time.sleep(1)  # Rate limiting
        return fallback_theme

# === 🤖 LLM Integration ===
def call_llm(prompt, system_prompt=None):
    """Call LLM API based on provider"""
    if TEXT_PROVIDER == 'groq':
        url = f"{GROQ_API_BASE}/chat/completions"
        api_key = GROQ_API_KEY
    else:
        url = f"{TOGETHER_API_BASE}/chat/completions"
        api_key = TOGETHER_API_KEY
    
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})
    
    payload = {
        "model": TEXT_MODEL,
        "messages": messages,
        "max_tokens": 2000,
        "temperature": 0.8
    }
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        data = response.json()
        result = data['choices'][0]['message']['content'].strip()
        time.sleep(1)  # Rate limiting
        return result
    except Exception as e:
        log.error(f"❌ LLM call failed: {e}")
        return None

def generate_prompts(theme, num_prompts=50):
    """Generate 50 architectural image prompts"""
    log.info(f"🎨 Generating {num_prompts} prompts for theme: {theme}")
    
    prompt = PROMPT_TEMPLATE.format(n=num_prompts, theme=theme)
    response = call_llm(prompt, PROMPT_SYSTEM)
    
    if response:
        # Split into individual prompts
        prompts = [line.strip() for line in response.split('\n') if line.strip()]
        log.info(f"✅ Generated {len(prompts)} prompts")
        time.sleep(1)  # Rate limiting
        return prompts[:num_prompts]  # Ensure we get exactly 50
    else:
        log.error("❌ Failed to generate prompts")
        return []

def generate_caption(prompt):
    """Generate a 6-line caption for an image prompt"""
    caption_prompt = CAPTION_TEMPLATE.format(prompt=prompt)
    response = call_llm(caption_prompt, CAPTION_SYSTEM)
    
    if response:
        # Ensure exactly 6 lines
        lines = [line.strip() for line in response.split('\n') if line.strip()]
        if len(lines) >= 6:
            result = '\n'.join(lines[:6])
            time.sleep(1)  # Rate limiting
            return result
        else:
            # Pad with generic lines if needed
            while len(lines) < 6:
                lines.append("Architecture speaks through silent spaces")
            result = '\n'.join(lines[:6])
            time.sleep(1)  # Rate limiting
            return result
    else:
        # Fallback caption
        return "Architecture speaks through silent spaces\nForm follows function in perfect harmony\nLight dances across geometric surfaces\nHuman scale meets monumental vision\nMaterials tell stories of creation\nSpace becomes poetry in motion"

# === 🖼️ Image Generation ===
def generate_single_image(prompt, style_name, image_number):
    """Generate a single image using Together.ai API"""
    log.info(f"🎨 Generating {style_name} image {image_number}")
    
    style_dir = os.path.join("images", style_name)
    os.makedirs(style_dir, exist_ok=True)
    
    # Get style configuration
    style_config = STYLE_CONFIG.get(style_name, {
        'model': IMAGE_MODEL,
        'prompt_suffix': f', {style_name} style, architectural beauty',
        'negative_prompt': 'blurry, low quality, distorted'
    })
    
    full_prompt = f"{prompt}{style_config['prompt_suffix']}"
    negative_prompt = style_config['negative_prompt']
    
    together_api_url = "https://api.together.xyz/v1/images/generations"
    
    payload = {
        "model": style_config['model'],
        "prompt": full_prompt,
        "negative_prompt": negative_prompt,
        "width": IMAGE_WIDTH,
        "height": IMAGE_HEIGHT,
        "steps": INFERENCE_STEPS,
        "guidance_scale": GUIDANCE_SCALE,
        "seed": random.randint(1, 1000000)
    }
    
    headers = {
        "Authorization": f"Bearer {TOGETHER_API_KEY}",
        "Content-Type": "application/json"
    }
    
    for attempt in range(3):
        try:
            log.info(f"🔄 Attempt {attempt + 1}/3 for {style_name} image {image_number}")
            
            response = requests.post(
                together_api_url,
                headers=headers,
                json=payload,
                timeout=120
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'data' in data and len(data['data']) > 0:
                    image_data = data['data'][0]
                    if 'url' in image_data:
                        image_url = image_data['url']
                        image_response = requests.get(image_url, timeout=60)
                        if image_response.status_code == 200:
                            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                            image_filename = f"{style_name}_image_{image_number:02d}_{timestamp}.jpg"
                            image_path = os.path.join(style_dir, image_filename)
                            
                            with open(image_path, 'wb') as f:
                                f.write(image_response.content)
                            
                            log.info(f"✅ Generated {style_name} image {image_number}: {image_filename}")
                            time.sleep(1)  # Rate limiting
                            return image_path
                        else:
                            log.error(f"❌ Failed to download image from {image_url}")
                    else:
                        log.error(f"❌ No image URL in response for {style_name} image {image_number}")
                else:
                    log.error(f"❌ Invalid response format for {style_name} image {image_number}")
            elif response.status_code == 429:
                log.warning(f"⚠️ Rate limited (attempt {attempt + 1}), waiting 60s...")
                time.sleep(60)
                continue
            else:
                log.error(f"❌ API error {response.status_code}: {response.text}")
                
        except Exception as e:
            log.error(f"❌ Image generation failed (attempt {attempt + 1}): {e}")
            if attempt < 2:
                time.sleep(5)
                continue
    
    log.error(f"❌ All attempts failed for {style_name} image {image_number}")
    return None

def generate_all_images(prompts, style_name):
    """Generate all 50 images using ThreadPoolExecutor"""
    log.info(f"🎨 Starting generation of {len(prompts)} images for {style_name} style")
    
    images = []
    with ThreadPoolExecutor(max_workers=4) as executor:
        future_to_prompt = {
            executor.submit(generate_single_image, prompt, style_name, i+1): i 
            for i, prompt in enumerate(prompts)
        }
        
        for future in as_completed(future_to_prompt):
            image_index = future_to_prompt[future]
            try:
                image_path = future.result()
                if image_path:
                    images.append((image_index, image_path))
                    log.info(f"✅ Image {image_index+1}/{len(prompts)} completed")
                else:
                    log.error(f"❌ Image {image_index+1} failed")
            except Exception as e:
                log.error(f"❌ Image {image_index+1} failed: {e}")
    
    # Sort by index to maintain order
    images.sort(key=lambda x: x[0])
    return [img[1] for img in images]

# === 📝 Caption Generation ===
def generate_all_captions(prompts):
    """Generate captions for all prompts"""
    log.info(f"📝 Generating captions for {len(prompts)} prompts")
    
    captions = []
    for i, prompt in enumerate(prompts):
        caption = generate_caption(prompt)
        captions.append(caption)
        log.info(f"✅ Caption {i+1}/{len(prompts)} generated")
        time.sleep(1)  # Rate limiting between captions
    
    return captions

# === 📄 PDF Generation ===
def place_caption_with_white_band(c, caption, w, h, page_num):
    """
    Draw a 100% white band at the bottom of the page, overlay the caption (left) and page number (right).
    The band is flush with the bottom of the page.
    """
    text = caption.split('\n')
    font_size = 14
    line_spacing = 18
    padding_x = 24
    padding_y = 16

    # Calculate text dimensions
    c.setFont("Helvetica-Bold", font_size)
    text_width = max(c.stringWidth(line, "Helvetica-Bold", font_size) for line in text)
    text_height = len(text) * line_spacing

    band_height = text_height + 2 * padding_y
    band_y = 0  # flush with the bottom of the page
    band_x = 0
    band_width = w

    # Draw white band
    c.setFillColorRGB(1, 1, 1)
    c.rect(band_x, band_y, band_width, band_height, fill=1, stroke=0)

    # Draw caption (left-aligned, vertically centered in band)
    c.setFont("Helvetica-Bold", font_size)
    c.setFillColorRGB(0, 0, 0)
    for i, line in enumerate(text):
        y = band_y + band_height - padding_y - (len(text) - i - 1) * line_spacing
        c.drawString(band_x + padding_x, y, line)

    # Draw page number (right-aligned, at the bottom of the white band)
    page_str = str(page_num)
    c.setFont("Helvetica", font_size)
    c.drawRightString(band_x + band_width - padding_x, band_y + padding_y, page_str)

def create_daily_pdf(images, captions, style_name, theme):
    """Create the daily PDF with all images and captions"""
    if not images:
        log.error("❌ No images provided for PDF creation")
        return None
    
    # Create output directory
    output_dir = "daily_pdfs"
    os.makedirs(output_dir, exist_ok=True)
    
    # Create PDF filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    pdf_filename = f"ASK_Daily_{style_name.upper()}_{timestamp}.pdf"
    pdf_path = os.path.join(output_dir, pdf_filename)
    
    log.info(f"📄 Creating PDF: {pdf_filename}")
    log.info(f"📊 Images to include: {len(images)}")
    
    # Create PDF
    c = canvas.Canvas(pdf_path, pagesize=A4)
    w, h = A4
    
    page_count = 0
    
    # Add title page
    c.setFont("Helvetica-Bold", 36)
    c.setFillColorRGB(0, 0, 0)
    c.drawCentredString(w/2, h/2 + 100, "ASK")
    c.setFont("Helvetica-Bold", 24)
    c.drawCentredString(w/2, h/2 + 50, f"DAILY {style_name.upper()}")
    c.setFont("Helvetica", 16)
    c.drawCentredString(w/2, h/2, f"{datetime.now().strftime('%B %d, %Y')}")
    c.setFont("Helvetica", 14)
    c.drawCentredString(w/2, h/2 - 50, f"50 Full-Bleed Images")
    c.setFont("Helvetica", 12)
    c.drawCentredString(w/2, h/2 - 100, f"Theme: {theme}")
    c.setFont("Helvetica", 10)
    c.drawCentredString(w/2, h/2 - 150, "Architectural Poetry in Motion")
    c.showPage()
    page_count += 1
    
    # Add images with captions
    for i, (image_path, caption) in enumerate(zip(images, captions)):
        try:
            # Add image to PDF (full bleed)
            c.drawImage(image_path, -20, -20, width=w+40, height=h+40)
            
            # Add caption with white band and page number
            place_caption_with_white_band(c, caption, w, h, i + 1)
            
            c.showPage()
            page_count += 1
            
            if (i + 1) % 10 == 0:
                log.info(f"✅ Added {i+1}/{len(images)} images to PDF")
            
        except Exception as e:
            log.error(f"❌ Error adding image {i+1}: {e}")
            continue
    
    c.save()
    
    log.info(f"🎉 Daily PDF created successfully!")
    log.info(f"📁 File: {pdf_path}")
    log.info(f"📄 Pages: {page_count}")
    log.info(f"📏 Size: {os.path.getsize(pdf_path)} bytes")
    
    return pdf_path

# === 🚀 Main Function ===
def main():
    """Main function to run the daily zine generation"""
    log.info("🚀 Starting Daily Zine Generator")
    
    # Step 1: Scrape web for architectural content
    log.info("📡 Step 1: Scraping web for architectural content")
    theme = scrape_architectural_content()
    time.sleep(1)  # Rate limiting
    
    # Step 2: Select daily style
    log.info("🎨 Step 2: Selecting daily style")
    style_name = get_daily_style()
    log.info(f"🎯 Selected style: {style_name.upper()}")
    time.sleep(1)  # Rate limiting
    
    # Step 3: Generate 50 prompts
    log.info("✍️ Step 3: Generating 50 prompts")
    prompts = generate_prompts(theme, 50)
    if not prompts:
        log.error("❌ Failed to generate prompts")
        return
    time.sleep(1)  # Rate limiting
    
    # Step 4: Generate 50 images in one style
    log.info("🖼️ Step 4: Generating 50 images")
    images = generate_all_images(prompts, style_name)
    if not images:
        log.error("❌ Failed to generate images")
        return
    time.sleep(1)  # Rate limiting
    
    # Step 5: Generate captions
    log.info("📝 Step 5: Generating captions")
    captions = generate_all_captions(prompts)
    time.sleep(1)  # Rate limiting
    
    # Step 6 & 7: Create PDF
    log.info("📄 Step 6 & 7: Creating PDF")
    pdf_path = create_daily_pdf(images, captions, style_name, theme)
    
    if pdf_path:
        log.info(f"🎉 Daily zine generation complete!")
        log.info(f"📁 PDF: {pdf_path}")
        log.info(f"🎨 Style: {style_name.upper()}")
        log.info(f"📊 Images: {len(images)}")
        log.info(f"📝 Captions: {len(captions)}")
        log.info(f"🎯 Theme: {theme}")
    else:
        log.error("❌ Failed to create daily PDF")

if __name__ == "__main__":
    main() 