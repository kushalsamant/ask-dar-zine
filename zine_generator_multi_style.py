import os
import sys
import subprocess
import logging
import time
from datetime import datetime
import concurrent.futures
import threading
from queue import Queue
import traceback

# === 🔧 Setup logging with better configuration ===
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)
log_filename = os.path.join(LOG_DIR, f"multi_style_zine_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")

# Configure logging with better formatting
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
REQUIRED_LIBS = [
    'python-dotenv', 'replicate', 'reportlab',
    'feedparser', 'requests', 'Pillow', 'beautifulsoup4'
]

def install_missing_libs():
    """Install missing dependencies with better error handling"""
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
    import replicate
    import requests
    import feedparser
    from dotenv import load_dotenv
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.utils import ImageReader
    from PIL import Image
    from io import BytesIO
    import random
    log.info("✅ All imports successful")
except ImportError as e:
    log.error(f"❌ Import error: {e}")
    sys.exit(1)

# === Web scraping imports ===
try:
    from web_scraper import WebScraper
    from date_filter import DateFilter
    WEB_SCRAPING_AVAILABLE = True
    log.info("✅ Web scraping modules available")
except ImportError as e:
    log.warning(f"⚠️ Web scraping modules not available: {e}")
    log.info("🔄 Using fallback theme generation")
    WEB_SCRAPING_AVAILABLE = False

# === 📥 Load environment variables ===
load_dotenv('ask.env')

# === 📌 Environment config ===
def get_env(var, default=None, required=False):
    """Get environment variable with better error handling"""
    value = os.getenv(var, default)
    if required and not value:
        log.error(f"❌ Required environment variable '{var}' is missing. Exiting.")
        sys.exit(1)
    return value

# === 🚦 Rate limiting for API calls ===
class RateLimiter:
    def __init__(self, max_calls_per_minute=30):
        self.max_calls = max_calls_per_minute
        self.calls = []
        self.lock = threading.Lock()
    
    def wait_if_needed(self):
        """Wait if rate limit is reached"""
        with self.lock:
            now = time.time()
            # Remove calls older than 1 minute
            self.calls = [call_time for call_time in self.calls if now - call_time < 60]
            
            if len(self.calls) >= self.max_calls:
                # Wait until we can make another call
                sleep_time = 60 - (now - self.calls[0])
                if sleep_time > 0:
                    log.info(f"⏳ Rate limit reached, waiting {sleep_time:.1f}s")
                    time.sleep(sleep_time)
            
            self.calls.append(time.time())

# === 🎨 Style Models Configuration ===
STYLE_MODELS = {
    'futuristic': {
        'model': 'stability-ai/sdxl:39ed52f2a78e934b3ba6e2a89f5b1c712de7dfea535525255b1aa35c5565e08b',
        'prompt_suffix': ', futuristic sci-fi style, neon colors, advanced technology, cyberpunk aesthetic',
        'negative_prompt': 'cartoon, anime, sketch, watercolor, traditional art, vintage'
    },
    'minimalist': {
        'model': 'stability-ai/sdxl:39ed52f2a78e934b3ba6e2a89f5b1c712de7dfea535525255b1aa35c5565e08b',
        'prompt_suffix': ', minimalist design, clean lines, simple composition, modern aesthetic',
        'negative_prompt': 'complex, cluttered, detailed, ornate, busy'
    },
    'sketch': {
        'model': 'stability-ai/sdxl:39ed52f2a78e934b3ba6e2a89f5b1c712de7dfea535525255b1aa35c5565e08b',
        'prompt_suffix': ', pencil sketch style, hand-drawn, artistic line work, monochrome',
        'negative_prompt': 'colorful, digital art, 3d render, photorealistic'
    },
    'abstract': {
        'model': 'stability-ai/sdxl:39ed52f2a78e934b3ba6e2a89f5b1c712de7dfea535525255b1aa35c5565e08b',
        'prompt_suffix': ', abstract art style, geometric shapes, vibrant colors, modern art',
        'negative_prompt': 'realistic, photorealistic, traditional, representational'
    },
    'technical': {
        'model': 'stability-ai/sdxl:39ed52f2a78e934b3ba6e2a89f5b1c712de7dfea535525255b1aa35c5565e08b',
        'prompt_suffix': ', technical drawing style, blueprint aesthetic, engineering diagrams, precise lines',
        'negative_prompt': 'artistic, abstract, colorful, organic shapes'
    },
    'watercolor': {
        'model': 'stability-ai/sdxl:39ed52f2a78e934b3ba6e2a89f5b1c712de7dfea535525255b1aa35c5565e08b',
        'prompt_suffix': ', watercolor painting style, soft edges, flowing colors, artistic',
        'negative_prompt': 'digital art, sharp edges, geometric, technical'
    },
    'anime': {
        'model': 'stability-ai/sdxl:39ed52f2a78e934b3ba6e2a89f5b1c712de7dfea535525255b1aa35c5565e08b',
        'prompt_suffix': ', anime style, Japanese animation, vibrant colors, stylized characters',
        'negative_prompt': 'realistic, photorealistic, western animation, 3d'
    },
    'photorealistic': {
        'model': 'stability-ai/sdxl:39ed52f2a78e934b3ba6e2a89f5b1c712de7dfea535525255b1aa35c5565e08b',
        'prompt_suffix': ', photorealistic style, high detail, realistic lighting, professional photography',
        'negative_prompt': 'cartoon, anime, abstract, artistic, stylized'
    }
}

