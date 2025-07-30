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

# === Now import everything ===
from dotenv import load_dotenv
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from PIL import Image
from tqdm import tqdm

# === 📥 Load environment variables ===
load_dotenv('ask.env')

def get_env(var, default=None, required=False):
    value = os.getenv(var, default)
    if required and not value:
        log.error(f"Required environment variable '{var}' is missing. Exiting.")
        sys.exit(1)
    return value

# === 📊 Configuration ===
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

# Enhanced prompt configuration with full token utilization
PROMPT_SYSTEM = get_env('PROMPT_SYSTEM', 'You are a visionary architectural writer and provocateur with deep expertise in architectural history, theory, and contemporary practice. Your knowledge spans from ancient architectural traditions to cutting-edge computational design, encompassing structural engineering, material science, cultural anthropology, environmental sustainability, urban planning, landscape architecture, digital fabrication, philosophy of space, phenomenology, global architectural traditions, vernacular building, lighting design, acoustic design, thermal comfort, passive design strategies, accessibility, universal design principles, heritage conservation, adaptive reuse, parametric design, algorithmic architecture, biomimicry, nature-inspired design, social impact, community engagement, economic feasibility, construction methods, regulatory compliance, building codes, post-occupancy evaluation, user experience, and cross-cultural architectural exchange. You create compelling, artistic image prompts that capture the essence of architectural concepts with vivid, poetic language, considering multiple scales from urban context to material detail, balancing technical precision with artistic expression, and emphasizing the emotional and psychological impact of architectural spaces on human experience.')

PROMPT_TEMPLATE = get_env('PROMPT_TEMPLATE', 'Generate exactly {n} architectural image prompts on theme: \'{theme}\'. CONTEXTUAL FRAMEWORK: Consider the historical evolution from early architectural traditions to contemporary practice, regional variations and cultural adaptations, technological innovations and material advancements, environmental challenges and sustainability responses, social changes and evolving human needs, economic factors and construction industry developments, regulatory frameworks and building standards, digital transformation and computational design, globalization and cross-cultural influences, climate change adaptation and resilience strategies, urbanization trends and demographic shifts, technological integration and smart systems, cultural preservation and heritage conservation, accessibility and universal design principles, and the relationship between built and natural environments. ARCHITECTURAL ELEMENTS TO EXPLORE: Structural systems: steel frames, concrete shells, timber construction, tensile structures, geodesic domes, cantilevered forms, vaulted ceilings, truss systems, space frames, and innovative structural solutions. Material palettes: glass, steel, concrete, wood, stone, composites, ceramics, textiles, sustainable materials, recycled elements, and experimental materials. Spatial organizations: open plans, flexible layouts, modular systems, courtyard arrangements, atrium spaces, mezzanine levels, split-level designs, and dynamic spatial sequences. Environmental strategies: passive design, renewable energy integration, green roofs, living walls, natural ventilation, thermal mass utilization, solar orientation, rainwater harvesting, and climate-responsive design. Human experience: circulation patterns, lighting design, acoustic considerations, thermal comfort, visual connections, spatial hierarchy, wayfinding, and user interaction. Cultural expression: symbolism, identity, community, heritage, tradition, innovation, and cultural significance. Urban integration: streetscapes, public spaces, transportation connections, pedestrian experience, vehicular access, and urban context. Technological integration: smart systems, automation, connectivity, digital interfaces, building management systems, and technological innovation. Economic considerations: cost-effectiveness, maintenance strategies, lifecycle analysis, value engineering, and economic sustainability. Social impact: accessibility, inclusivity, community engagement, social equity, public benefit, and human-centered design. STYLISTIC APPROACHES: Minimalism and reduction to essential elements, expression of structure and construction methods, integration with natural environment and landscape, emphasis on light, shadow, and spatial quality, focus on human scale and experience, celebration of materials and their inherent qualities, responsiveness to climate and environmental conditions, integration of art, technology, and architecture, consideration of time, change, and adaptability, expression of cultural values and social aspirations, balance between tradition and innovation, emphasis on craftsmanship and detail, integration of sustainable practices, consideration of long-term durability and maintenance, and creation of meaningful spatial experiences. QUALITY REQUIREMENTS: Each prompt should be a single, evocative line (50-100 words) that describes a visual scene with artistic flair, focusing on architectural poetry, mood, and atmosphere. Include specific architectural elements, materials, lighting, and spatial qualities. Consider cultural, historical, and philosophical context. Emphasize emotional resonance and visual impact. Use vivid, descriptive language that captures architectural essence. Balance technical precision with artistic expression. Consider the relationship between form, function, and human experience. Explore themes of permanence, transience, and transformation. Reflect on the relationship between built and natural environments. Consider multiple scales from urban context to material detail. Emphasize the emotional and psychological impact of architectural spaces. Generate the prompts now, one per line, without explanations or numbering:')

