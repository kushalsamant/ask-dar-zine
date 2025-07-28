# === 🛠️ Auto-install required packages ===
import os, sys, subprocess

REQUIRED_LIBS = [
    'python-dotenv', 'openai', 'replicate', 'reportlab',
    'feedparser', 'requests', 'Pillow'
]

def install_missing_libs():
    for lib in REQUIRED_LIBS:
        try:
            __import__(lib)
        except ImportError:
            print(f"📦 Installing missing: {lib}")
            subprocess.check_call([sys.executable, "-m", "pip", "install", lib])

install_missing_libs()

# === ✅ Imports (after installation) ===
import openai, replicate, requests, feedparser
from dotenv import load_dotenv
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from io import BytesIO
from PIL import Image
import random
import textwrap

# === 📥 Load config ===
load_dotenv()

TEXT_PROVIDER = os.getenv("TEXT_PROVIDER", "groq").lower()
TEXT_MODEL = os.getenv("TEXT_MODEL")
NUM_SPREADS = int(os.getenv("NUM_SPREADS", "10"))
FILTER_KEYWORDS = [kw.strip() for kw in os.getenv("FILTER_KEYWORDS", "").split(",") if kw.strip()]
IMAGE_WIDTH = int(os.getenv("IMAGE_WIDTH", "1024"))
IMAGE_HEIGHT = int(os.getenv("IMAGE_HEIGHT", "1024"))
IMAGE_DPI = int(os.getenv("IMAGE_DPI", "300"))
CAPTION_POSITION = os.getenv("CAPTION_POSITION", "bottom").lower()

ZINE_TITLE_TEMPLATE = os.getenv("ZINE_TITLE_TEMPLATE", "Zine: {theme}")
OUTPUT_FILENAME_TEMPLATE = os.getenv("OUTPUT_FILENAME_TEMPLATE", "zine_{theme}.pdf")

REPLICATE_MODEL = os.getenv("REPLICATE_MODEL")

# Optional advanced image gen config
GEN_OPTS = {
    "num_inference_steps": int(os.getenv("NUM_INFERENCE_STEPS", "25")),
    "guidance_scale": float(os.getenv("GUIDANCE_SCALE", "7.5"))
}

# API keys and bases
API_KEYS = {
    "openai": os.getenv("OPENAI_API_KEY"),
    "groq": os.getenv("GROQ_API_KEY"),
    "together": os.getenv("TOGETHER_API_KEY")
}
API_BASES = {
    "openai": os.getenv("OPENAI_API_BASE"),
    "groq": os.getenv("GROQ_API_BASE"),
    "together": os.getenv("TOGETHER_API_BASE")
}
openai.api_key = API_KEYS.get(TEXT_PROVIDER)
openai.api_base = API_BASES.get(TEXT_PROVIDER)

# === 🎯 Get Theme from RSS ===
def get_theme_from_rss():
    urls = [u.strip() for u in os.getenv("RSS_FEEDS", "").split(",") if u.strip()]
    headlines = []
    for url in urls:
        try:
            feed = feedparser.parse(url)
            for e in feed.entries:
                t = e.title.strip()
                if t and (not FILTER_KEYWORDS or any(kw.lower() in t.lower() for kw in FILTER_KEYWORDS)):
                    headlines.append(t)
        except Exception as e:
            print(f"⚠️ RSS fail: {url} -> {e}")
    return random.choice(headlines) if headlines else os.getenv("FALLBACK_THEME", "Architecture & AI")

def get_theme():
    return ' '.join(sys.argv[1:]) if len(sys.argv) > 1 else get_theme_from_rss()

# === 🧠 Modular Text Generation ===
def call_openai(messages):
    resp = openai.ChatCompletion.create(model=TEXT_MODEL, messages=messages)
    return resp['choices'][0]['message']['content']

def call_groq(messages):
    import openai as groq_openai
    groq_openai.api_key = API_KEYS["groq"]
    groq_openai.api_base = API_BASES["groq"]
    resp = groq_openai.ChatCompletion.create(model=TEXT_MODEL, messages=messages)
    return resp['choices'][0]['message']['content']

def call_together(messages):
    import openai as together_openai
    together_openai.api_key = API_KEYS["together"]
    together_openai.api_base = API_BASES["together"]
    resp = together_openai.ChatCompletion.create(model=TEXT_MODEL, messages=messages)
    return resp['choices'][0]['message']['content']