# === 🔧 Performance and Configuration Settings ===
TEXT_PROVIDER = get_env("TEXT_PROVIDER", "groq")
TEXT_MODEL = get_env("TEXT_MODEL", required=True)
IMAGE_WIDTH = int(get_env("IMAGE_WIDTH", "2048"))
IMAGE_HEIGHT = int(get_env("IMAGE_HEIGHT", "1024"))
IMAGE_DPI = int(get_env("IMAGE_DPI", "300"))
CAPTION_FONT_SIZE = int(get_env("CAPTION_FONT_SIZE", "14"))
CAPTION_LINE_SPACING = int(get_env("CAPTION_LINE_SPACING", "18"))
CAPTION_POSITION = get_env("CAPTION_POSITION", "top-right")
NUM_STEPS = int(get_env("NUM_INFERENCE_STEPS", "30"))
GUIDANCE_SCALE = float(get_env("GUIDANCE_SCALE", "7.5"))
FILTER_KEYWORDS = [kw.strip() for kw in get_env("FILTER_KEYWORDS", "").split(",") if kw.strip()]

# Performance settings
MAX_CONCURRENT_IMAGES = int(get_env("MAX_CONCURRENT_IMAGES", "4"))
MAX_RETRIES = int(get_env("MAX_RETRIES", "3"))
RATE_LIMIT_PER_MINUTE = int(get_env("RATE_LIMIT_PER_MINUTE", "30"))

# Initialize rate limiter
rate_limiter = RateLimiter(RATE_LIMIT_PER_MINUTE)

# === API Keys and Endpoints ===
API_BASES = {
    "groq": get_env("GROQ_API_BASE", "https://api.groq.com/openai/v1"),
    "together": get_env("TOGETHER_API_BASE", "https://api.together.xyz/v1")
}
API_KEYS = {
    "groq": get_env("GROQ_API_KEY", required=True),
    "together": get_env("TOGETHER_API_KEY")
}

HEADERS = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {API_KEYS[TEXT_PROVIDER]}"
}
TEXT_API_URL = f"{API_BASES[TEXT_PROVIDER]}/chat/completions"

# === 🌐 Dynamic RSS Source Management ===
RSS_SOURCES = {
    'tech': {
        'TechCrunch': 'https://techcrunch.com/feed/',
        'Ars Technica': 'https://feeds.arstechnica.com/arstechnica/index',
        'The Verge': 'https://www.theverge.com/rss/index.xml',
        'Wired': 'https://www.wired.com/feed/rss',
        'MIT Technology Review': 'https://www.technologyreview.com/feed/',
        'IEEE Spectrum': 'https://spectrum.ieee.org/rss/fulltext',
        'VentureBeat': 'https://venturebeat.com/feed/',
        'TechRadar': 'https://www.techradar.com/rss',
        'Engadget': 'https://www.engadget.com/rss.xml',
        'Gizmodo': 'https://gizmodo.com/rss'
    },
    'science': {
        'Nature': 'https://www.nature.com/nature.rss',
        'Science': 'https://www.science.org/rss/news_current.xml',
        'Scientific American': 'https://rss.sciam.com/ScientificAmerican-Global',
        'Science Daily': 'https://www.sciencedaily.com/rss/all.xml',
        'New Scientist': 'https://www.newscientist.com/feed/home/?cmpid=RSS',
        'Popular Science': 'https://www.popsci.com/rss.xml',
        'Science News': 'https://www.sciencenews.org/feed',
        'Quanta Magazine': 'https://www.quantamagazine.org/feed/',
        'Physics World': 'https://physicsworld.com/feed/',
        'Chemistry World': 'https://www.chemistryworld.com/rss'
    },
    'architecture': {
        'ArchDaily': 'https://www.archdaily.com/rss',
        'Dezeen': 'https://www.dezeen.com/feed/',
        'Architectural Digest': 'https://www.architecturaldigest.com/rss.xml',
        'Architect Magazine': 'https://www.architectmagazine.com/rss',
        'Architecture Now': 'https://architecturenow.co.nz/feed/',
        'Architectural Review': 'https://www.architectural-review.com/rss',
        'Architecture Lab': 'https://www.architecturelab.net/feed/',
        'Architecture & Design': 'https://www.architectureanddesign.com.au/rss',
        'Architectural Record': 'https://www.architecturalrecord.com/rss',
        'Architectural Digest India': 'https://www.architecturaldigest.in/rss'
    },
    'innovation': {
        'Fast Company': 'https://www.fastcompany.com/feed',
        'Harvard Business Review': 'https://hbr.org/feed',
        'MIT Sloan Management Review': 'https://sloanreview.mit.edu/feed/',
        'Innovation Excellence': 'https://www.innovationexcellence.com/feed/',
        'Innovation Management': 'https://innovationmanagement.se/feed/',
        'Stanford Social Innovation Review': 'https://ssir.org/rss',
        'Innovation Leader': 'https://www.innovationleader.com/feed/',
        'Innovation Enterprise': 'https://channels.theinnovationenterprise.com/rss',
        'Innovation Excellence': 'https://www.innovationexcellence.com/feed/',
        'Innovation Management': 'https://innovationmanagement.se/feed/'
    }
}

