import os
import sys
import subprocess
import logging
import time
from datetime import datetime

# === 🔧 Setup real-time logging ===
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)
log_filename = os.path.join(LOG_DIR, f"zine_run_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
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
TITLE_TEMPLATE = get_env("TITLE_TEMPLATE", "ASK: {theme}")
OUTPUT_PATH = get_env("OUTPUT_PATH", "output")

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

# === 🧠 STEP 2: Prompt + Caption generation using Groq/Together API ===
def call_llm(messages):
    try:
        # Add small delay to avoid rate limiting with 70B model
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
        {"role": "system", "content": get_env("PROMPT_SYSTEM", "You're an architectural provocateur zine writer.")},
        {"role": "user", "content": get_env("PROMPT_TEMPLATE", "Generate {n} image prompts on theme: '{theme}'.").format(n=NUM_SPREADS, theme=theme)}
    ]
    raw = call_llm(prompts_msg)
    
    if not raw or raw.strip() == "":
        raise Exception("LLM returned empty response for prompts")
    
    prompts = [line.strip("1234567890. ") for line in raw.split('\n') if line.strip()][:NUM_SPREADS]
    
    if len(prompts) < NUM_SPREADS:
        raise Exception(f"LLM only generated {len(prompts)} prompts, need {NUM_SPREADS}")
    
    captions = []
    for prompt in prompts:
        cap_msg = [
            {"role": "system", "content": get_env("CAPTION_SYSTEM", "You're a poetic architect writing 6x6 captions.")},
            {"role": "user", "content": get_env("CAPTION_TEMPLATE", "Write exactly 6 lines, each containing exactly 6 words, that form a complete, meaningful caption for this architectural image: {prompt}. Each line should be a complete thought and the entire caption should tell a coherent story.").format(prompt=prompt)}
        ]
        raw_caption = call_llm(cap_msg)
        
        if not raw_caption or raw_caption.strip() == "":
            raise Exception(f"LLM returned empty response for caption: {prompt[:50]}...")
            
        validated_caption = validate_caption(raw_caption)
        captions.append(validated_caption)
        log.info(f"Generated caption for '{prompt[:50]}...': {len(validated_caption.split('\n'))} lines")
    return prompts, captions

# === 🎨 STEP 3: Generate images ===
def generate_images(prompts):
    images = []
    model_ref = get_env("REPLICATE_MODEL", required=True)
    for prompt in prompts:
        try:
            output = replicate.run(model_ref, input={
                "prompt": prompt,
                "width": IMAGE_WIDTH,
                "height": IMAGE_HEIGHT,
                "num_inference_steps": NUM_STEPS,
                "guidance_scale": GUIDANCE_SCALE
            })
            images.append(output[0] if isinstance(output, list) else output)
        except Exception as e:
            log.error(f"Image gen failed for prompt '{prompt}': {e}")
            images.append(None)
    return images

# === 🖼️ STEP 4: Place captions ===
def place_caption(c, cap, pos, w, h):
    text = cap.split('\n')
    c.setFont("Helvetica", 10)
    c.setFillColorRGB(0, 0, 0)
    spacing = 12
    if pos == "bottom":
        for i, line in enumerate(text):
            c.drawString(30, 40 + i * spacing, line)
    elif pos == "center":
        for i, line in enumerate(text):
            c.drawCentredString(w / 2, h / 2 - i * spacing, line)
    elif pos == "top":
        for i, line in enumerate(text):
            c.drawString(30, h - 100 - i * spacing, line)
    # Add more positions as needed

# === 📄 STEP 5: Build PDF ===
def make_pdf(images, captions, theme):
    os.makedirs(OUTPUT_PATH, exist_ok=True)
    title = TITLE_TEMPLATE.format(theme=theme).replace(" ", "_")
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
        
        log.info(f"Created spread {i+1}/10 (pages {i*2+1}-{i*2+2})")
    
    c.save()
    log.info(f"PDF saved to: {fname} (20 pages total)")

# === 🚀 MAIN RUN ===
def main():
    theme = get_theme()
    log.info(f"Theme selected: {theme}")
    prompts, captions = generate_prompts_and_captions(theme)
    log.info("Prompts and captions generated")
    images = generate_images(prompts)
    log.info("Images generated")
    make_pdf(images, captions, theme)
    log.info("Zine build complete.")

if __name__ == "__main__":
    main()