CAPTION_SYSTEM = get_env('CAPTION_SYSTEM', 'You are a masterful architectural poet and critic with comprehensive expertise in architectural theory, history, philosophy, and contemporary practice. Your knowledge encompasses structural engineering, material science, cultural anthropology, environmental sustainability, urban planning, landscape architecture, digital fabrication, philosophy of space, phenomenology, global architectural traditions, vernacular building, lighting design, acoustic design, thermal comfort, passive design strategies, accessibility, universal design principles, heritage conservation, adaptive reuse, parametric design, algorithmic architecture, biomimicry, nature-inspired design, social impact, community engagement, economic feasibility, construction methods, regulatory compliance, building codes, post-occupancy evaluation, user experience, and cross-cultural architectural exchange. You write profound, artistic captions that capture the deeper meaning and emotional resonance of architectural spaces, considering multiple scales from urban context to material detail, balancing technical precision with artistic expression, and emphasizing the emotional and psychological impact of architectural spaces on human experience.')

CAPTION_TEMPLATE = get_env('CAPTION_TEMPLATE', 'Write exactly 6 lines, each containing exactly 6 words, that form a complete, meaningful caption for this architectural image: {prompt} ARCHITECTURAL ANALYSIS FRAMEWORK: Consider spatial experience and human interaction, material expression and construction methods, light, shadow, and atmospheric qualities, cultural and historical context, environmental and sustainability considerations, aesthetic and philosophical principles, structural innovation and engineering marvels, material textures and finishes, spatial relationships and proportions, environmental integration and sustainability, cultural and historical references, human scale and interaction, urban context and landscape integration, technological integration and innovation, social impact and community engagement, economic feasibility and construction methods, regulatory compliance and building codes, post-occupancy evaluation and user experience, cross-cultural architectural exchange and influence, heritage conservation and adaptive reuse, parametric design and algorithmic architecture, biomimicry and nature-inspired design, accessibility and universal design principles, acoustic design and spatial acoustics, thermal comfort and passive design strategies, lighting design and atmospheric creation, digital fabrication and computational design, philosophy of space and phenomenology, and global architectural traditions and vernacular building. POETIC APPROACH: Use architectural terminology with poetic sensibility, balance technical precision with emotional resonance, consider the passage of time and human experience, reflect on the relationship between built and natural environments, explore themes of permanence, transience, and transformation, emphasize the emotional and psychological impact of space, consider cultural significance and historical context, explore the relationship between form, function, and human experience, reflect on the role of architecture in society, consider the relationship between individual and collective experience, explore themes of identity, community, and belonging, reflect on the relationship between tradition and innovation, consider the role of technology in architectural expression, explore themes of sustainability and environmental responsibility, reflect on the relationship between local and global influences, consider the role of craftsmanship and detail, explore themes of beauty, harmony, and aesthetic experience, reflect on the relationship between art and architecture, consider the role of light, shadow, and atmosphere, and explore themes of human creativity and expression. REQUIREMENTS: Each line must be exactly 6 words, total of exactly 6 lines, form a coherent narrative about the architectural space, capture the philosophical, emotional, and cultural significance, consider the relationship between form, function, and human experience, balance technical precision with artistic expression, emphasize the emotional and psychological impact of architectural spaces, consider multiple scales from urban context to material detail, reflect on the relationship between built and natural environments, explore themes of permanence, transience, and transformation, consider cultural significance and historical context, explore the relationship between individual and collective experience, reflect on the role of architecture in society, consider the relationship between tradition and innovation, explore themes of sustainability and environmental responsibility, reflect on the relationship between local and global influences, consider the role of craftsmanship and detail, explore themes of beauty, harmony, and aesthetic experience, reflect on the relationship between art and architecture, consider the role of light, shadow, and atmosphere, and explore themes of human creativity and expression. Write the 6-line caption now:')