def get_best_rss_sources(category='tech', max_sources=5):
    """Dynamically select the best RSS sources based on availability and content quality"""
    try:
        available_sources = {}
        category_sources = RSS_SOURCES.get(category, RSS_SOURCES['tech'])
        
        log.info(f"🔍 Testing {len(category_sources)} RSS sources for category: {category}")
        
        for source_name, url in category_sources.items():
            try:
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    feed = feedparser.parse(response.content)
                    if feed.entries and len(feed.entries) > 0:
                        # Calculate source quality score
                        quality_score = calculate_source_quality(feed)
                        available_sources[source_name] = {
                            'url': url,
                            'quality_score': quality_score,
                            'entry_count': len(feed.entries),
                            'latest_update': get_latest_entry_date(feed)
                        }
                        log.info(f"✅ {source_name}: {quality_score:.2f} quality score, {len(feed.entries)} entries")
                    else:
                        log.warning(f"⚠️ {source_name}: No entries found")
                else:
                    log.warning(f"⚠️ {source_name}: HTTP {response.status_code}")
            except Exception as e:
                log.warning(f"⚠️ {source_name}: {e}")
        
        # Sort by quality score and select top sources
        sorted_sources = sorted(available_sources.items(), 
                              key=lambda x: x[1]['quality_score'], reverse=True)
        
        selected_sources = sorted_sources[:max_sources]
        
        log.info(f"🎯 Selected top {len(selected_sources)} sources:")
        for source_name, info in selected_sources:
            log.info(f"  📡 {source_name}: {info['quality_score']:.2f} score")
        
        return [info['url'] for _, info in selected_sources]
        
    except Exception as e:
        log.error(f"❌ Error selecting RSS sources: {e}")
        # Fallback to default sources
        return list(RSS_SOURCES['tech'].values())[:max_sources]

def calculate_source_quality(feed):
    """Calculate quality score for RSS source based on content analysis"""
    try:
        score = 0.0
        entries = feed.entries[:20]  # Analyze first 20 entries
        
        if not entries:
            return 0.0
        
        # Content length analysis
        avg_title_length = sum(len(entry.title) for entry in entries) / len(entries)
        if 20 <= avg_title_length <= 100:
            score += 0.3
        
        # Content freshness
        recent_entries = 0
        for entry in entries:
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                pub_date = datetime(*entry.published_parsed[:6])
                if (datetime.now() - pub_date).days <= 7:
                    recent_entries += 1
        
        freshness_ratio = recent_entries / len(entries)
        score += freshness_ratio * 0.4
        
        # Content diversity (avoid duplicate titles)
        titles = [entry.title.lower() for entry in entries]
        unique_titles = len(set(titles))
        diversity_ratio = unique_titles / len(titles)
        score += diversity_ratio * 0.3
        
        return min(score, 1.0)
        
    except Exception as e:
        log.warning(f"⚠️ Error calculating source quality: {e}")
        return 0.5

def get_latest_entry_date(feed):
    """Get the date of the latest entry in the feed"""
    try:
        for entry in feed.entries:
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                return datetime(*entry.published_parsed[:6])
        return datetime.now()
    except:
        return datetime.now()

