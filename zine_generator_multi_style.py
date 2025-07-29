import os
import sys
import subprocess
import logging
import time
from datetime import datetime
import concurrent.futures
import threading
from queue import Queue
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)
log_filename = os.path.join(LOG_DIR, f"multi_style_zine_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
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
REQUIRED_LIBS = [
    'python-dotenv', 'replicate', 'reportlab',
    'feedparser', 'requests', 'Pillow'
]

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
import replicate, requests, feedparser
from dotenv import load_dotenv
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from PIL import Image
from io import BytesIO
import random

# === 📥 Load environment variables ===
load_dotenv('ask.env')

# === 📌 Environment config ===
def get_env(var, default=None, required=False):
    value = os.getenv(var, default)
    if required and not value:
        log.error(f"Required environment variable '{var}' is missing. Exiting.")
        sys.exit(1)
    return value

# Rate limiting for API calls
class RateLimiter:
    def __init__(self, max_calls_per_minute=30):
        self.max_calls = max_calls_per_minute
        self.calls = []
        self.lock = threading.Lock()
    
    def wait_if_needed(self):
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

# Performance settings
MAX_CONCURRENT_IMAGES = int(get_env("MAX_CONCURRENT_IMAGES", "4"))
MAX_RETRIES = int(get_env("MAX_RETRIES", "3"))
RATE_LIMIT_PER_MINUTE = int(get_env("RATE_LIMIT_PER_MINUTE", "30"))

# Global rate limiter
rate_limiter = RateLimiter(max_calls_per_minute=RATE_LIMIT_PER_MINUTE)

TEXT_PROVIDER = get_env("TEXT_PROVIDER", "groq")
TEXT_MODEL = get_env("TEXT_MODEL", required=True)
NUM_SPREADS = int(get_env("NUM_SPREADS", "10"))
FILTER_KEYWORDS = [kw.strip() for kw in get_env("FILTER_KEYWORDS", "").split(",") if kw.strip()]
IMAGE_WIDTH = int(get_env("IMAGE_WIDTH", "1024"))
IMAGE_HEIGHT = int(get_env("IMAGE_HEIGHT", "1024"))
IMAGE_DPI = int(get_env("IMAGE_DPI", "300"))
CAPTION_POSITION = get_env("CAPTION_POSITION", "bottom")
NUM_STEPS = int(get_env("NUM_INFERENCE_STEPS", "30"))
GUIDANCE_SCALE = float(get_env("GUIDANCE_SCALE", "7.5"))
TITLE_TEMPLATE = get_env("ZINE_TITLE_TEMPLATE", "ASK Volume {theme}")
OUTPUT_PATH = get_env("OUTPUT_PATH", "output")

# === 🎨 Multi-Style Image Generation Models ===
STYLE_MODELS = {
    "photorealistic": {
        "model": "stability-ai/sdxl:39ed52f2a78e934b3ba6e2a89f5b1c712de7dfea535525255b1aa35c5565e08b",
        "style_prompt": "photorealistic architectural photography, high resolution, professional lighting",
        "description": "Photorealistic architectural photography"
    },
    "anime": {
        "model": "cjwbw/anything-v3-better-vae:09a5805203f4c12da649ec1923e9dafc1e7d0aed5e2d0c35a658ac25f4f4d1b8",
        "style_prompt": "anime style, architectural illustration, vibrant colors, detailed linework",
        "description": "Anime-style architectural illustrations"
    },
    "watercolor": {
        "model": "stability-ai/sdxl:39ed52f2a78e934b3ba6e2a89f5b1c712de7dfea535525255b1aa35c5565e08b",
        "style_prompt": "watercolor painting style, architectural art, soft colors, artistic interpretation",
        "description": "Watercolor architectural paintings"
    },
    "technical": {
        "model": "jagilley/controlnet-scribble:435061a1b5a4c1e26740464bf786efdfa9cb3a3ac488595a2de23e143fdb0117",
        "style_prompt": "technical architectural drawing, blueprint style, precise lines, engineering diagram",
        "description": "Technical architectural drawings"
    },
    "abstract": {
        "model": "stability-ai/sdxl:39ed52f2a78e934b3ba6e2a89f5b1c712de7dfea535525255b1aa35c5565e08b",
        "style_prompt": "abstract architectural art, geometric forms, modern art style, conceptual design",
        "description": "Abstract architectural art"
    },
    "sketch": {
        "model": "stability-ai/sdxl:39ed52f2a78e934b3ba6e2a89f5b1c712de7dfea535525255b1aa35c5565e08b",
        "style_prompt": "architectural sketch, hand-drawn style, pencil drawing, artistic sketch",
        "description": "Hand-drawn architectural sketches"
    },
    "minimalist": {
        "model": "stability-ai/sdxl:39ed52f2a78e934b3ba6e2a89f5b1c712de7dfea535525255b1aa35c5565e08b",
        "style_prompt": "minimalist architectural design, clean lines, simple forms, modern minimalism",
        "description": "Minimalist architectural design"
    },
    "futuristic": {
        "model": "stability-ai/sdxl:39ed52f2a78e934b3ba6e2a89f5b1c712de7dfea535525255b1aa35c5565e08b",
        "style_prompt": "futuristic architecture, sci-fi design, advanced technology, cyberpunk style",
        "description": "Futuristic architectural concepts"
    }
}

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

# === 🌐 STEP 1: Get theme from RSS or CLI ===
def get_theme_from_rss():
    urls = [u.strip() for u in get_env("RSS_FEEDS", "").split(",") if u.strip()]
    headlines = []
    for url in urls:
        try:
            feed = feedparser.parse(url)
            for e in feed.entries:
                t = e.title.strip()
                if t and (not FILTER_KEYWORDS or any(kw.lower() in t.lower() for kw in FILTER_KEYWORDS)):
                    headlines.append(t)
        except Exception as e:
            log.warning(f"RSS failed for {url}: {e}")
    return random.choice(headlines) if headlines else get_env("FALLBACK_THEME", "Architecture & AI")

def get_theme():
    if len(sys.argv) > 1:
        return ' '.join(sys.argv[1:])
    return get_theme_from_rss()

# === 🧠 STEP 2: Prompt + Caption generation ===
def call_llm(messages):
    try:
        # Add small delay to avoid rate limiting
        time.sleep(1)
        
        response = requests.post(TEXT_API_URL, headers=HEADERS, json={
            "model": TEXT_MODEL,
            "messages": messages
        })
        result = response.json()
        
        if response.status_code != 200:
            log.error(f"API Error: {result}")
            raise Exception(f"API returned status {response.status_code}: {result}")
            
        # Handle different response formats
        if 'choices' in result and len(result['choices']) > 0:
            return result['choices'][0]['message']['content']
        elif 'output' in result:
            return result['output']
        elif 'text' in result:
            return result['text']
        else:
            raise Exception(f"Unexpected response format: {result}")
            
    except Exception as e:
        log.error(f"LLM call failed: {e}")
        raise e

def validate_caption(caption):
    """Validate and fix caption to ensure 6 lines of 6 words each"""
    lines = [line.strip() for line in caption.split('\n') if line.strip()]
    
    # If we don't have exactly 6 lines, try to fix it
    if len(lines) != 6:
        # Split by periods or other punctuation if needed
        if len(lines) == 1:
            # Single line - try to split into 6 parts
            words = lines[0].split()
            if len(words) >= 36:
                lines = []
                for i in range(6):
                    start = i * 6
                    end = start + 6
                    lines.append(' '.join(words[start:end]))
            else:
                # Pad with meaningful text
                while len(lines) < 6:
                    lines.append("Architecture speaks through silent spaces")
    
    # Ensure each line has exactly 6 words
    fixed_lines = []
    for line in lines[:6]:  # Take only first 6 lines
        words = line.split()
        if len(words) > 6:
            words = words[:6]
        elif len(words) < 6:
            # Pad with meaningful words
            padding = ["in", "the", "space", "between", "dreams", "reality"]
            while len(words) < 6:
                words.append(padding[len(words) % len(padding)])
        fixed_lines.append(' '.join(words))
    
    # Ensure we have exactly 6 lines
    while len(fixed_lines) < 6:
        fixed_lines.append("Architecture speaks through silent spaces")
    
    return '\n'.join(fixed_lines[:6])

def generate_prompts_and_captions(theme):
    prompts_msg = [
        {"role": "system", "content": get_env("PROMPT_SYSTEM", "You are a visionary architectural writer and provocateur. You create compelling, artistic image prompts that capture the essence of architectural concepts with vivid, poetic language.")},
        {"role": "user", "content": get_env("PROMPT_TEMPLATE", "Generate {n} architectural image prompts on theme: '{theme}'. Each prompt should be a single, evocative line that describes a visual scene with artistic flair. Focus on mood, atmosphere, and architectural poetry. Do not include explanations or numbered lists - just the prompts, one per line.").format(n=NUM_SPREADS, theme=theme)}
    ]
    raw = call_llm(prompts_msg)
    
    if not raw or raw.strip() == "":
        raise Exception("LLM returned empty response for prompts")
    
    # Parse prompts more robustly
    lines = [line.strip() for line in raw.split('\n') if line.strip()]
    prompts = []
    
    for line in lines:
        # Remove numbering and common prefixes
        cleaned = line.strip("1234567890. -•*")
        if cleaned and len(cleaned) > 10:  # Ensure it's a meaningful prompt
            prompts.append(cleaned)
    
    # If we still don't have enough, try to split longer responses
    if len(prompts) < NUM_SPREADS and len(lines) > 0:
        # Try to split by common separators
        for line in lines:
            if ',' in line or ';' in line:
                parts = line.replace(',', '\n').replace(';', '\n').split('\n')
                for part in parts:
                    cleaned = part.strip("1234567890. -•*")
                    if cleaned and len(cleaned) > 10 and len(prompts) < NUM_SPREADS:
                        prompts.append(cleaned)
    
    if len(prompts) < NUM_SPREADS:
        log.warning(f"LLM only generated {len(prompts)} prompts, need {NUM_SPREADS}. Raw response: {raw[:200]}...")
        # Pad with variations of the theme
        while len(prompts) < NUM_SPREADS:
            prompts.append(f"Architectural interpretation of {theme} with artistic vision")
    
    captions = []
    for prompt in prompts:
        cap_msg = [
            {"role": "system", "content": get_env("CAPTION_SYSTEM", "You are a masterful architectural poet and critic. You write profound, artistic captions that capture the deeper meaning and emotional resonance of architectural spaces.")},
            {"role": "user", "content": get_env("CAPTION_TEMPLATE", "Write exactly 6 lines, each containing exactly 6 words, that form a complete, meaningful caption for this architectural image: {prompt}. Each line should be a complete thought with poetic depth. The entire caption should tell a coherent story that reveals the architectural philosophy, emotional impact, and cultural significance of the space.").format(prompt=prompt)}
        ]
        raw_caption = call_llm(cap_msg)
        
        if not raw_caption or raw_caption.strip() == "":
            raise Exception(f"LLM returned empty response for caption: {prompt[:50]}...")
            
        validated_caption = validate_caption(raw_caption)
        captions.append(validated_caption)
        log.info(f"Generated caption for '{prompt[:50]}...': {len(validated_caption.split('\n'))} lines")
    return prompts, captions

# === 🎨 STEP 3: Generate images with different styles ===
def generate_single_image(args):
    """Generate a single image with retry logic and memory optimization"""
    prompt, style_name, i, style_config = args
    
    max_retries = MAX_RETRIES
    retry_delay = 2
    
    for attempt in range(max_retries):
        try:
            # Rate limiting
            rate_limiter.wait_if_needed()
            
            # Combine the architectural prompt with the style prompt
            full_prompt = f"{prompt}, {style_config['style_prompt']}"
            
            output = replicate.run(style_config["model"], input={
                "prompt": full_prompt,
                "width": IMAGE_WIDTH,
                "height": IMAGE_HEIGHT,
                "num_inference_steps": NUM_STEPS,
                "guidance_scale": GUIDANCE_SCALE
            })
            
            image_url = output[0] if isinstance(output, list) else output
            
            # Download and save image locally with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            image_filename = f"{style_name}_image_{i+1:02d}_{timestamp}.jpg"
            image_path = os.path.join("images", style_name, image_filename)
            
            # Download image with memory optimization
            resp = requests.get(image_url, stream=True)
            resp.raise_for_status()
            
            with open(image_path, 'wb') as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            # Clear response from memory immediately
            resp.close()
            
            # Log image details
            image_log_file = os.path.join("images", style_name, f"{style_name}_image_log.txt")
            with open(image_log_file, 'a', encoding='utf-8') as log_file:
                log_file.write(f"Image {i+1}: {image_filename}\n")
                log_file.write(f"Prompt: {prompt}\n")
                log_file.write(f"Full Prompt: {full_prompt}\n")
                log_file.write(f"URL: {image_url}\n")
                log_file.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                log_file.write("-" * 80 + "\n")
            
            log.info(f"✅ Generated {style_name} image {i+1}: {image_filename}")
            return image_url, image_path
            
        except Exception as e:
            log.warning(f"Attempt {attempt + 1} failed for {style_name} image {i+1}: {e}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay * (attempt + 1))  # Exponential backoff
            else:
                log.error(f"❌ Failed to generate {style_name} image {i+1} after {max_retries} attempts")
                return None, None
    
    return None, None

def generate_images_with_style(prompts, style_name):
    """Generate images in parallel with better error handling"""
    images = []
    image_paths = []
    style_config = STYLE_MODELS[style_name]
    
    # Create images directory for this style
    images_dir = os.path.join("images", style_name)
    os.makedirs(images_dir, exist_ok=True)
    
    log.info(f"🚀 Generating {len(prompts)} images with {style_name} style: {style_config['description']}")
    
    # Prepare arguments for parallel processing
    args_list = [(prompt, style_name, i, style_config) for i, prompt in enumerate(prompts)]
    
    # Use ThreadPoolExecutor for parallel processing
    max_workers = min(MAX_CONCURRENT_IMAGES, len(prompts))  # Limit concurrent requests
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_index = {executor.submit(generate_single_image, args): i for i, args in enumerate(args_list)}
        
        # Collect results as they complete
        for future in concurrent.futures.as_completed(future_to_index):
            index = future_to_index[future]
            try:
                image_url, image_path = future.result()
                images.append(image_url)
                image_paths.append(image_path)
            except Exception as e:
                log.error(f"❌ Exception in parallel processing for image {index + 1}: {e}")
                images.append(None)
                image_paths.append(None)
    
    successful_images = sum(1 for img in images if img is not None)
    log.info(f"✅ {style_name} style complete: {successful_images}/{len(prompts)} images generated successfully")
    
    return images, image_paths

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
        images, image_paths = generate_images_with_style(prompts, style_name)
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
    theme = get_theme()
    log.info(f"🎯 Theme selected: {theme}")
    
    # Generate images for all styles (no PDFs)
    generated_images = []
    total_styles = len(STYLE_MODELS)
    
    log.info(f"🚀 Starting generation for {total_styles} styles...")
    
    for i, style_name in enumerate(STYLE_MODELS.keys(), 1):
        style_start_time = time.time()
        log.info(f"📊 Progress: {i}/{total_styles} - {style_name.upper()}")
        
        try:
            images, image_paths, captions = generate_images_for_style(theme, style_name)
            if images:
                successful_count = sum(1 for img in images if img is not None)
                generated_images.append((style_name, successful_count))
                style_time = time.time() - style_start_time
                log.info(f"✅ {style_name.upper()} complete: {successful_count} images in {style_time:.1f}s")
            else:
                log.error(f"❌ {style_name.upper()}: No images generated")
        except Exception as e:
            log.error(f"❌ Failed to generate {style_name} images: {e}")
            continue
    
    # Summary
    total_time = time.time() - start_time
    log.info(f"🎉 === IMAGE GENERATION COMPLETE ===")
    log.info(f"⏱️  Total time: {total_time:.1f} seconds")
    log.info(f"📊 Successfully generated images for {len(generated_images)}/{total_styles} styles:")
    
    total_images = 0
    for style_name, count in generated_images:
        log.info(f"✅ {style_name.upper()}: {count} images")
        total_images += count
    
    if not generated_images:
        log.error("❌ No images were generated successfully")
    else:
        avg_time_per_image = total_time / total_images if total_images > 0 else 0
        log.info(f"🎉 Image generation complete! {total_images} total images across {len(generated_images)} styles.")
        log.info(f"📈 Average time per image: {avg_time_per_image:.1f}s")
        log.info(f"📁 Images saved to: images/")
        log.info(f"📝 Captions saved to: captions/")
        log.info(f"📄 PDFs will be created by weekly/monthly curators")

if __name__ == "__main__":
    main() 