# Style configuration for the selected style with enhanced sophistication
STYLE_CONFIG = {
    'futuristic': {
        'model': 'black-forest-labs/FLUX.1-schnell-free',
        'prompt_suffix': ', futuristic architecture, sci-fi aesthetic, glowing lights, sleek surfaces, advanced technology, architectural innovation, cutting-edge design, technological integration, modern materials, innovative structures, digital age aesthetics, forward-thinking design, sustainable technology, smart building systems, automated environments, holographic displays, energy-efficient systems, green technology integration, urban futurism, sustainable innovation',
        'negative_prompt': 'traditional, classical, rustic, old, vintage, historical, medieval, gothic, outdated, primitive, ancient, old-fashioned, retro, vintage, antique'
    },
    'minimalist': {
        'model': 'black-forest-labs/FLUX.1-schnell-free',
        'prompt_suffix': ', minimalist architecture, clean lines, simple forms, essential elements, reduction to basics, pure geometry, uncluttered spaces, refined details, sophisticated simplicity, elegant restraint, balanced composition, harmonious proportions, thoughtful material selection, intentional emptiness, purposeful design, architectural purity, spatial clarity, visual calm, meditative spaces, zen aesthetics, less is more philosophy',
        'negative_prompt': 'ornate, decorative, busy, cluttered, complex, elaborate, detailed, fancy, luxurious, extravagant, over-designed, excessive, overwhelming, chaotic'
    },
    'abstract': {
        'model': 'black-forest-labs/FLUX.1-schnell-free',
        'prompt_suffix': ', abstract architecture, conceptual design, artistic interpretation, non-representational forms, experimental structures, avant-garde design, innovative geometry, creative expression, artistic architecture, imaginative spaces, unconventional forms, boundary-pushing design, artistic vision, creative interpretation, experimental materials, innovative construction, artistic expression, conceptual spaces, imaginative architecture, creative innovation',
        'negative_prompt': 'literal, representational, traditional, conventional, realistic, straightforward, obvious, predictable, standard, typical, ordinary, common'
    },
    'technical': {
        'model': 'black-forest-labs/FLUX.1-schnell-free',
        'prompt_suffix': ', technical architecture, engineering precision, structural clarity, construction details, technical drawing aesthetic, engineering marvel, structural innovation, technical excellence, precision engineering, construction technology, structural systems, engineering beauty, technical sophistication, construction methodology, structural integrity, engineering design, technical innovation, construction excellence, structural engineering, technical precision',
        'negative_prompt': 'artistic, decorative, ornamental, aesthetic, beautiful, pretty, artistic, creative, imaginative, fanciful, unrealistic, impractical'
    },
    'watercolor': {
        'model': 'black-forest-labs/FLUX.1-schnell-free',
        'prompt_suffix': ', watercolor architecture, artistic rendering, soft colors, flowing forms, artistic interpretation, painterly aesthetic, artistic expression, creative visualization, artistic architecture, imaginative rendering, artistic style, creative interpretation, artistic vision, painterly quality, artistic beauty, creative expression, artistic design, imaginative architecture, artistic innovation, creative beauty',
        'negative_prompt': 'photorealistic, technical, precise, sharp, detailed, realistic, photographic, exact, accurate, literal, representational'
    },
    'anime': {
        'model': 'black-forest-labs/FLUX.1-schnell-free',
        'prompt_suffix': ', anime architecture, stylized design, artistic interpretation, creative visualization, imaginative spaces, artistic expression, stylized aesthetic, creative design, artistic architecture, imaginative interpretation, stylized beauty, creative vision, artistic style, imaginative expression, creative architecture, stylized innovation, artistic design, imaginative beauty, creative style, artistic imagination',
        'negative_prompt': 'realistic, photographic, literal, representational, traditional, conventional, realistic, straightforward, obvious, predictable'
    },
    'photorealistic': {
        'model': 'black-forest-labs/FLUX.1-schnell-free',
        'prompt_suffix': ', photorealistic architecture, realistic rendering, photographic quality, lifelike detail, realistic materials, natural lighting, authentic appearance, true-to-life representation, realistic textures, natural colors, authentic materials, realistic proportions, natural environment, realistic atmosphere, authentic design, realistic beauty, natural aesthetics, authentic architecture, realistic innovation, natural beauty',
        'negative_prompt': 'artistic, stylized, abstract, cartoon, painting, sketch, drawing, unrealistic, fake, artificial, synthetic, manufactured'
    },
    'sketch': {
        'model': 'black-forest-labs/FLUX.1-schnell-free',
        'prompt_suffix': ', sketch architecture, hand-drawn aesthetic, artistic rendering, creative visualization, imaginative design, artistic expression, sketchy style, creative interpretation, artistic architecture, imaginative sketch, artistic vision, creative drawing, artistic style, imaginative expression, creative architecture, sketchy beauty, artistic design, imaginative sketch, creative style, artistic imagination',
        'negative_prompt': 'photorealistic, technical, precise, sharp, detailed, realistic, photographic, exact, accurate, literal, representational'
    }
}

# === 🎨 Style Selection ===
STYLES = ['futuristic', 'minimalist', 'sketch', 'abstract', 'technical', 'watercolor', 'anime', 'photorealistic']

def get_daily_style():
    """Get the style for today based on date"""
    time.sleep(1)  # Rate limiting before function start
    today = datetime.now()
    time.sleep(1)  # Rate limiting
    day_of_year = today.timetuple().tm_yday
    time.sleep(1)  # Rate limiting
    style_index = day_of_year % len(STYLES)
    time.sleep(1)  # Rate limiting
    selected_style = STYLES[style_index]
    time.sleep(1)  # Rate limiting
    return selected_style