def get_theme_from_rss():
    """Get theme from dynamic RSS sources with better content selection"""
    try:
        # Select best sources for current run
        category = random.choice(['tech', 'science', 'architecture', 'innovation'])
        rss_urls = get_best_rss_sources(category, max_sources=3)
        
        headlines = []
        source_quality = {}
        
        for url in rss_urls:
            try:
                log.info(f"📡 Fetching RSS feed: {url}")
                response = requests.get(url, timeout=15)
                response.raise_for_status()
                
                feed = feedparser.parse(response.content)
                
                for entry in feed.entries[:10]:  # Get top 10 entries
                    title = entry.title.strip()
                    
                    # Enhanced content filtering
                    if is_quality_headline(title, category):
                        headlines.append({
                            'title': title,
                            'source': feed.feed.get('title', 'Unknown'),
                            'url': entry.get('link', ''),
                            'category': category,
                            'quality_score': calculate_headline_quality(title, category)
                        })
                        
            except Exception as e:
                log.warning(f"⚠️ RSS failed for {url}: {e}")
                continue
        
        if headlines:
            # Sort by quality score and select best headline
            headlines.sort(key=lambda x: x['quality_score'], reverse=True)
            selected = headlines[0]
            
            log.info(f"🎯 Selected theme: {selected['title'][:50]}...")
            log.info(f"📊 Quality score: {selected['quality_score']:.2f}")
            log.info(f"📡 Source: {selected['source']}")
            
            return selected['title']
        else:
            fallback_theme = get_env("FALLBACK_THEME", "Architecture & AI")
            log.info(f"🔄 Using fallback theme: {fallback_theme}")
            return fallback_theme
            
    except Exception as e:
        log.error(f"❌ Error in RSS theme generation: {e}")
        fallback_theme = get_env("FALLBACK_THEME", "Architecture & AI")
        log.info(f"🔄 Using fallback theme: {fallback_theme}")
        return fallback_theme

def is_quality_headline(title, category):
    """Check if headline meets quality criteria"""
    if not title or len(title) < 10:
        return False
    
    # Filter out common low-quality patterns
    low_quality_patterns = [
        'breaking news', 'just in', 'update', 'alert', 'urgent',
        'exclusive', 'shocking', 'amazing', 'incredible', 'unbelievable'
    ]
    
    title_lower = title.lower()
    for pattern in low_quality_patterns:
        if pattern in title_lower:
            return False
    
    # Category-specific filtering
    if category == 'tech':
        tech_keywords = ['ai', 'artificial intelligence', 'machine learning', 'technology', 'innovation', 'startup', 'software', 'hardware', 'digital', 'cyber']
        return any(keyword in title_lower for keyword in tech_keywords)
    elif category == 'science':
        science_keywords = ['research', 'study', 'discovery', 'scientific', 'experiment', 'analysis', 'finding', 'breakthrough']
        return any(keyword in title_lower for keyword in science_keywords)
    elif category == 'architecture':
        arch_keywords = ['architecture', 'design', 'building', 'construction', 'urban', 'sustainable', 'modern', 'traditional', 'space', 'structure']
        return any(keyword in title_lower for keyword in arch_keywords)
    elif category == 'innovation':
        innovation_keywords = ['innovation', 'creative', 'solution', 'problem', 'challenge', 'future', 'next generation', 'revolutionary']
        return any(keyword in title_lower for keyword in innovation_keywords)
    
    return True

def calculate_headline_quality(title, category):
    """Calculate quality score for individual headline"""
    score = 0.0
    
    # Length score (prefer medium-length titles)
    length = len(title)
    if 20 <= length <= 80:
        score += 0.3
    elif 10 <= length <= 120:
        score += 0.2
    
    # Complexity score (prefer substantive content)
    words = title.split()
    if 4 <= len(words) <= 12:
        score += 0.3
    
    # Category relevance score
    category_keywords = {
        'tech': ['ai', 'technology', 'digital', 'innovation', 'software', 'hardware'],
        'science': ['research', 'study', 'discovery', 'scientific', 'analysis'],
        'architecture': ['architecture', 'design', 'building', 'space', 'structure'],
        'innovation': ['innovation', 'creative', 'solution', 'future', 'revolutionary']
    }
    
    title_lower = title.lower()
    keywords = category_keywords.get(category, [])
    keyword_matches = sum(1 for keyword in keywords if keyword in title_lower)
    score += (keyword_matches / len(keywords)) * 0.4
    
    return min(score, 1.0)

def get_theme():
    """Get theme from command line or dynamic RSS"""
    if len(sys.argv) > 1:
        theme = ' '.join(sys.argv[1:])
        log.info(f"🎯 Using command line theme: {theme}")
        return theme
    return get_theme_from_rss()