CALL_PROVIDER = {
    "openai": call_openai,
    "groq": call_groq,
    "together": call_together
}

# === 🧠 Prompt + Caption Generator ===
def generate_prompts_and_captions(theme):
    call_fn = CALL_PROVIDER[TEXT_PROVIDER]

    prompt_system = os.getenv("PROMPT_SYSTEM", "You're an architectural provocateur zine writer.")
    prompt_template = os.getenv("PROMPT_TEMPLATE", "Generate {n} image prompts on theme: '{theme}'.")

    messages = [
        {"role": "system", "content": prompt_system},
        {"role": "user", "content": prompt_template.format(n=NUM_SPREADS, theme=theme)}
    ]
    raw = call_fn(messages)
    prompts = [line.strip("1234567890. ") for line in raw.split('\n') if line.strip()]
    prompts = prompts[:NUM_SPREADS]

    caption_tpl = os.getenv("CAPTION_TEMPLATE", "Write a Socratic 6-line, 6-word caption for: {prompt}")
    caption_system = os.getenv("CAPTION_SYSTEM", "You're a poetic architect writing 6x6 captions.")

    captions = []
    for prompt in prompts:
        messages = [
            {"role": "system", "content": caption_system},
            {"role": "user", "content": caption_tpl.format(prompt=prompt)}
        ]
        captions.append(call_fn(messages))

    return prompts, captions

# === 🎨 Image Generation via Replicate ===
def generate_images(prompts):
    images = []
    for prompt in prompts:
        output = replicate.run(
            REPLICATE_MODEL,
            input={
                "prompt": prompt,
                "width": IMAGE_WIDTH,
                "height": IMAGE_HEIGHT,
                **GEN_OPTS
            }
        )
        images.append(output)
    return images

# === 🖼️ True DPI-Resized PDF Page ===
def draw_image_resized(c, img_url):
    try:
        img_resp = requests.get(img_url)
        img = Image.open(BytesIO(img_resp.content))
        img.load()

        target_width = int((A4[0] / 72) * IMAGE_DPI)
        target_height = int((A4[1] / 72) * IMAGE_DPI)
        img = img.resize((target_width, target_height), Image.Resampling.LANCZOS)

        bio = BytesIO()
        img.save(bio, format="PNG")
        bio.seek(0)
        c.drawImage(ImageReader(bio), 0, 0, width=A4[0], height=A4[1])
    except Exception as e:
        print("⚠️ Error loading image:", e)

# === ✏️ Caption Drawing ===
def draw_caption(c, caption):
    c.setFont("Helvetica", int(os.getenv("CAPTION_FONT_SIZE", "10")))
    spacing = int(os.getenv("CAPTION_LINE_SPACING", "12"))
    lines = caption.strip().split("\n")
    w, h = A4

    pos = CAPTION_POSITION
    y_start = {
        "top": h - 60,
        "bottom": 80,
        "center": h // 2,
        "top-left": h - 60,
        "top-right": h - 60,
        "bottom-left": 80,
        "bottom-right": 80,
        "left": h // 2,
        "right": h // 2
    }.get(pos, 80)

    x_start = {
        "left": 20,
        "bottom-left": 20,
        "top-left": 20,
        "center": w // 2 - 100,
        "right": w - 200,
        "bottom-right": w - 200,
        "top-right": w - 200
    }.get(pos, 20)

    for i, line in enumerate(lines):
        c.drawString(x_start, y_start - i * spacing, line.strip())

# === 🧾 PDF Maker ===
def make_pdf(images, captions, theme):
    title = ZINE_TITLE_TEMPLATE.format(theme=theme)
    fname = OUTPUT_FILENAME_TEMPLATE.format(theme=theme.replace(" ", "_"))
    c = canvas.Canvas(fname, pagesize=A4)

    for img_url, caption in zip(images, captions):
        draw_image_resized(c, img_url)
        draw_caption(c, caption)
        c.showPage()

    c.save()
    print("✅ Zine saved:", fname)

# === 🚀 Run ===
def main():
    theme = get_theme()
    print("🎯 Theme selected:", theme)
    prompts, captions = generate_prompts_and_captions(theme)
    print("🧠 Generated prompts & captions")
    images = generate_images(prompts)
    print("🎨 Generated images")
    make_pdf(images, captions, theme)
    print("📄 PDF complete")

if __name__ == "__main__":
    main()