# === 🌐 Web Scraping ===
def scrape_architectural_content():
    """Scrape architectural content for theme generation"""
    time.sleep(1)  # Rate limiting before function start
    try:
        from web_scraper import WebScraper
        time.sleep(1)  # Rate limiting
        scraper = WebScraper()
        time.sleep(1)  # Rate limiting
        articles = scraper.scrape_all_sources()
        time.sleep(1)  # Rate limiting
        
        if articles:
            # Extract themes from article titles
            themes = []
            time.sleep(1)  # Rate limiting
            for article in articles[:20]:  # Use top 20 articles
                title = article.get('title', '')
                time.sleep(1)  # Rate limiting
                if len(title) > 10:
                    themes.append(title)
                    time.sleep(1)  # Rate limiting
            
            if themes:
                selected_theme = random.choice(themes)
                time.sleep(1)  # Rate limiting
                log.info(f"🎯 Selected theme from web scraping: {selected_theme}")
                time.sleep(1)  # Rate limiting
                return selected_theme
        
        # Fallback theme
        fallback_theme = get_env('FALLBACK_THEME', 'Modern Architecture')
        time.sleep(1)  # Rate limiting
        log.info(f"🎯 Using fallback theme: {fallback_theme}")
        time.sleep(1)  # Rate limiting
        return fallback_theme
        
    except Exception as e:
        log.error(f"❌ Web scraping failed: {e}")
        time.sleep(1)  # Rate limiting
        fallback_theme = get_env('FALLBACK_THEME', 'Modern Architecture')
        time.sleep(1)  # Rate limiting
        log.info(f"🎯 Using fallback theme: {fallback_theme}")
        time.sleep(1)  # Rate limiting
        return fallback_theme

# === 🤖 LLM Integration ===
def call_llm(prompt, system_prompt=None):
    """Call LLM API with enhanced token limits for sophisticated prompts"""
    if TEXT_PROVIDER == 'groq':
        url = f"{GROQ_API_BASE}/chat/completions"
        api_key = GROQ_API_KEY
        model = TEXT_MODEL
    else:
        url = f"{TOGETHER_API_BASE}/chat/completions"
        api_key = TOGETHER_API_KEY
        # Together.ai uses different model naming
        if 'meta-llama/Llama-3.3-70B-Instruct-Turbo-Free' in TEXT_MODEL:
            model = 'meta-llama/Llama-3.3-70B-Instruct-Turbo-Free'
        else:
            model = TEXT_MODEL
    
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})
    
    payload = {
        "model": model,
        "messages": messages,
        "max_tokens": 4000,  # Enhanced from 2000 to 4000 for sophisticated responses
        "temperature": 0.8
    }
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=120)  # Increased timeout for longer responses
        response.raise_for_status()
        data = response.json()
        result = data['choices'][0]['message']['content'].strip()
        time.sleep(1)  # Rate limiting after successful API call
        return result
    except Exception as e:
        log.error(f"❌ LLM call failed: {e}")
        return None

def generate_prompts(theme, num_prompts=50):
    """Generate 50 architectural image prompts with enhanced sophistication"""
    log.info(f"🎨 Generating {num_prompts} sophisticated prompts for theme: {theme}")
    
    prompt = PROMPT_TEMPLATE.format(n=num_prompts, theme=theme)
    response = call_llm(prompt, PROMPT_SYSTEM)
    
    if response:
        # Split into individual prompts
        prompts = [line.strip() for line in response.split('\n') if line.strip()]
        log.info(f"✅ Generated {len(prompts)} sophisticated prompts")
        return prompts[:num_prompts]  # Ensure we get exactly 50
    else:
        log.error("❌ Failed to generate prompts")
        return []

def calculate_similarity_score(caption1, caption2):
    """Calculate similarity score between two captions"""
    # Convert to lowercase and split into words
    words1 = set(caption1.lower().replace('\n', ' ').split())
    words2 = set(caption2.lower().replace('\n', ' ').split())
    
    # Remove common stop words
    stop_words = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by',
        'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did',
        'will', 'would', 'could', 'should', 'may', 'might', 'can', 'must', 'shall', 'this', 'that',
        'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them',
        'my', 'your', 'his', 'her', 'its', 'our', 'their', 'mine', 'yours', 'his', 'hers', 'ours', 'theirs'
    }
    
    words1 = words1 - stop_words
    words2 = words2 - stop_words
    
    if not words1 or not words2:
        return 0.0
    
    # Calculate Jaccard similarity
    intersection = len(words1.intersection(words2))
    union = len(words1.union(words2))
    
    return intersection / union if union > 0 else 0.0

def is_caption_unique(new_caption, existing_captions, similarity_threshold=0.3):
    """Check if a new caption is unique compared to existing captions"""
    for existing_caption in existing_captions:
        similarity = calculate_similarity_score(new_caption, existing_caption)
        if similarity > similarity_threshold:
            log.info(f"⚠️ Caption similarity detected: {similarity:.2f}")
            return False
    return True