# === 🧠 LLM Integration ===
def call_llm(messages, max_retries=3):
    """Call LLM with retry logic and error handling"""
    for attempt in range(max_retries):
        try:
            # Rate limiting
            rate_limiter.wait_if_needed()
            
            response = requests.post(
                TEXT_API_URL,
                headers=HEADERS,
                json={
                    "model": TEXT_MODEL,
                    "messages": messages,
                    "max_tokens": 500,
                    "temperature": 0.7
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                content = data['choices'][0]['message']['content'].strip()
                log.info(f"✅ LLM call successful (attempt {attempt + 1})")
                return content
            elif response.status_code == 429:
                log.warning(f"⚠️ Rate limited (attempt {attempt + 1}), waiting...")
                time.sleep(60)  # Wait 1 minute for rate limit
            elif response.status_code == 500:
                log.warning(f"⚠️ Server error (attempt {attempt + 1}), retrying...")
                time.sleep(5)
            else:
                log.error(f"❌ API error {response.status_code}: {response.text}")
                if attempt < max_retries - 1:
                    time.sleep(5)
                    
        except requests.exceptions.Timeout:
            log.warning(f"⚠️ LLM timeout (attempt {attempt + 1})")
            if attempt < max_retries - 1:
                time.sleep(5)
        except Exception as e:
            log.error(f"❌ LLM call failed (attempt {attempt + 1}): {e}")
            if attempt < max_retries - 1:
                time.sleep(5)
    
    log.error("❌ All LLM attempts failed")
    return None

def validate_caption(caption_text):
    """Validate and format caption to ensure 6 lines of 6 words each"""
    try:
        lines = [line.strip() for line in caption_text.split('\n') if line.strip()]
        
        # If we have exactly 6 lines, validate each
        if len(lines) == 6:
            validated_lines = []
            for line in lines:
                words = line.split()
                if len(words) == 6:
                    validated_lines.append(' '.join(words))
                else:
                    # Pad or truncate to 6 words
                    if len(words) < 6:
                        words.extend(['space'] * (6 - len(words)))
                    else:
                        words = words[:6]
                    validated_lines.append(' '.join(words))
            return '\n'.join(validated_lines)
        
        # If not 6 lines, create a simple 6x6 caption
        fallback_caption = [
            "Architecture speaks through silent spaces",
            "Form follows function in perfect harmony",
            "Light dances across geometric surfaces",
            "Human scale meets monumental vision",
            "Materials tell stories of creation",
            "Space becomes poetry in motion"
        ]
        return '\n'.join(fallback_caption)
        
    except Exception as e:
        log.warning(f"⚠️ Caption validation failed: {e}")
        return "Architecture speaks through silent spaces\n" * 6

# === 🧠 Enhanced Prompt Generation ===
def generate_prompts_and_captions(theme):
    """Generate optimized prompts and captions with better content quality"""
    try:
        # Enhanced prompt generation with context
        prompts_msg = [
            {
                "role": "system", 
                "content": """You are a visionary architectural artist and conceptual designer. You create compelling, artistic image prompts that capture the essence of architectural concepts with vivid, poetic language. Focus on:

1. **Visual Poetry**: Create prompts that evoke strong visual imagery
2. **Architectural Depth**: Incorporate spatial relationships, materials, and form
3. **Emotional Resonance**: Connect architecture to human experience
4. **Innovation**: Blend traditional and futuristic elements
5. **Atmospheric Quality**: Consider lighting, mood, and environmental context

Your prompts should be single, evocative sentences that describe architectural scenes with artistic flair."""
            },
            {
                "role": "user", 
                "content": f"""Generate exactly 1 architectural image prompt on theme: '{theme}'.

Requirements:
- Single, evocative sentence (20-40 words)
- Focus on visual impact and architectural poetry
- Include specific architectural elements (materials, forms, spaces)
- Consider lighting, atmosphere, and mood
- Blend innovation with timeless design principles

Theme Context: {theme}

Generate the prompt:"""
            }
        ]
        
        prompts_response = call_llm(prompts_msg)
        prompts = [line.strip() for line in prompts_response.split('\n') if line.strip()]
        
        # Ensure we have enough prompts
        if len(prompts) < 1:
            log.warning(f"⚠️ Only {len(prompts)} prompts generated, using fallback")
            prompts = [f"Architectural concept exploring {theme} with artistic vision and spatial poetry"]
        
        # Enhanced caption generation
        captions_msg = [
            {
                "role": "system", 
                "content": """You are a masterful architectural poet and critic. Create exactly 6 lines of exactly 6 words each that form a complete, meaningful caption for architectural imagery. Each line should be a complete thought with poetic depth. The entire caption should tell a coherent story that reveals the architectural philosophy, emotional impact, and cultural significance of the space.

Focus on:
1. **Spatial Poetry**: How space affects human experience
2. **Material Language**: The story of materials and construction
3. **Cultural Context**: Architecture's role in society
4. **Emotional Journey**: The feelings evoked by the space
5. **Philosophical Depth**: Deeper meaning of architectural choices
6. **Visual Narrative**: Telling a story through built form"""
            },
            {
                "role": "user", 
                "content": f"""Create a 6-line caption (6 words per line) for an architectural image about: {theme}

Each line must be exactly 6 words and form a complete thought. The caption should tell a story about the architectural concept, its meaning, and its impact on human experience.

Theme: {theme}

Generate the caption:"""
            }
        ]
        
        captions_response = call_llm(captions_msg)
        caption = validate_caption(captions_response)
        
        log.info(f"✅ Generated {len(prompts)} prompts and 1 caption")
        return prompts, [caption]  # Return list of captions for consistency
        
    except Exception as e:
        log.error(f"❌ Failed to generate prompts/captions: {e}")
        log.info("🔄 Using fallback prompts and captions")
        
        # Enhanced fallback prompts and captions
        fallback_prompts = [f"Architectural concept exploring {theme} with artistic vision and spatial poetry"]
        fallback_caption = "Architecture speaks through silent spaces\n" * 6
        
        return fallback_prompts, [fallback_caption]

# === 🎨 STEP 3: Generate images with different styles ===
# === 🎨 Image Generation ===
def generate_single_image(args):
    """Generate a single image with retry logic and memory optimization (TEST MODE - SKIPS REPLICATE)"""
    prompt, style_name, i, style_config = args
    
    log.info(f"🧪 TEST MODE: Simulating {style_name} image {i+1} generation")
    
    # Create directory structure
    style_dir = os.path.join("images", style_name)
    os.makedirs(style_dir, exist_ok=True)
    
    # Simulate image generation (skip Replicate API call)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    image_filename = f"{style_name}_image_{i+1:02d}_{timestamp}.jpg"
    image_path = os.path.join(style_dir, image_filename)
    
    # Create a dummy image file for testing
    try:
        # Create a simple test image using PIL
        from PIL import Image, ImageDraw, ImageFont
        import random
        
        # Create a test image with the style name and prompt
        img = Image.new('RGB', (IMAGE_WIDTH, IMAGE_HEIGHT), color=(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)))
        draw = ImageDraw.Draw(img)
        
        # Add text to the image
        try:
            # Try to use a default font
            font = ImageFont.load_default()
        except:
            font = None
        
        # Add style name and prompt info
        text_lines = [
            f"TEST IMAGE - {style_name.upper()}",
            f"Prompt: {prompt[:50]}...",
            f"Generated: {timestamp}",
            "REPLICATE SKIPPED FOR TESTING"
        ]
        
        y_position = 50
        for line in text_lines:
            if font:
                draw.text((50, y_position), line, fill=(255, 255, 255), font=font)
            else:
                draw.text((50, y_position), line, fill=(255, 255, 255))
            y_position += 30
        
        # Save the test image
        img.save(image_path, 'JPEG', quality=85)
        
        # Log image details
        image_log_file = os.path.join(style_dir, f"{style_name}_image_log.txt")
        with open(image_log_file, 'a', encoding='utf-8') as log_file:
            log_file.write(f"Image {i+1}: {image_filename}\n")
            log_file.write(f"Prompt: {prompt}\n")
            log_file.write(f"Full Prompt: {prompt}, {style_config['prompt_suffix']}\n")
            log_file.write(f"URL: TEST_MODE_NO_URL\n")
            log_file.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            log_file.write(f"File Size: {os.path.getsize(image_path)} bytes\n")
            log_file.write(f"Status: TEST_MODE_SIMULATED\n")
            log_file.write("-" * 80 + "\n")
        
        log.info(f"✅ TEST MODE: Generated {style_name} image {i+1}: {image_filename} ({os.path.getsize(image_path)} bytes)")
        return f"test_url_{image_filename}", image_path
        
    except Exception as e:
        log.error(f"❌ TEST MODE: Failed to create test image: {e}")
        return None, None

def generate_images_with_style(prompts, style_name):
    """Generate images for a specific style with parallel processing"""
    try:
        style_config = STYLE_MODELS.get(style_name)
        if not style_config:
            log.error(f"❌ Unknown style: {style_name}")
            return [], [], []
        
        log.info(f"🎨 Starting {style_name} image generation...")
        
        # Prepare arguments for parallel processing
        args_list = [(prompt, style_name, i, style_config) for i, prompt in enumerate(prompts)]
        
        # Generate images with parallel processing
        images = []
        image_paths = []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_CONCURRENT_IMAGES) as executor:
            future_to_prompt = {executor.submit(generate_single_image, args): args for args in args_list}
            
            for future in concurrent.futures.as_completed(future_to_prompt):
                args = future_to_prompt[future]
                try:
                    image_url, image_path = future.result()
                    if image_url and image_path:
                        images.append(image_url)
                        image_paths.append(image_path)
                except Exception as e:
                    log.error(f"❌ Failed to generate image for {args[1]}: {e}")
        
        log.info(f"✅ {style_name} generation complete: {len(images)}/{len(prompts)} images")
        return images, image_paths, prompts
        
    except Exception as e:
        log.error(f"❌ Failed to generate {style_name} images: {e}")
        return [], [], []

