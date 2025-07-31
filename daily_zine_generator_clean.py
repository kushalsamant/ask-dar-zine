#!/usr/bin/env python3
"""
Daily Zine Generator - Clean Version
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
import argparse
from datetime import datetime, timedelta
from pathlib import Path
import sqlite3
import feedparser
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import pickle
import gc

from dotenv import load_dotenv
load_dotenv('ask.env')

def get_env(var, default=None, required=False):
    value = os.getenv(var, default)
    if required and not value:
        print(f"Required environment variable '{var}' is missing. Exiting.")
        sys.exit(1)
    return value

# Setup logging
LOG_DIR = get_env('LOG_DIR', 'logs')
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

# Auto-install missing dependencies
REQUIRED_LIBS = ['python-dotenv', 'reportlab', 'Pillow', 'beautifulsoup4', 'tqdm']

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
            elif lib == 'tqdm':
                __import__('tqdm')
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

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from PIL import Image
from tqdm import tqdm

# Configuration
CACHE_DIR = Path(get_env('CACHE_DIR', 'cache'))
CACHE_DIR.mkdir(exist_ok=True)

def get_cache_path(key):
    hash_key = hashlib.md5(key.encode()).hexdigest()
    return CACHE_DIR / f"{hash_key}.pkl"

def save_to_cache(key, data):
    if not CACHE_ENABLED:
        return
    try:
        cache_path = get_cache_path(key)
        with open(cache_path, 'wb') as f:
            pickle.dump(data, f)
    except Exception as e:
        log.debug(f"Cache save failed: {e}")

def load_from_cache(key, max_age_hours=None):
    if not CACHE_ENABLED:
        return None
    if max_age_hours is None:
        max_age_hours = int(get_env('CACHE_MAX_AGE_HOURS', '24'))
    try:
        cache_path = get_cache_path(key)
        if cache_path.exists():
            if time.time() - cache_path.stat().st_mtime < max_age_hours * 3600:
                with open(cache_path, 'rb') as f:
                    return pickle.load(f)
    except Exception as e:
        log.debug(f"Cache load failed: {e}")
    return None

# API Configuration
TEXT_PROVIDER = get_env('TEXT_PROVIDER', 'together')
TEXT_MODEL = get_env('TEXT_MODEL', 'meta-llama/Llama-3.3-70B-Instruct-Turbo-Free')
TOGETHER_API_KEY = get_env('TOGETHER_API_KEY', required=True)
TOGETHER_API_BASE = get_env('TOGETHER_API_BASE', 'https://api.together.xyz/v1')

IMAGE_PROVIDER = get_env('IMAGE_PROVIDER', 'together')
IMAGE_MODEL = get_env('IMAGE_MODEL', 'black-forest-labs/FLUX.1-schnell-free')
IMAGE_WIDTH = int(get_env('IMAGE_WIDTH', '1024'))
IMAGE_HEIGHT = int(get_env('IMAGE_HEIGHT', '1024'))
INFERENCE_STEPS = int(get_env('INFERENCE_STEPS', '4'))
GUIDANCE_SCALE = float(get_env('GUIDANCE_SCALE', '7.5'))

# Performance settings
MAX_CONCURRENT_IMAGES = int(get_env('MAX_CONCURRENT_IMAGES', '1'))
MAX_CONCURRENT_CAPTIONS = int(get_env('MAX_CONCURRENT_CAPTIONS', '1'))
RATE_LIMIT_DELAY = float(get_env('RATE_LIMIT_DELAY', '20.0'))
SKIP_CAPTION_DEDUPLICATION = get_env('SKIP_CAPTION_DEDUPLICATION', 'true').lower() == 'true'
FAST_MODE = get_env('FAST_MODE', 'false').lower() == 'true'
SKIP_WEB_SCRAPING = get_env('SKIP_WEB_SCRAPING', 'false').lower() == 'true'
SKIP_THEME_GENERATION = get_env('SKIP_THEME_GENERATION', 'false').lower() == 'true'
SKIP_PROMPT_GENERATION = get_env('SKIP_PROMPT_GENERATION', 'false').lower() == 'true'
SKIP_PDF_CREATION = get_env('SKIP_PDF_CREATION', 'false').lower() == 'true'
CACHE_ENABLED = get_env('CACHE_ENABLED', 'true').lower() == 'true'
PRELOAD_STYLES = get_env('PRELOAD_STYLES', 'true').lower() == 'true'
BATCH_PROCESSING = get_env('BATCH_PROCESSING', 'false').lower() == 'true'
OPTIMIZE_MEMORY = get_env('OPTIMIZE_MEMORY', 'true').lower() == 'true'

# Prompts
PROMPT_SYSTEM = get_env('PROMPT_SYSTEM', 'You are a visionary architectural writer and provocateur with deep expertise in architectural history, theory, and contemporary practice. Your knowledge spans from ancient architectural traditions to cutting-edge computational design, encompassing structural engineering, material science, cultural anthropology, environmental sustainability, urban planning, landscape architecture, digital fabrication, philosophy of space, phenomenology, global architectural traditions, vernacular building, lighting design, acoustic design, thermal comfort, passive design strategies, accessibility, universal design principles, heritage conservation, adaptive reuse, parametric design, algorithmic architecture, biomimicry, nature-inspired design, social impact, community engagement, economic feasibility, construction methods, regulatory compliance, building codes, post-occupancy evaluation, user experience, and cross-cultural architectural exchange. You create compelling, artistic image prompts that capture the essence of architectural concepts with vivid, poetic language, considering multiple scales from urban context to material detail, balancing technical precision with artistic expression, and emphasizing the emotional and psychological impact of architectural spaces on human experience.')

PROMPT_TEMPLATE = get_env('PROMPT_TEMPLATE', 'Generate exactly {n} architectural image prompts on theme: \'{theme}\'. Each prompt should be a single, evocative line (50-100 words) that describes a visual scene with artistic flair, focusing on architectural poetry, mood, and atmosphere. Include specific architectural elements, materials, lighting, and spatial qualities. Consider cultural, historical, and philosophical context. Emphasize emotional resonance and visual impact. Use vivid, descriptive language that captures architectural essence. Balance technical precision with artistic expression. Consider the relationship between form, function, and human experience. Explore themes of permanence, transience, and transformation. Reflect on the relationship between built and natural environments. Consider multiple scales from urban context to material detail. Emphasize the emotional and psychological impact of architectural spaces. Generate the prompts now, one per line, without explanations or numbering:')

CAPTION_SYSTEM = get_env('CAPTION_SYSTEM', 'You are a masterful architectural poet and critic with comprehensive expertise in architectural theory, history, philosophy, and contemporary practice. Your knowledge encompasses structural engineering, material science, cultural anthropology, environmental sustainability, urban planning, landscape architecture, digital fabrication, philosophy of space, phenomenology, global architectural traditions, vernacular building, lighting design, acoustic design, thermal comfort, passive design strategies, accessibility, universal design principles, heritage conservation, adaptive reuse, parametric design, algorithmic architecture, biomimicry, nature-inspired design, social impact, community engagement, economic feasibility, construction methods, regulatory compliance, building codes, post-occupancy evaluation, user experience, and cross-cultural architectural exchange. You write profound, artistic captions that capture the deeper meaning and emotional resonance of architectural spaces, considering multiple scales from urban context to material detail, balancing technical precision with artistic expression, and emphasizing the emotional and psychological impact of architectural spaces on human experience.')

CAPTION_TEMPLATE = get_env('CAPTION_TEMPLATE', 'Write exactly 6 lines, each containing exactly 6 words, that form a complete, meaningful caption for this architectural image: {prompt}. Each line must be exactly 6 words, total of exactly 6 lines, form a coherent narrative about the architectural space, capture the philosophical, emotional, and cultural significance, consider the relationship between form, function, and human experience, balance technical precision with artistic expression, emphasize the emotional and psychological impact of architectural spaces, consider multiple scales from urban context to material detail, reflect on the relationship between built and natural environments, explore themes of permanence, transience, and transformation, consider cultural significance and historical context, explore the relationship between individual and collective experience, reflect on the role of architecture in society, consider the relationship between tradition and innovation, explore themes of sustainability and environmental responsibility, reflect on the relationship between local and global influences, consider the role of craftsmanship and detail, explore themes of beauty, harmony, and aesthetic experience, reflect on the relationship between art and architecture, consider the role of light, shadow, and atmosphere, and explore themes of human creativity and expression. Write the 6-line caption now:')

# Simplified style configuration
STYLE_CONFIG = {
    'futuristic': {'prompt_suffix': ', futuristic architecture, sci-fi aesthetic, advanced technology', 'negative_prompt': 'traditional, classical, rustic, old'},
    'minimalist': {'prompt_suffix': ', minimalist architecture, clean lines, simple forms', 'negative_prompt': 'ornate, decorative, busy, cluttered'},
    'abstract': {'prompt_suffix': ', abstract architecture, conceptual design, artistic interpretation', 'negative_prompt': 'literal, representational, traditional'},
    'technical': {'prompt_suffix': ', technical architecture, engineering precision, structural clarity', 'negative_prompt': 'artistic, decorative, ornamental'},
    'watercolor': {'prompt_suffix': ', watercolor architecture, artistic painting style, soft brushstrokes', 'negative_prompt': 'photographic, realistic, sharp'},
    'brutalist': {'prompt_suffix': ', brutalist architecture, raw concrete, massive forms', 'negative_prompt': 'delicate, refined, elegant'},
    'organic': {'prompt_suffix': ', organic architecture, flowing forms, natural curves', 'negative_prompt': 'geometric, angular, rigid'},
    'deconstructivist': {'prompt_suffix': ', deconstructivist architecture, fragmented forms, angular geometry', 'negative_prompt': 'unified, harmonious, balanced'},
    'parametric': {'prompt_suffix': ', parametric architecture, algorithmic design, computational forms', 'negative_prompt': 'traditional, manual, handcrafted'},
    'vernacular': {'prompt_suffix': ', vernacular architecture, local traditions, cultural expression', 'negative_prompt': 'modern, contemporary, international'},
    'gothic': {'prompt_suffix': ', gothic architecture, pointed arches, soaring spaces', 'negative_prompt': 'modern, contemporary, minimal'},
    'art_deco': {'prompt_suffix': ', art deco architecture, geometric patterns, decorative elements', 'negative_prompt': 'minimal, simple, plain'},
    'modernist': {'prompt_suffix': ', modernist architecture, functional design, clean lines', 'negative_prompt': 'decorative, ornate, elaborate'},
    'postmodern': {'prompt_suffix': ', postmodern architecture, eclectic design, playful forms', 'negative_prompt': 'serious, formal, rigid'},
    'high_tech': {'prompt_suffix': ', high-tech architecture, exposed structure, technological expression', 'negative_prompt': 'traditional, natural, organic'},
    'critical_regionalism': {'prompt_suffix': ', critical regionalism, local identity, cultural context', 'negative_prompt': 'universal, global, international'},
    'digital_baroque': {'prompt_suffix': ', digital baroque, complex ornamentation, digital decoration', 'negative_prompt': 'simple, minimal, plain'},
    'ecological': {'prompt_suffix': ', ecological architecture, sustainable design, environmental integration', 'negative_prompt': 'unsustainable, harmful, polluting'},
    'metabolic': {'prompt_suffix': ', metabolic architecture, modular systems, flexible design', 'negative_prompt': 'fixed, rigid, permanent'},
    'expressionist': {'prompt_suffix': ', expressionist architecture, emotional forms, dramatic spaces', 'negative_prompt': 'rational, logical, calm'},
    'constructivist': {'prompt_suffix': ', constructivist architecture, geometric abstraction, dynamic composition', 'negative_prompt': 'organic, flowing, natural'},
    'international': {'prompt_suffix': ', international style, universal design, modern aesthetic', 'negative_prompt': 'local, regional, traditional'},
    'new_urbanism': {'prompt_suffix': ', new urbanism, walkable communities, human scale', 'negative_prompt': 'car-dependent, sprawling'},
    'smart_city': {'prompt_suffix': ', smart city, technological integration, connected systems', 'negative_prompt': 'low-tech, disconnected'},
    'biophilic': {'prompt_suffix': ', biophilic architecture, nature connection, natural elements', 'negative_prompt': 'artificial, synthetic'},
    'circular': {'prompt_suffix': ', circular architecture, sustainable systems, regenerative design', 'negative_prompt': 'linear, wasteful'},
    'immersive': {'prompt_suffix': ', immersive architecture, experiential spaces, sensory design', 'negative_prompt': 'distant, disconnected'},
    'tactile': {'prompt_suffix': ', tactile architecture, material expression, textured surfaces', 'negative_prompt': 'smooth, uniform'},
    'atmospheric': {'prompt_suffix': ', atmospheric architecture, mood creation, ambient spaces', 'negative_prompt': 'neutral, bland'},
    'temporal': {'prompt_suffix': ', temporal architecture, time-based design, changing spaces', 'negative_prompt': 'static, unchanging'},
    'phenomenological': {'prompt_suffix': ', phenomenological architecture, experiential perception, sensory experience', 'negative_prompt': 'abstract, conceptual'},
    'critical': {'prompt_suffix': ', critical architecture, social commentary, political expression', 'negative_prompt': 'neutral, apolitical'}
}

# Add model to all styles
for style in STYLE_CONFIG:
    STYLE_CONFIG[style]['model'] = 'black-forest-labs/FLUX.1-schnell-free'

# Preload styles for performance
if PRELOAD_STYLES:
    STYLE_NAMES = list(STYLE_CONFIG.keys())
    log.info(f"Preloaded {len(STYLE_NAMES)} architectural styles")

def get_daily_style():
    """Get the architectural style for today based on date"""
    if PRELOAD_STYLES:
        day_of_year = datetime.now().timetuple().tm_yday
        style_index = day_of_year % len(STYLE_NAMES)
        return STYLE_NAMES[style_index]
    else:
        return random.choice(list(STYLE_CONFIG.keys()))

# Continue with the rest of the functions...

class FreshRSSAutomation:
    def __init__(self):
        self.freshrss_url = get_env('FRESHRSS_URL', 'http://localhost:8080')
        self.freshrss_user = get_env('FRESHRSS_USER', 'admin')
        self.freshrss_password = get_env('FRESHRSS_PASSWORD', 'password')
        self.freshrss_db_path = get_env('FRESHRSS_DB_PATH', '/var/www/FreshRSS/data/users/admin/db.sqlite')
        self.delay_between_requests = float(get_env('FRESHRSS_DELAY_BETWEEN_REQUESTS', '1'))
        self.articles_hours = int(get_env('FRESHRSS_ARTICLES_HOURS', '24'))

    def load_architectural_feeds(self):
        """Load architectural RSS feeds from manual sources"""
        manual_sources_file = get_env('MANUAL_SOURCES_FILE', 'manual_sources.txt')
        feeds = []
        
        if os.path.exists(manual_sources_file):
            with open(manual_sources_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        parts = line.split('|')
                        if len(parts) >= 2:
                            name = parts[0].strip()
                            url = parts[1].strip()
                            category = parts[2].strip() if len(parts) > 2 else 'General'
                            feeds.append({'name': name, 'url': url, 'category': category})
        
        return feeds

    def get_recent_articles(self, hours: int = None):
        """Get recent articles from RSS feeds"""
        if hours is None:
            hours = self.articles_hours
        
        feeds = self.load_architectural_feeds()
        all_articles = []
        
        for feed in feeds:
            try:
                articles = self.scrape_rss_feed(feed['url'], feed['name'], feed['category'])
                all_articles.extend(articles)
                time.sleep(self.delay_between_requests)
            except Exception as e:
                log.error(f"Error scraping {feed['name']}: {e}")
        
        return all_articles

    def fallback_rss_scraping(self):
        """Fallback RSS scraping if FreshRSS is not available"""
        log.info("Using fallback RSS scraping")
        return self.get_recent_articles()

    def scrape_rss_feed(self, feed_url, feed_name, category):
        """Scrape a single RSS feed"""
        try:
            feed = feedparser.parse(feed_url)
            articles = []
            
            for entry in feed.entries[:10]:  # Limit to 10 articles per feed
                article = {
                    'title': entry.get('title', ''),
                    'summary': entry.get('summary', ''),
                    'link': entry.get('link', ''),
                    'published': entry.get('published', ''),
                    'source': feed_name,
                    'category': category
                }
                articles.append(article)
            
            log.info(f"Scraped {len(articles)} articles from {feed_name}")
            return articles
            
        except Exception as e:
            log.error(f"Error scraping {feed_name}: {e}")
            return []

    def analyze_content_themes(self, articles):
        """Analyze articles to extract themes"""
        if not articles:
            return "Modern Architecture"
        
        # Extract keywords from titles and summaries
        text_content = " ".join([f"{a['title']} {a['summary']}" for a in articles])
        
        # Simple keyword extraction
        keywords = ['architecture', 'design', 'building', 'construction', 'urban', 'sustainable', 'modern', 'traditional']
        found_keywords = [kw for kw in keywords if kw.lower() in text_content.lower()]
        
        if found_keywords:
            return f"{found_keywords[0].title()} Architecture"
        else:
            return "Contemporary Architecture"

    def create_zine_theme_prompt(self, articles):
        """Create a theme prompt from articles"""
        theme = self.analyze_content_themes(articles)
        return f"Create a daily architectural zine theme based on: {theme}"

def scrape_architectural_content():
    """Main function to scrape architectural content"""
    if SKIP_WEB_SCRAPING:
        log.info("Skipping web scraping")
        return []
    
    freshrss = FreshRSSAutomation()
    articles = freshrss.fallback_rss_scraping()
    
    if not articles:
        log.warning("No articles found, using fallback theme")
        return []
    
    log.info(f"Scraped {len(articles)} architectural articles")
    return articles

def add_daily_architectural_source():
    """Add a new architectural source daily"""
    if not get_env('DAILY_SOURCE_ADDITION_ENABLED', 'true').lower() == 'true':
        return
    
    predefined_sources = get_env('PREDEFINED_SOURCES', '').split(',')
    categories = get_env('SOURCE_CATEGORIES', 'Academic,Research,International').split(',')
    
    if predefined_sources:
        source = random.choice(predefined_sources).strip()
        if source:
            parts = source.split('|')
            if len(parts) >= 2:
                name = parts[0].strip()
                url = parts[1].strip()
                category = random.choice(categories)
                
                manual_sources_file = get_env('MANUAL_SOURCES_FILE', 'manual_sources.txt')
                with open(manual_sources_file, 'a', encoding='utf-8') as f:
                    f.write(f"{name}|{url}|{category}\n")
                
                log.info(f"Added daily source: {name}")

def display_architectural_sources():
    """Display current architectural sources"""
    manual_sources_file = get_env('MANUAL_SOURCES_FILE', 'manual_sources.txt')
    
    if not os.path.exists(manual_sources_file):
        print("No sources file found")
        return
    
    print("\n📚 Current Architectural Sources:")
    print("=" * 50)
    
    with open(manual_sources_file, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if line and not line.startswith('#'):
                parts = line.split('|')
                if len(parts) >= 2:
                    name = parts[0].strip()
                    url = parts[1].strip()
                    category = parts[2].strip() if len(parts) > 2 else 'General'
                    print(f"{line_num:2d}. {name} ({category})")
                    print(f"    {url}")
                    print()

def add_manual_source(name, url, category):
    """Add a single source manually"""
    log.info(f"Adding manual source: {name}")
    manual_sources_file = get_env('MANUAL_SOURCES_FILE', 'manual_sources.txt')
    
    # Check if source already exists
    if os.path.exists(manual_sources_file):
        with open(manual_sources_file, 'r', encoding='utf-8') as f:
            existing_sources = f.read()
            if name in existing_sources:
                log.warning(f"Source '{name}' already exists")
                return
    
    # Add new source
    with open(manual_sources_file, 'a', encoding='utf-8') as f:
        f.write(f"{name}|{url}|{category}\n")
    
    log.info(f"Successfully added: {name}")

def remove_manual_source(name):
    """Remove a source by name"""
    log.info(f"Removing manual source: {name}")
    manual_sources_file = get_env('MANUAL_SOURCES_FILE', 'manual_sources.txt')
    
    if not os.path.exists(manual_sources_file):
        log.error("Sources file not found")
        return
    
    # Read all sources and filter out the one to remove
    with open(manual_sources_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    filtered_lines = []
    removed = False
    
    for line in lines:
        if line.strip() and not line.startswith('#'):
            parts = line.split('|')
            if len(parts) >= 1 and parts[0].strip() != name:
                filtered_lines.append(line)
            else:
                removed = True
        else:
            filtered_lines.append(line)
    
    # Write back filtered sources
    with open(manual_sources_file, 'w', encoding='utf-8') as f:
        f.writelines(filtered_lines)
    
    if removed:
        log.info(f"Successfully removed: {name}")
    else:
        log.warning(f"Source '{name}' not found")

def add_batch_manual_sources():
    """Add multiple sources in batch"""
    print("Enter sources in format: Name|URL|Category")
    print("Enter 'done' when finished:")
    
    manual_sources_file = get_env('MANUAL_SOURCES_FILE', 'manual_sources.txt')
    
    while True:
        source_input = input("Source: ").strip()
        if source_input.lower() == 'done':
            break
        
        if '|' in source_input:
            parts = source_input.split('|')
            if len(parts) >= 2:
                name = parts[0].strip()
                url = parts[1].strip()
                category = parts[2].strip() if len(parts) > 2 else 'General'
                
                with open(manual_sources_file, 'a', encoding='utf-8') as f:
                    f.write(f"{name}|{url}|{category}\n")
                
                print(f"Added: {name}")
            else:
                print("Invalid format. Use: Name|URL|Category")
        else:
            print("Invalid format. Use: Name|URL|Category")

def call_llm(prompt, system_prompt=None):
    """Call LLM with caching"""
    cache_key = f"llm_{hashlib.md5((prompt + (system_prompt or '')).encode()).hexdigest()}"
    
    # Try to load from cache first
    cached_response = load_from_cache(cache_key)
    if cached_response:
        return cached_response
    
    # Call API
    headers = {
        "Authorization": f"Bearer {TOGETHER_API_KEY}",
        "Content-Type": "application/json"
    }
    
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})
    
    payload = {
        "model": TEXT_MODEL,
        "messages": messages,
        "max_tokens": 2000,
        "temperature": 0.7
    }
    
    max_retries = int(get_env('LLM_MAX_RETRIES', '3'))
    retry_delays = [int(x) for x in get_env('LLM_RETRY_DELAYS', '60,120,180').split(',')]
    
    for attempt in range(max_retries):
        try:
            response = requests.post(
                f"{TOGETHER_API_BASE}/chat/completions",
                headers=headers,
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result['choices'][0]['message']['content']
                
                # Save to cache
                save_to_cache(cache_key, content)
                return content
            else:
                log.error(f"API error: {response.status_code} - {response.text}")
                
        except Exception as e:
            log.error(f"Request failed (attempt {attempt + 1}): {e}")
        
        if attempt < max_retries - 1:
            delay = retry_delays[min(attempt, len(retry_delays) - 1)]
            log.info(f"Retrying in {delay} seconds...")
            time.sleep(delay)
    
    raise Exception("All LLM API calls failed")

def generate_prompts(theme, num_prompts=50):
    """Generate image prompts from theme"""
    if SKIP_PROMPT_GENERATION:
        log.info("Skipping prompt generation")
        return [f"architectural design, {theme}" for _ in range(num_prompts)]
    
    prompt = PROMPT_TEMPLATE.format(n=num_prompts, theme=theme)
    response = call_llm(prompt, PROMPT_SYSTEM)
    
    prompts = [line.strip() for line in response.split('\n') if line.strip()]
    return prompts[:num_prompts]

def calculate_similarity_score(caption1, caption2):
    """Calculate similarity between two captions"""
    words1 = set(caption1.lower().split())
    words2 = set(caption2.lower().split())
    
    if not words1 or not words2:
        return 0.0
    
    intersection = words1.intersection(words2)
    union = words1.union(words2)
    
    return len(intersection) / len(union)

def is_caption_unique(new_caption, existing_captions, similarity_threshold=None):
    """Check if caption is unique"""
    if similarity_threshold is None:
        similarity_threshold = float(get_env('CAPTION_SIMILARITY_THRESHOLD', '0.3'))
    
    for existing in existing_captions:
        similarity = calculate_similarity_score(new_caption, existing)
        if similarity > similarity_threshold:
            return False
    return True

def generate_unique_caption(prompt, existing_captions, max_attempts=None):
    """Generate a unique caption"""
    if max_attempts is None:
        max_attempts = int(get_env('CAPTION_MAX_ATTEMPTS', '5'))
    
    for attempt in range(max_attempts):
        caption = generate_caption(prompt)
        
        if SKIP_CAPTION_DEDUPLICATION or is_caption_unique(caption, existing_captions):
            return caption
        
        log.debug(f"Caption not unique, retrying... (attempt {attempt + 1})")
    
    return generate_caption(prompt)  # Return last attempt even if not unique

def generate_caption(prompt):
    """Generate a single caption"""
    prompt_text = CAPTION_TEMPLATE.format(prompt=prompt)
    response = call_llm(prompt_text, CAPTION_SYSTEM)
    
    # Clean up response
    lines = [line.strip() for line in response.split('\n') if line.strip()]
    return '\n'.join(lines[:6])  # Return first 6 lines

def generate_single_image(prompt, style_name, image_number):
    """Generate a single image"""
    if style_name not in STYLE_CONFIG:
        style_name = 'abstract'
    
    style_config = STYLE_CONFIG[style_name]
    full_prompt = prompt + style_config['prompt_suffix']
    negative_prompt = style_config['negative_prompt']
    
    headers = {
        "Authorization": f"Bearer {TOGETHER_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": IMAGE_MODEL,
        "prompt": full_prompt,
        "negative_prompt": negative_prompt,
        "width": IMAGE_WIDTH,
        "height": IMAGE_HEIGHT,
        "steps": INFERENCE_STEPS,
        "guidance_scale": GUIDANCE_SCALE
    }
    
    max_retries = int(get_env('IMAGE_MAX_RETRIES', '3'))
    retry_delays = [int(x) for x in get_env('IMAGE_RETRY_DELAYS', '60,120,180').split(',')]
    
    for attempt in range(max_retries):
        try:
            response = requests.post(
                f"{TOGETHER_API_BASE}/images/generations",
                headers=headers,
                json=payload,
                timeout=120
            )
            
            if response.status_code == 200:
                result = response.json()
                image_data = result['data'][0]['url']
                
                # Save image
                images_dir = Path(get_env('IMAGES_DIR', 'images'))
                images_dir.mkdir(exist_ok=True)
                
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"{timestamp}_{image_number:02d}_{style_name}.jpg"
                filepath = images_dir / filename
                
                # Download and save image
                img_response = requests.get(image_data)
                with open(filepath, 'wb') as f:
                    f.write(img_response.content)
                
                log.info(f"Generated image {image_number}: {filename}")
                return str(filepath)
            else:
                log.error(f"Image API error: {response.status_code} - {response.text}")
                
        except Exception as e:
            log.error(f"Image generation failed (attempt {attempt + 1}): {e}")
        
        if attempt < max_retries - 1:
            delay = retry_delays[min(attempt, len(retry_delays) - 1)]
            log.info(f"Retrying image generation in {delay} seconds...")
            time.sleep(delay)
    
    raise Exception(f"Failed to generate image {image_number}")

def generate_all_images(prompts, style_name):
    """Generate all images with concurrency"""
    log.info(f"Generating {len(prompts)} images in {style_name} style")
    
    images = []
    
    if MAX_CONCURRENT_IMAGES > 1:
        with ThreadPoolExecutor(max_workers=MAX_CONCURRENT_IMAGES) as executor:
            futures = []
            for i, prompt in enumerate(prompts):
                future = executor.submit(generate_single_image, prompt, style_name, i + 1)
                futures.append(future)
                time.sleep(RATE_LIMIT_DELAY)
            
            for future in tqdm(as_completed(futures), total=len(futures), desc="Generating images"):
                try:
                    image_path = future.result()
                    images.append(image_path)
                except Exception as e:
                    log.error(f"Image generation failed: {e}")
    else:
        for i, prompt in enumerate(tqdm(prompts, desc="Generating images")):
            try:
                image_path = generate_single_image(prompt, style_name, i + 1)
                images.append(image_path)
                time.sleep(RATE_LIMIT_DELAY)
            except Exception as e:
                log.error(f"Image generation failed: {e}")
    
    return images

def generate_all_captions(prompts):
    """Generate all captions with concurrency"""
    log.info(f"Generating {len(prompts)} captions")
    
    captions = []
    
    if MAX_CONCURRENT_CAPTIONS > 1:
        with ThreadPoolExecutor(max_workers=MAX_CONCURRENT_CAPTIONS) as executor:
            futures = []
            for i, prompt in enumerate(prompts):
                future = executor.submit(generate_unique_caption, prompt, captions)
                futures.append(future)
                time.sleep(RATE_LIMIT_DELAY)
            
            for future in tqdm(as_completed(futures), total=len(futures), desc="Generating captions"):
                try:
                    caption = future.result()
                    captions.append(caption)
                except Exception as e:
                    log.error(f"Caption generation failed: {e}")
    else:
        for i, prompt in enumerate(tqdm(prompts, desc="Generating captions")):
            try:
                caption = generate_unique_caption(prompt, captions)
                captions.append(caption)
                time.sleep(RATE_LIMIT_DELAY)
            except Exception as e:
                log.error(f"Caption generation failed: {e}")
    
    return captions

def place_caption_with_white_band(c, caption, w, h, page_num):
    """Place caption with white band for readability"""
    font_size = int(get_env('PDF_FONT_SIZE', '14'))
    line_spacing = int(get_env('PDF_LINE_SPACING', '18'))
    padding_x = int(get_env('PDF_PADDING_X', '24'))
    padding_y = int(get_env('PDF_PADDING_Y', '16'))
    top_padding = int(get_env('PDF_TOP_PADDING', '40'))
    band_y = int(get_env('PDF_BAND_Y', '0'))
    band_x = int(get_env('PDF_BAND_X', '0'))
    
    # Create white band
    band_height = 120
    band_y_pos = h - band_height - 20
    
    c.setFillColorRGB(1, 1, 1)
    c.rect(band_x, band_y_pos, w - band_x, band_height, fill=1)
    
    # Add caption text
    c.setFillColorRGB(0, 0, 0)
    c.setFont("Helvetica", font_size)
    
    lines = caption.split('\n')
    y_pos = band_y_pos + band_height - 20
    
    for line in lines:
        if line.strip():
            c.drawString(padding_x, y_pos, line.strip())
            y_pos -= line_spacing

def create_daily_pdf(images, captions, style_name, theme):
    """Create the daily PDF zine"""
    if SKIP_PDF_CREATION:
        log.info("Skipping PDF creation")
        return None
    
    log.info("Creating daily PDF zine")
    
    # Create output directory
    daily_pdfs_dir = Path(get_env('DAILY_PDFS_DIR', 'daily_pdfs'))
    daily_pdfs_dir.mkdir(exist_ok=True)
    
    # Generate filename
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    volume = datetime.now().strftime('%Y%m%d')
    filename = f"ASK_Daily_Architectural_Research_Zine-{datetime.now().year}-VOL-{volume}-{style_name.title()}.pdf"
    filepath = daily_pdfs_dir / filename
    
    # Create PDF
    c = canvas.Canvas(str(filepath), pagesize=A4)
    w, h = A4
    
    # Add pages
    for i, (image_path, caption) in enumerate(zip(images, captions)):
        if os.path.exists(image_path):
            # Add image
            img = Image.open(image_path)
            img_reader = ImageReader(img)
            
            # Scale image to fit page
            img_w, img_h = img.size
            scale = min(w / img_w, h / img_h)
            new_w = img_w * scale
            new_h = img_h * scale
            
            x = (w - new_w) / 2
            y = (h - new_h) / 2
            
            c.drawImage(img_reader, x, y, width=new_w, height=new_h)
            
            # Add caption
            place_caption_with_white_band(c, caption, w, h, i + 1)
        
        c.showPage()
    
    c.save()
    log.info(f"Created PDF: {filename}")
    return str(filepath)

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Daily Architectural Zine Generator')
    parser.add_argument('--sources', action='store_true', help='Display current sources')
    parser.add_argument('--add-source', nargs=3, metavar=('NAME', 'URL', 'CATEGORY'), help='Add a source')
    parser.add_argument('--remove-source', metavar='NAME', help='Remove a source')
    parser.add_argument('--batch-sources', action='store_true', help='Add multiple sources')
    parser.add_argument('--fast', action='store_true', help='Enable fast mode')
    parser.add_argument('--ultra', action='store_true', help='Enable ultra mode')
    
    args = parser.parse_args()
    
    # Handle source management
    if args.sources:
        display_architectural_sources()
        return
    
    if args.add_source:
        name, url, category = args.add_source
        add_manual_source(name, url, category)
        return
    
    if args.remove_source:
        remove_manual_source(args.remove_source)
        return
    
    if args.batch_sources:
        add_batch_manual_sources()
        return
    
    # Set performance mode
    global RATE_LIMIT_DELAY, MAX_CONCURRENT_IMAGES, MAX_CONCURRENT_CAPTIONS
    
    if args.ultra:
        RATE_LIMIT_DELAY = float(get_env('ULTRA_MODE_DELAY', '6.0'))
        MAX_CONCURRENT_IMAGES = int(get_env('ULTRA_MODE_CONCURRENT_IMAGES', '1'))
        MAX_CONCURRENT_CAPTIONS = int(get_env('ULTRA_MODE_CONCURRENT_CAPTIONS', '1'))
        log.info("Ultra mode enabled")
    elif args.fast:
        RATE_LIMIT_DELAY = float(get_env('FAST_MODE_DELAY', '6.0'))
        log.info("Fast mode enabled")
    
    # Main pipeline
    log.info("🚀 Starting Daily Architectural Zine Generation")
    
    # Step 1: Scrape content
    articles = scrape_architectural_content()
    
    # Step 2: Generate theme
    if SKIP_THEME_GENERATION:
        theme = "Modern Architecture"
        log.info("Using fallback theme")
    else:
        freshrss = FreshRSSAutomation()
        theme = freshrss.analyze_content_themes(articles)
        log.info(f"Generated theme: {theme}")
    
    # Step 3: Get daily style
    style_name = get_daily_style()
    log.info(f"Selected style: {style_name}")
    
    # Step 4: Generate prompts
    prompts = generate_prompts(theme)
    log.info(f"Generated {len(prompts)} prompts")
    
    # Step 5: Generate images
    images = generate_all_images(prompts, style_name)
    log.info(f"Generated {len(images)} images")
    
    # Step 6: Generate captions
    captions = generate_all_captions(prompts)
    log.info(f"Generated {len(captions)} captions")
    
    # Step 7: Create PDF
    pdf_path = create_daily_pdf(images, captions, style_name, theme)
    
    # Step 8: Add daily source
    add_daily_architectural_source()
    
    log.info("✅ Daily zine generation complete!")
    
    if OPTIMIZE_MEMORY:
        gc.collect()

if __name__ == "__main__":
    main() 