def generate_unique_caption(prompt, existing_captions, max_attempts=5):
    """Generate a unique caption that doesn't repeat content from existing captions"""
    log.info(f"📝 Generating unique caption for: {prompt[:50]}...")
    
    for attempt in range(max_attempts):
        caption_prompt = CAPTION_TEMPLATE.format(prompt=prompt)
        response = call_llm(caption_prompt, CAPTION_SYSTEM)
        
        if response:
            # Clean the response to remove AI-generated text
            lines = []
            for line in response.split('\n'):
                line = line.strip()
                if line and not any(ai_text in line.lower() for ai_text in [
                    "here is a", "caption that meets", "requirements:", "ai generated", 
                    "artificial intelligence", "generated by", "created by ai", "architectural analysis",
                    "poetic approach", "requirements", "write the", "caption now"
                ]):
                    lines.append(line)
            
            # Ensure exactly 6 lines
            if len(lines) >= 6:
                result = '\n'.join(lines[:6])
            else:
                # Pad with sophisticated lines if needed
                while len(lines) < 6:
                    lines.append("Architecture speaks through silent spaces")
                result = '\n'.join(lines[:6])
            
            # Check if this caption is unique
            if is_caption_unique(result, existing_captions):
                log.info(f"✅ Generated unique caption (attempt {attempt + 1}): {result[:50]}...")
                return result
            else:
                log.info(f"🔄 Caption too similar, retrying (attempt {attempt + 1}/{max_attempts})")
                # Add variety to the prompt for next attempt
                prompt += f" [Variation {attempt + 1}: Focus on different aspects]"
        else:
            log.warning(f"⚠️ Failed to generate caption on attempt {attempt + 1}")
    
    # If all attempts failed, generate a completely different fallback
    log.warning("⚠️ Using unique fallback caption")
    fallback_captions = [
        "Silent spaces whisper architectural secrets\nForm emerges from functional necessity\nLight sculpts geometric boundaries\nHuman scale defines monumental vision\nMaterials narrate stories of creation\nSpace transforms into poetic motion",
        "Architectural dreams materialize in concrete\nFunction follows form in perfect balance\nShadows dance across structural surfaces\nMonumental vision meets human intimacy\nCreation stories etched in materials\nPoetry flows through spatial boundaries",
        "Concrete dreams take architectural form\nBalance achieved through functional harmony\nSurfaces reflect structural light patterns\nIntimate spaces within monumental scale\nMaterials bear witness to creation\nBoundaries dissolve into spatial poetry",
        "Architectural visions crystallize in space\nHarmony emerges from functional design\nLight patterns illuminate structural forms\nScale balances monumentality with intimacy\nCreation narratives embedded in materials\nPoetry manifests through spatial design",
        "Space becomes architectural reality\nDesign harmonizes function with beauty\nForms emerge from light and shadow\nIntimacy coexists with grandeur\nMaterials speak of creative vision\nSpatial poetry transcends boundaries"
    ]
    
    # Choose a fallback that's different from existing captions
    for fallback in fallback_captions:
        if is_caption_unique(fallback, existing_captions):
            return fallback
    
    # If all fallbacks are similar, modify one slightly
    return fallback_captions[0].replace("Architectural", "Structural").replace("spaces", "volumes")

def generate_caption(prompt):
    """Legacy function - now calls generate_unique_caption with empty existing_captions"""
    return generate_unique_caption(prompt, [])