# === 🖼️ STEP 4: Place captions ===
def place_caption(c, cap, pos, w, h):
    text = cap.split('\n')
    font_size = int(get_env("CAPTION_FONT_SIZE", "14"))
    line_spacing = int(get_env("CAPTION_LINE_SPACING", "18"))
    
    c.setFont("Helvetica-Bold", font_size)
    c.setFillColorRGB(0, 0, 0)
    
    # Calculate total height of caption block
    total_height = len(text) * line_spacing
    
    if pos == "bottom":
        # Position at bottom with proper margins
        start_y = 60
        
        # Add subtle background for better readability
        c.setFillColorRGB(0.95, 0.95, 0.95)
        c.rect(30, start_y - 10, w - 60, total_height + 20, fill=1)
        c.setFillColorRGB(0, 0, 0)
        
        for i, line in enumerate(text):
            c.drawString(40, start_y + i * line_spacing, line)
    elif pos == "center":
        # Center the entire caption block
        start_y = (h + total_height) / 2
        for i, line in enumerate(text):
            c.drawCentredString(w / 2, start_y - i * line_spacing, line)
    elif pos == "top":
        # Position at top with proper margins
        start_y = h - 120
        for i, line in enumerate(text):
            c.drawString(40, start_y - i * line_spacing, line)
    elif pos == "top-right":
        # Position at top-right corner
        start_y = h - 120
        for i, line in enumerate(text):
            c.drawRightString(w - 40, start_y - i * line_spacing, line)
    elif pos == "top-left":
        # Position at top-left corner
        start_y = h - 120
        for i, line in enumerate(text):
            c.drawString(40, start_y - i * line_spacing, line)
    elif pos == "bottom-right":
        # Position at bottom-right corner
        start_y = 60
        for i, line in enumerate(text):
            c.drawRightString(w - 40, start_y + i * line_spacing, line)
    elif pos == "bottom-left":
        # Position at bottom-left corner
        start_y = 60
        for i, line in enumerate(text):
            c.drawString(40, start_y + i * line_spacing, line)
    elif pos == "left":
        # Position at left side, centered vertically
        start_y = (h + total_height) / 2
        for i, line in enumerate(text):
            c.drawString(40, start_y - i * line_spacing, line)
    elif pos == "right":
        # Position at right side, centered vertically
        start_y = (h + total_height) / 2
        for i, line in enumerate(text):
            c.drawRightString(w - 40, start_y - i * line_spacing, line)

