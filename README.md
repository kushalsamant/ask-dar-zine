# ASK - Daily Architectural Zine Generator

An automated system that generates daily architectural zines with 50 full-bleed images in a single style, complete with poetic captions.

## 🎯 **Flow**

1. **Web Scraping**: Scrapes architectural content from reliable sources
2. **Theme Generation**: Uses scraped content to create 1 daily theme
3. **Prompt Creation**: Generates 50 architectural image prompts from the theme
4. **Image Generation**: Creates 50 full-bleed images in ONE style only
5. **Caption Creation**: Generates 50 poetic captions (6 lines, 6 words each)
6. **PDF Assembly**: Stitches everything into one comprehensive PDF

## 🚀 **Quick Start**

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/ask-dar-zine.git
   cd ask-dar-zine
   ```

2. **Set up environment**:
   ```bash
   cp ask.env.template ask.env
   # Edit ask.env with your API keys
   ```

3. **Run daily generation**:
   ```bash
   python daily_zine_generator.py
   ```

## 📁 **Output Structure**

```
ask-dar-zine/
├── daily_pdfs/          # Generated PDFs
├── images/              # Generated images by style
├── captions/            # Generated captions
├── scraped_content/     # Web scraped articles
├── logs/                # Generation logs
└── ask.env              # Configuration
```

## ⚙️ **Configuration**

Edit `ask.env` to configure:

- **API Keys**: Groq (text), Together.ai (images)
- **Image Settings**: Size, steps, guidance scale
- **Web Scraping**: Sources, timeouts, retries
- **Style Selection**: 8 architectural styles rotating daily

## 🎨 **Styles**

The system rotates through 8 architectural styles:
- **Futuristic** - Sci-fi aesthetic, glowing lights
- **Minimalist** - Clean lines, simplicity
- **Sketch** - Hand-drawn beauty
- **Abstract** - Geometric harmony
- **Technical** - Precision engineering
- **Watercolor** - Fluid artistic vision
- **Anime** - Japanese aesthetic
- **Photorealistic** - Perfect detail

## 🤖 **Automation**

- **GitHub Actions**: Runs daily at 4:00 AM UTC
- **Manual Trigger**: Use workflow_dispatch
- **Artifacts**: Uploads generated content
- **Git Integration**: Commits and pushes results

## 📊 **Daily Output**

Each run generates:
- **50 full-bleed images** in one style
- **50 poetic captions** (6 lines each)
- **1 comprehensive PDF** (51 pages)
- **Web scraped content** for themes

## 🔧 **Dependencies**

- Python 3.9+
- python-dotenv
- reportlab
- Pillow
- requests
- beautifulsoup4

## 📝 **License**

MIT License - see LICENSE file for details.

---

**ASK** - Architectural Poetry in Motion 🏛️✨ 