# === 🖼️ Image Generation ===
def generate_single_image(prompt, style_name, image_number):
    """Generate a single image using Together.ai API"""
    log.info(f"🎨 Generating {style_name} image {image_number}")
    
    style_dir = os.path.join("images", style_name)
    os.makedirs(style_dir, exist_ok=True)
    
    # Get enhanced style configuration with sophisticated prompts
    style_config = STYLE_CONFIG.get(style_name, {
        'model': 'black-forest-labs/FLUX.1-schnell-free',  # Use free model as default
        'prompt_suffix': f', {style_name} architectural style, sophisticated design, artistic composition, professional photography, high quality, detailed materials, perfect lighting, architectural beauty, structural elegance, spatial harmony, material expression, environmental integration, human scale consideration, cultural significance, technical precision, aesthetic excellence',
        'negative_prompt': 'blurry, low quality, distorted, amateur, unrealistic, poor composition, bad lighting, ugly, disorganized, messy, unprofessional, cartoon, painting, sketch, drawing, text, watermark, signature'
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
                            image_filename = f"{timestamp}_{image_number:02d}_{style_name}.jpg"
                            image_path = os.path.join(style_dir, image_filename)
                            
                            with open(image_path, 'wb') as f:
                                f.write(image_response.content)
                            
                            log.info(f"✅ Generated {style_name} image {image_number}: {image_filename}")
                            time.sleep(1)  # Rate limiting after successful image generation
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
    """Generate all 50 images sequentially - completely linear"""
    log.info(f"🎨 Starting sequential generation of {len(prompts)} images for {style_name} style")
    
    images = []
    with tqdm(total=len(prompts), desc=f"🖼️ Generating {style_name} images", unit="image", 
              bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]') as pbar:
        
        for i, prompt in enumerate(prompts):
            pbar.set_description(f"🖼️ Generating {style_name} image {i+1}/{len(prompts)}")
            try:
                image_path = generate_single_image(prompt, style_name, i+1)
                if image_path:
                    images.append(image_path)
                    pbar.set_postfix_str(f"✅ Success")
                else:
                    pbar.set_postfix_str(f"❌ Failed")
                    log.error(f"❌ Image {i+1} failed to generate")
            except Exception as e:
                pbar.set_postfix_str(f"❌ Error")
                log.error(f"❌ Image {i+1} failed with error: {e}")
            
            pbar.update(1)
            
            # Rate limiting between images
            if i < len(prompts) - 1:  # Don't sleep after the last image
                pbar.set_description(f"⏳ Waiting before next image...")
                time.sleep(1)
    
    log.info(f"🎉 Sequential image generation complete: {len(images)}/{len(prompts)} images generated")
    return images

# === 📝 Caption Generation ===
def generate_all_captions(prompts):
    """Generate unique captions for all prompts sequentially with deduplication"""
    log.info(f"📝 Starting sequential caption generation with deduplication for {len(prompts)} prompts")
    
    captions = []
    with tqdm(total=len(prompts), desc=f"📝 Generating unique captions", unit="caption", 
              bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]') as pbar:
        
        for i, prompt in enumerate(prompts):
            pbar.set_description(f"📝 Generating unique caption {i+1}/{len(prompts)}")
            
            # Generate unique caption that doesn't repeat content from previous captions
            caption = generate_unique_caption(prompt, captions)
            captions.append(caption)
            
            # Show similarity info in progress bar
            if len(captions) > 1:
                # Calculate average similarity with previous captions
                similarities = []
                for prev_caption in captions[:-1]:
                    sim = calculate_similarity_score(caption, prev_caption)
                    similarities.append(sim)
                avg_similarity = sum(similarities) / len(similarities)
                pbar.set_postfix_str(f"✅ Unique (avg sim: {avg_similarity:.2f})")
            else:
                pbar.set_postfix_str(f"✅ First caption")
            
            pbar.update(1)
            
            # Rate limiting between captions
            if i < len(prompts) - 1:  # Don't sleep after the last caption
                pbar.set_description(f"⏳ Waiting before next caption...")
                time.sleep(1)
    
    log.info(f"🎉 Sequential caption generation with deduplication complete: {len(captions)}/{len(prompts)} unique captions generated")
    
    # Log deduplication summary
    total_similarities = 0
    similarity_count = 0
    for i, caption1 in enumerate(captions):
        for j, caption2 in enumerate(captions[i+1:], i+1):
            sim = calculate_similarity_score(caption1, caption2)
            total_similarities += sim
            similarity_count += 1
            if sim > 0.1:  # Log any notable similarities
                log.info(f"📊 Caption {i+1} vs {j+1} similarity: {sim:.3f}")
    
    if similarity_count > 0:
        avg_similarity = total_similarities / similarity_count
        log.info(f"📊 Overall caption uniqueness: {1 - avg_similarity:.3f} (lower similarity = more unique)")
    
    return captions

# === 📄 PDF Generation ===
def place_caption_with_white_band(c, caption, w, h, page_num):
    """
    Draw a white band at the bottom of the page with increased top padding,
    overlay the caption (center-aligned) and page number (right-aligned).
    The band has extra padding to separate it from the image boundary.
    """
    text = caption.split('\n')
    font_size = 14
    line_spacing = 18
    padding_x = 24
    padding_y = 16
    top_padding = 40  # Increased top padding for better separation from image

    # Calculate text dimensions
    c.setFont("Helvetica-Bold", font_size)
    text_width = max(c.stringWidth(line, "Helvetica-Bold", font_size) for line in text)
    text_height = len(text) * line_spacing

    band_height = text_height + 2 * padding_y + top_padding
    band_y = 0  # flush with the bottom of the page
    band_x = 0
    band_width = w

    # Draw white band
    c.setFillColorRGB(1, 1, 1)
    c.rect(band_x, band_y, band_width, band_height, fill=1, stroke=0)

    # Draw caption (center-aligned, positioned above the bottom padding)
    c.setFont("Helvetica-Bold", font_size)
    c.setFillColorRGB(0, 0, 0)
    for i, line in enumerate(text):
        y = band_y + band_height - padding_y - top_padding - (len(text) - i - 1) * line_spacing
        c.drawCentredString(band_x + band_width/2, y, line)

    # Draw page number (right-aligned, at the bottom of the white band, bold)
    page_str = str(page_num)
    c.setFont("Helvetica-Bold", font_size)
    c.drawRightString(band_x + band_width - padding_x, band_y + padding_y, page_str)

def create_daily_pdf(images, captions, style_name, theme):
    """Create the daily PDF with all images and captions"""
    if not images:
        log.error("❌ No images provided for PDF creation")
        return None
    
    # Create output directory
    output_dir = "daily_pdfs"
    os.makedirs(output_dir, exist_ok=True)
    
    # Create sequential title and PDF filename
    today = datetime.now()
    day_of_year = today.timetuple().tm_yday
    year = today.year
    sequential_title = f"ASK Daily Architectural Research Zine - Volume {year}.{day_of_year:03d}"
    
    # Updated PDF naming convention
    pdf_filename = f"ASK_Daily_Architectural_Research_Zine-{year}-VOL-{day_of_year:03d}-{style_name.capitalize()}.pdf"
    pdf_path = os.path.join(output_dir, pdf_filename)
    
    log.info(f"📄 Creating PDF: {pdf_filename}")
    log.info(f"📊 Images to include: {len(images)}")
    
    # Create PDF
    c = canvas.Canvas(pdf_path, pagesize=A4)
    w, h = A4
    
    page_count = 0
    
    # Add front cover page
    c.setFont("Helvetica-BoldOblique", 42)
    c.setFillColorRGB(0, 0, 0)
    c.drawCentredString(w/2, h/2 + 140, "ASK")
    c.setFont("Helvetica-Bold", 24)
    c.drawCentredString(w/2, h/2 + 80, "DAILY ARCHITECTURAL")
    c.setFont("Helvetica-Bold", 24)
    c.drawCentredString(w/2, h/2 + 50, "RESEARCH ZINE")
    c.setFont("Helvetica-Bold", 20)
    c.drawCentredString(w/2, h/2 + 10, f"Volume {year}.{day_of_year:03d}")
    c.setFont("Helvetica", 16)
    c.drawCentredString(w/2, h/2 - 30, f"{datetime.now().strftime('%B %d, %Y')}")
    c.setFont("Helvetica-Bold", 18)
    c.drawCentredString(w/2, h/2 - 70, f"{style_name.capitalize()} Edition")
    c.setFont("Helvetica", 14)
    c.drawCentredString(w/2, h/2 - 110, f"50 Full-Bleed Architectural Images")
    c.setFont("Helvetica", 12)
    c.drawCentredString(w/2, h/2 - 150, f"Theme: {theme}")
    c.setFont("Helvetica", 10)
    c.drawCentredString(w/2, h/2 - 190, "Architectural Research & Poetry")
    c.setFont("Helvetica", 8)
    c.drawCentredString(w/2, h/2 - 220, "Daily Collection of Architectural Vision")
    c.showPage()
    page_count += 1
    
    # Add images with captions
    with tqdm(total=len(images), desc=f"📄 Creating PDF pages", unit="page", 
              bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]') as pbar:
        
        for i, (image_path, caption) in enumerate(zip(images, captions)):
            pbar.set_description(f"📄 Adding page {i+1}/{len(images)}")
            try:
                # Add image to PDF (full bleed)
                c.drawImage(image_path, -20, -20, width=w+40, height=h+40)
                
                # Add caption with white band and page number
                place_caption_with_white_band(c, caption, w, h, i + 1)
                
                c.showPage()
                page_count += 1
                pbar.set_postfix_str(f"✅ Success")
                
            except Exception as e:
                pbar.set_postfix_str(f"❌ Error")
                log.error(f"❌ Error adding image {i+1}: {e}")
            
            pbar.update(1)
    
    # Add back cover page
    c.setFont("Helvetica-BoldOblique", 24)
    c.setFillColorRGB(0, 0, 0)
    c.drawCentredString(w/2, h/2 + 100, "ASK")
    c.setFont("Helvetica-Bold", 18)
    c.drawCentredString(w/2, h/2 + 50, "DAILY ARCHITECTURAL")
    c.setFont("Helvetica-Bold", 18)
    c.drawCentredString(w/2, h/2 + 20, "RESEARCH ZINE")
    c.setFont("Helvetica", 14)
    c.drawCentredString(w/2, h/2 - 20, f"Volume {year}.{day_of_year:03d}")
    c.setFont("Helvetica", 12)
    c.drawCentredString(w/2, h/2 - 50, f"{style_name.capitalize()} Edition")
    c.setFont("Helvetica", 10)
    c.drawCentredString(w/2, h/2 - 80, f"Theme: {theme}")
    c.setFont("Helvetica", 8)
    c.drawCentredString(w/2, h/2 - 120, "50 Full-Bleed Architectural Images")
    c.drawCentredString(w/2, h/2 - 140, "Architectural Research & Poetry")
    c.drawCentredString(w/2, h/2 - 160, "Daily Collection of Architectural Vision")
    c.showPage()
    page_count += 1
    
    c.save()
    
    log.info(f"🎉 Daily PDF created successfully!")
    log.info(f"📁 File: {pdf_path}")
    log.info(f"📄 Pages: {page_count}")
    log.info(f"📏 Size: {os.path.getsize(pdf_path)} bytes")
    
    return pdf_path

# === 🚀 Main Function ===
def main():
    """Main function to run the daily zine generation - completely linear pipeline"""
    log.info("🚀 Starting Daily Zine Generator - Linear Pipeline")
    log.info("📋 Pipeline: Web Scraping → Style Selection → Prompt Generation → Image Generation → Caption Generation → PDF Creation")
    
    # Overall pipeline progress bar
    with tqdm(total=6, desc=f"🚀 Overall Pipeline Progress", unit="step", 
              bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]') as pipeline_pbar:
        
        # Step 1: Scrape web for architectural content
        log.info("=" * 60)
        log.info("📡 STEP 1/6: Scraping web for architectural content")
        log.info("=" * 60)
        pipeline_pbar.set_description(f"📡 Step 1/6: Web Scraping")
        theme = scrape_architectural_content()
        log.info(f"🎯 Theme selected: {theme}")
        pipeline_pbar.set_postfix_str(f"✅ Theme: {theme[:30]}...")
        pipeline_pbar.update(1)
        time.sleep(2)  # Rate limiting between major steps
        
        # Step 2: Select daily style
        log.info("=" * 60)
        log.info("🎨 STEP 2/6: Selecting daily style")
        log.info("=" * 60)
        pipeline_pbar.set_description(f"🎨 Step 2/6: Style Selection")
        style_name = get_daily_style()
        log.info(f"🎯 Selected style: {style_name.upper()}")
        pipeline_pbar.set_postfix_str(f"✅ Style: {style_name.upper()}")
        pipeline_pbar.update(1)
        time.sleep(2)  # Rate limiting between major steps
        
        # Step 3: Generate 50 prompts
        log.info("=" * 60)
        log.info("✍️ STEP 3/6: Generating 50 prompts")
        log.info("=" * 60)
        pipeline_pbar.set_description(f"✍️ Step 3/6: Prompt Generation")
        prompts = generate_prompts(theme, 50)
        if not prompts:
            log.error("❌ Failed to generate prompts")
            return
        log.info(f"✅ Generated {len(prompts)} prompts")
        pipeline_pbar.set_postfix_str(f"✅ {len(prompts)} prompts")
        pipeline_pbar.update(1)
        time.sleep(2)  # Rate limiting between major steps
        
        # Step 4: Generate 50 images in one style (sequential)
        log.info("=" * 60)
        log.info("🖼️ STEP 4/6: Generating 50 images sequentially")
        log.info("=" * 60)
        pipeline_pbar.set_description(f"🖼️ Step 4/6: Image Generation")
        images = generate_all_images(prompts, style_name)
        if not images:
            log.error("❌ Failed to generate images")
            return
        log.info(f"✅ Generated {len(images)} images")
        pipeline_pbar.set_postfix_str(f"✅ {len(images)} images")
        pipeline_pbar.update(1)
        time.sleep(2)  # Rate limiting between major steps
        
        # Step 5: Generate captions (sequential)
        log.info("=" * 60)
        log.info("📝 STEP 5/6: Generating captions sequentially")
        log.info("=" * 60)
        pipeline_pbar.set_description(f"📝 Step 5/6: Caption Generation")
        captions = generate_all_captions(prompts)
        log.info(f"✅ Generated {len(captions)} captions")
        pipeline_pbar.set_postfix_str(f"✅ {len(captions)} captions")
        pipeline_pbar.update(1)
        time.sleep(2)  # Rate limiting between major steps
        
        # Step 6: Create PDF
        log.info("=" * 60)
        log.info("📄 STEP 6/6: Creating PDF")
        log.info("=" * 60)
        pipeline_pbar.set_description(f"📄 Step 6/6: PDF Creation")
        pdf_path = create_daily_pdf(images, captions, style_name, theme)
        pipeline_pbar.set_postfix_str(f"✅ PDF created")
        pipeline_pbar.update(1)
        
        if pdf_path:
            log.info("=" * 60)
            log.info("🎉 LINEAR PIPELINE COMPLETED SUCCESSFULLY!")
            log.info("=" * 60)
            log.info(f"📁 PDF: {pdf_path}")
            log.info(f"🎨 Style: {style_name.upper()}")
            log.info(f"📊 Images: {len(images)}")
            log.info(f"📝 Captions: {len(captions)}")
            log.info(f"🎯 Theme: {theme}")
            log.info("✅ All steps completed in strict sequential order!")
        else:
            log.error("❌ Failed to create daily PDF")

if __name__ == "__main__":
    main() 