# === 📄 STEP 5: Build PDF ===
def make_pdf(images, captions, theme, style_name):
    os.makedirs(OUTPUT_PATH, exist_ok=True)
    title = f"{TITLE_TEMPLATE.format(theme=theme)}_{style_name}".replace(" ", "_").replace(":", "_").replace("&", "and")
    fname = os.path.join(OUTPUT_PATH, f"{title}.pdf")
    c = canvas.Canvas(fname, pagesize=A4)
    w, h = A4
    
    # Create full bleed spreads (2 pages each)
    for i, (img_url, cap) in enumerate(zip(images, captions)):
        # Left page (full bleed)
        try:
            resp = requests.get(img_url)
            img = Image.open(BytesIO(resp.content))
            img.load()
            img.save("temp_img.jpg", dpi=(IMAGE_DPI, IMAGE_DPI))
            # Full bleed: extend image beyond page margins
            c.drawImage("temp_img.jpg", -20, -20, width=w+40, height=h+40)
        except Exception as e:
            log.warning(f"Couldn't render image: {e}")
        
        # Add caption to left page
        place_caption(c, cap, CAPTION_POSITION, w, h)
        c.showPage()
        
        # Right page (full bleed continuation)
        try:
            # Same image on right page for full bleed effect
            c.drawImage("temp_img.jpg", -20, -20, width=w+40, height=h+40)
        except Exception as e:
            log.warning(f"Couldn't render right page image: {e}")
        
        # Add caption to right page
        place_caption(c, cap, CAPTION_POSITION, w, h)
        c.showPage()
        
        log.info(f"Created {style_name} spread {i+1}/{len(images)} (pages {i*2+1}-{i*2+2})")
    
    c.save()
    log.info(f"PDF saved to: {fname} (20 pages total)")
    return fname

# === 🚀 MAIN RUN ===
def generate_images_for_style(theme, style_name):
    """Generate images for a specific style (no PDF creation)"""
    log.info(f"=== Generating {style_name.upper()} Style Images ===")
    
    try:
        # Generate prompts and captions
        prompts, captions = generate_prompts_and_captions(theme)
        log.info(f"Generated {len(prompts)} prompts and captions for {style_name} style")
        
        # Generate images with the specific style
        images, image_paths, prompts = generate_images_with_style(prompts, style_name)
        log.info(f"Generated {len(images)} images for {style_name} style")
        
        # Store captions for later use in weekly/monthly PDFs
        captions_file = os.path.join("captions", f"{style_name}_captions.txt")
        os.makedirs("captions", exist_ok=True)
        with open(captions_file, 'w', encoding='utf-8') as f:
            for i, caption in enumerate(captions):
                f.write(f"Image {i+1}: {caption}\n")
        
        log.info(f"✅ {style_name.upper()} images complete: {len(images)} images generated")
        
        return images, image_paths, captions
        
    except Exception as e:
        log.error(f"❌ Failed to generate {style_name} images: {e}")
        return None, None, None

def main():
    start_time = time.time()
    
    # Initialize web scraping if available
    if WEB_SCRAPING_AVAILABLE:
        log.info("🌐 Initializing web scraping...")
        try:
            scraper = WebScraper()
            scraper.run_daily_scraping()
            date_filter = DateFilter()
            log.info("✅ Web scraping completed")
        except Exception as e:
            log.error(f"❌ Web scraping failed: {e}")
            log.info("🔄 Falling back to RSS theme generation")
            theme = get_theme()
    else:
        theme = get_theme()
    
    # Get topics from web scraping or fallback
    if WEB_SCRAPING_AVAILABLE:
        try:
            # Get 10 unique topics for daily generation (10 social only, no daily PDF)
            topics = date_filter.get_unused_topics('daily', 10)
            if len(topics) >= 10:
                log.info(f"🎯 Using {len(topics)} scraped topics for daily generation")
                theme = topics[0]  # Use first topic as main theme
            else:
                log.warning(f"⚠️ Only {len(topics)} topics available, using fallback")
                theme = get_theme()
        except Exception as e:
            log.error(f"❌ Topic extraction failed: {e}")
            theme = get_theme()
    else:
        theme = get_theme()
    
    log.info(f"🎯 Theme selected: {theme}")
    
    # Generate 10 images daily (10 for PDF curation only, no daily PDF)
    # Distribute across 8 styles to ensure variety
    images_per_style = 10 // 8  # 1 image per style
    remaining_images = 10 % 8   # 2 extra images to distribute
    
    generated_images = []
    total_images_generated = 0
    
    log.info(f"🚀 Starting daily generation: 10 images across 8 styles for PDF curation...")
    
    style_names = list(STYLE_MODELS.keys())
    
    # Generate base images (1 per style)
    for i, style_name in enumerate(style_names):
        style_start_time = time.time()
        log.info(f"📊 Progress: {i+1}/8 - {style_name.upper()}")
        
        try:
            # Generate 1 image for this style
            images, image_paths, captions = generate_images_for_style(theme, style_name)
            if images and len(images) >= 1:
                generated_images.append((style_name, 1))
                total_images_generated += 1
                style_time = time.time() - style_start_time
                log.info(f"✅ {style_name.upper()} complete: 1 image in {style_time:.1f}s")
            else:
                log.error(f"❌ {style_name.upper()}: No images generated")
        except Exception as e:
            log.error(f"❌ Failed to generate {style_name} images: {e}")
            continue
    
    # Generate remaining 2 images (distribute across first 2 styles)
    for i in range(remaining_images):
        if i < len(style_names):
            style_name = style_names[i]
            style_start_time = time.time()
            log.info(f"📊 Extra image {i+1}/2 - {style_name.upper()}")
            
            try:
                # Generate 1 extra image for this style
                images, image_paths, captions = generate_images_for_style(theme, style_name)
                if images and len(images) >= 1:
                    # Update count for this style
                    for j, (existing_style, count) in enumerate(generated_images):
                        if existing_style == style_name:
                            generated_images[j] = (style_name, count + 1)
                            break
                    total_images_generated += 1
                    style_time = time.time() - style_start_time
                    log.info(f"✅ {style_name.upper()} extra image complete in {style_time:.1f}s")
                else:
                    log.error(f"❌ {style_name.upper()}: Extra image failed")
            except Exception as e:
                log.error(f"❌ Failed to generate extra {style_name} image: {e}")
                continue
    
    # Summary
    total_time = time.time() - start_time
    log.info(f"🎉 === DAILY PDF CURATION GENERATION COMPLETE ===")
    log.info(f"⏱️  Total time: {total_time:.1f} seconds")
    log.info(f"📊 Successfully generated images for {len(generated_images)}/8 styles:")
    
    for style_name, count in generated_images:
        log.info(f"✅ {style_name.upper()}: {count} images")
    
    if not generated_images:
        log.error("❌ No images were generated successfully")
    else:
        avg_time_per_image = total_time / total_images_generated if total_images_generated > 0 else 0
        log.info(f"🎉 Daily generation complete! {total_images_generated} total images.")
        log.info(f"📈 Average time per image: {avg_time_per_image:.1f}s")
        log.info(f"📁 Images saved to: images/")
        log.info(f"📝 Captions saved to: captions/")
        log.info(f"📄 10 images allocated for PDF curation (weekly/monthly/yearly)")
        log.info(f"📄 PDFs will be created by weekly/monthly/yearly curators")

if __name__ == "__main__":
    main() 