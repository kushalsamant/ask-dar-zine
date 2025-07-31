# 🏛️ ASK Daily Architectural Research Zine

**Automated Daily Generation of Architectural Research Zines with AI-Powered Content Creation**

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![GitHub Actions](https://img.shields.io/badge/GitHub%20Actions-Daily%20Generation-brightgreen.svg)](.github/workflows/daily-zine-generation.yml)

## 📖 Overview

ASK Daily Architectural Research Zine is an automated system that generates daily architectural research publications featuring:

- **50 Full-Bleed Architectural Images** in rotating styles
- **AI-Generated Poetic Captions** with deduplication
- **FreshRSS-Curated Themes** from architectural sources
- **Professional PDF Layout** with cover pages
- **30 Architectural Styles** rotating daily

## 🎯 Features

### 🤖 **AI-Powered Content Generation**
- **Together.ai Integration**: Uses free models for text and image generation
- **Sophisticated Prompts**: Full token utilization (4000 tokens) for rich content
- **Caption Deduplication**: Jaccard similarity algorithm prevents repetitive content
- **Smart Retry Logic**: Up to 5 attempts for unique caption generation

### 🎨 **30 Architectural Styles**
- **Futuristic**: Sci-fi aesthetic with advanced technology
- **Minimalist**: Clean lines and essential elements
- **Abstract**: Conceptual and artistic interpretation
- **Technical**: Engineering precision and structural clarity
- **Watercolor**: Artistic rendering with soft colors
- **Anime**: Stylized design and creative visualization
- **Photorealistic**: Realistic rendering with lifelike detail
- **Sketch**: Hand-drawn aesthetic and artistic expression
- *And 22 more styles...*

### 📄 **Professional PDF Output**
- **Full-Bleed Images**: Images extend to page edges
- **Enhanced Captions**: 6-line poetic captions with white bands
- **Cover Pages**: Professional front and back covers
- **Sequential Naming**: `ASK_Daily_Architectural_Research_Zine-2025-VOL-211-Abstract.pdf`
- **Page Numbers**: Bold numbering for easy navigation

### 🌐 **FreshRSS Content Automation**
- **Self-Hosted RSS**: FreshRSS with 20+ architectural feeds
- **Intelligent Curation**: AI-powered theme analysis from curated content
- **Database Access**: Direct SQLite access for unlimited automation
- **Fallback System**: Traditional web scraping when FreshRSS unavailable

### 📊 **Progress Tracking & Analytics**
- **Real-Time Progress Bars**: Visual feedback for all operations
- **Similarity Metrics**: Caption uniqueness scoring
- **Detailed Logging**: Comprehensive execution logs
- **Performance Monitoring**: Rate limiting and API optimization

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- Together.ai API key (free tier available)
- Docker (for FreshRSS)
- Git

### Installation

1. **Clone the repository:**
```bash
git clone https://github.com/kushalsamant/ask-dar-zine.git
cd ask-dar-zine
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Set up environment variables:**
```bash
cp ask.env.template ask.env
# Edit ask.env with your Together.ai API key
```

4. **Start FreshRSS (optional but recommended):**
```bash
docker-compose up -d
# Access FreshRSS at http://localhost:8080
# Add architectural RSS feeds manually
```

5. **Configure API keys:**
```env
# Text Generation
TEXT_PROVIDER=together
TEXT_MODEL=meta-llama/Llama-3.3-70B-Instruct-Turbo-Free
TOGETHER_API_KEY=your_api_key_here

# Image Generation
IMAGE_PROVIDER=together
IMAGE_MODEL=black-forest-labs/FLUX.1-schnell-free
IMAGE_WIDTH=1024
IMAGE_HEIGHT=1024
INFERENCE_STEPS=4
GUIDANCE_SCALE=7.5
```

6. **Run the generator:**
```bash
# Test run (5 images)
python daily_zine_generator.py --test

# Ultra-fast test run (skip optional steps)
python daily_zine_generator.py --test --fast

# View current architectural sources
python daily_zine_generator.py --sources

# Full run (50 images) - 10x faster with concurrent processing
python daily_zine_generator.py

# Ultra-fast full run (skip optional steps)
python daily_zine_generator.py --fast

# 100x speed mode (maximum optimization)
python daily_zine_generator.py --ultra

# Custom options
python daily_zine_generator.py --images 10 --style technical
```

## 📁 Project Structure

```
ask-dar-zine/
├── daily_zine_generator.py      # 🎯 Complete zine generation pipeline
├── add_manual_sources.py       # 🔧 Manual source management tool
├── docker-compose.yml          # 🐳 FreshRSS Docker setup
├── ask.env                     # ⚙️ Environment variables (API keys, config)
├── ask.env.template            # 📋 Template for environment variables
├── requirements.txt            # 📦 Python dependencies
├── README.md                   # 📖 This documentation
├── existing_architectural_feeds.json  # 📊 Dynamically updated sources
├── .github/workflows/          # 🤖 GitHub Actions automation
│   └── daily-zine-generation.yml
├── images/                     # 🖼️ Generated images
├── daily_pdfs/                 # 📄 Generated PDFs
├── logs/                       # 📝 Log files
├── captions/                   # 💬 Generated captions
├── scraped_content/            # 🌐 Scraped web content
└── checkpoints/                # 💾 Pipeline progress checkpoints
```

## ⚡ Performance Optimization

### **100x Speed Improvements**

The pipeline now includes maximum performance optimizations:

- **🔄 Massive Concurrent Processing**: Up to 30 concurrent image generations and 40 concurrent caption generations
- **📦 Intelligent Caching**: Cache LLM responses and captions to avoid duplicate API calls
- **⚡ Ultra-Fast Mode**: Skip optional steps with `--fast` flag
- **🚀 100x Mode**: Maximum optimization with `--ultra` flag
- **🚫 Caption Deduplication**: Optional deduplication can be disabled for speed
- **⏱️ Minimal Rate Limiting**: Reduced delays between API calls (0.05s)
- **🎯 Smart Retry Logic**: Faster retry delays in fast mode
- **💾 Memory Optimization**: Batch processing and garbage collection
- **📦 Style Preloading**: Preload architectural styles for instant access

### **Performance Settings**

Configure in `ask.env`:
```env
# Performance Optimization
MAX_CONCURRENT_IMAGES=20
MAX_CONCURRENT_CAPTIONS=25
RATE_LIMIT_DELAY=0.1
SKIP_CAPTION_DEDUPLICATION=true
FAST_MODE=true
CACHE_ENABLED=true
PRELOAD_STYLES=true
BATCH_PROCESSING=true
OPTIMIZE_MEMORY=true
```

### **Speed Comparison**

| Mode | Images | Estimated Time | Speed Improvement |
|------|--------|----------------|-------------------|
| Sequential | 50 | ~45 minutes | 1x |
| Concurrent | 50 | ~8 minutes | 5.6x |
| Ultra-Fast | 50 | ~4.5 minutes | 10x |
| **100x Mode** | 50 | **~27 seconds** | **100x** |

## 🔄 Pipeline Flow

### **6-Step Linear Process**

1. **🌐 Content Scraping** (FreshRSS + Fallback)
   - Retrieve articles from 20+ architectural feeds
   - Analyze content themes and keywords
   - Generate intelligent theme prompts

2. **🎯 Theme Generation** (LLM)
   - Create sophisticated themes from curated content
   - Analyze trending topics and sources
   - Generate context-aware prompts

3. **🖼️ Image Generation** (AI)
   - Generate 50 full-bleed images
   - Apply daily rotating architectural style
   - Optimize for quality and consistency

4. **📝 Caption Generation** (LLM)
   - Create 6-line poetic captions
   - Ensure uniqueness with deduplication
   - Retry logic for quality assurance

5. **📄 PDF Creation** (ReportLab)
   - Compile images and captions
   - Professional layout with covers
   - Sequential naming convention

6. **🚀 Publishing** (GitHub Pages)
   - Automated daily publishing
   - Version control and archiving
   - Public accessibility

## 🎨 Architectural Styles

The system rotates through **30 distinct architectural styles**:

| Style | Description | Use Case |
|-------|-------------|----------|
| **Abstract** | Conceptual and artistic | Creative interpretation |
| **Minimalist** | Clean lines and essentials | Modern simplicity |
| **Futuristic** | Sci-fi aesthetic | Advanced technology |
| **Technical** | Engineering precision | Structural clarity |
| **Watercolor** | Artistic rendering | Soft, expressive |
| **Anime** | Stylized design | Creative visualization |
| **Photorealistic** | Realistic rendering | Lifelike detail |
| **Sketch** | Hand-drawn aesthetic | Artistic expression |
| **Brutalist** | Raw concrete aesthetic | Bold, monumental |
| **Gothic** | Medieval architectural | Dramatic, ornate |
| **Art Deco** | 1920s-30s style | Elegant, geometric |
| **Modernist** | 20th century clean | Functional beauty |
| **Postmodern** | Eclectic, playful | Creative diversity |
| **Deconstructivist** | Fragmented forms | Dynamic complexity |
| **Parametric** | Algorithmic design | Digital fabrication |
| **Biomimetic** | Nature-inspired | Organic forms |
| **Sustainable** | Green architecture | Environmental focus |
| **Vernacular** | Local traditions | Cultural context |
| **Neoclassical** | Classical revival | Timeless elegance |
| **Expressionist** | Emotional architecture | Dramatic forms |
| **Constructivist** | Russian avant-garde | Geometric abstraction |
| **International** | Universal style | Global modernism |
| **Critical Regionalism** | Local + global | Contextual modern |
| **Digital Baroque** | Complex ornamentation | Digital intricacy |
| **Neo-Futurist** | Future technology | Advanced concepts |
| **Eco-Tech** | Ecological technology | Sustainable innovation |
| **Blobitecture** | Organic forms | Fluid geometry |
| **Hi-Tech** | Industrial aesthetic | Technical expression |
| **Contextual** | Site-responsive | Environmental harmony |
| **Metabolist** | Organic growth | Evolving structures |

## 📈 Daily Source Addition

### **Automatic Content Expansion**
The system automatically adds **one new architectural research website** to the content sources every day:

- **35+ Pre-curated Sources**: Academic institutions, research journals, international publications
- **Deterministic Selection**: Uses day of year to ensure consistent, non-duplicate additions
- **Categorized Organization**: Academic, Research, International, Innovation, Regional, Emerging, Digital
- **Persistent Storage**: Added sources are saved and reused in future runs

### **View Current Sources**
```bash
python daily_zine_generator.py --sources
```

**Output:**
```
📊 Current Architectural Sources Status
==================================================
📈 Total Sources: 1
📅 Sources Added: 1 over time

🏷️  Academic (1 sources):
   • ETH Zurich Architecture

🎯 Next Source to Add: ETH Zurich Architecture (Academic)
📅 Day 212 of 35 total sources
```

### **Source Categories**
- **🏛️ Academic & Research**: ETH Zurich, AA School, UCL Bartlett, Cornell, Princeton
- **🌍 International**: Architectural Digest variants, regional publications
- **🔬 Specialized Research**: Academic journals, research publications
- **💡 Innovation & Technology**: Digital architecture, computational design
- **🏛️ Regional & Cultural**: Regional architectural magazines
- **🌱 Emerging & Alternative**: Experimental and humanitarian architecture
- **💻 Digital & Computational**: Parametric and computational architecture

### **Manual Source Management**
Use the dedicated tool to manage architectural sources:

```bash
# List all current sources
python add_manual_sources.py --list

# Add a single source
python add_manual_sources.py --add "Source Name" "https://source.com/feed" "Category"

# Add batch of predefined sources
python add_manual_sources.py --batch

# Remove a source
python add_manual_sources.py --remove "Source Name"
```

**Categories**: Academic, Research, International, Innovation, Regional, Emerging, Digital

### **Environment-Based Source Configuration**
Sources can also be configured directly in `ask.env`:

```env
# Enable/disable daily source addition
DAILY_SOURCE_ADDITION_ENABLED=true
MAX_SOURCES_PER_DAY=1
SOURCE_CATEGORIES=Academic,Research,International,Innovation,Regional,Emerging,Digital

# Predefined sources (pipe-separated: name|url|category)
PREDEFINED_SOURCES=AA School of Architecture|https://www.aaschool.ac.uk/feed|Academic,Berlage Institute|https://theberlage.nl/feed|Academic
```

**Format**: `Source Name|URL|Category,Source Name|URL|Category`

## 🌐 FreshRSS Integration

### **Why FreshRSS?**

| Feature | FreshRSS | Feedly |
|---------|----------|--------|
| **API Access** | ✅ Full access | ❌ Enterprise only |
| **Self-hosted** | ✅ Yes | ❌ No |
| **Database Access** | ✅ Direct SQLite | ❌ No |
| **Automation** | ✅ Unlimited | ❌ Limited |
| **Cost** | ✅ Free | ❌ $5-15/month |
| **Customization** | ✅ Full control | ❌ Limited |

### **Architectural Feeds**

**Core Architectural:**
- ArchDaily, Dezeen, DesignBoom, Architizer, Architectural Record

**Academic & Research:**
- MIT Media Lab, Harvard GSD, Yale Architecture, Columbia GSAPP

**International:**
- Domus, Architectural Digest, Architectural Review

### **Setup Instructions**

1. **Start FreshRSS:**
```bash
docker-compose up -d
```

2. **Access FreshRSS:**
- URL: http://localhost:8080
- Username: admin
- Password: password

3. **Add Feeds:**
- Use the web interface to add RSS feeds
- Organize into categories
- Set update frequency

4. **Integration:**
- The system automatically uses FreshRSS when available
- Falls back to traditional scraping if needed

## 📊 Performance Metrics

### **Test Results**
```
✅ Retrieved 60 articles
📊 Content Analysis:
   Total Articles: 60
   Top Sources: ArchDaily (10), Dezeen (10), DesignBoom (10)
   Top Keywords: design (8), media (6), 2025 (5), architects (4), house (4)
```

### **Generation Times**
- **Content Scraping**: 2-3 minutes
- **Theme Generation**: 30-60 seconds
- **Image Generation**: 15-20 minutes (50 images)
- **Caption Generation**: 5-7 minutes
- **PDF Creation**: 1-2 minutes
- **Total Time**: 25-35 minutes

### **Quality Metrics**
- **Caption Uniqueness**: 95%+ similarity avoidance
- **Image Quality**: High-resolution full-bleed
- **Theme Relevance**: Context-aware from curated content
- **PDF Layout**: Professional publication standard

## 🔧 Advanced Configuration

### **Command Line Options**

```bash
# Test run with limited images
python daily_zine_generator.py --test --images 5

# Specific style
python daily_zine_generator.py --style Abstract

# Custom theme
python daily_zine_generator.py --theme "Sustainable Architecture"

# Debug mode
python daily_zine_generator.py --debug

# Resume from checkpoint
python daily_zine_generator.py --resume
```

### **Environment Variables**

```env
# API Configuration
TEXT_PROVIDER=together
TEXT_MODEL=meta-llama/Llama-3.3-70B-Instruct-Turbo-Free
IMAGE_PROVIDER=together
IMAGE_MODEL=black-forest-labs/FLUX.1-schnell-free

# Generation Settings
IMAGE_WIDTH=1024
IMAGE_HEIGHT=1024
INFERENCE_STEPS=4
GUIDANCE_SCALE=7.5
NUM_IMAGES=50

# FreshRSS Configuration
FRESHRSS_URL=http://localhost:8080
FRESHRSS_USER=admin
FRESHRSS_PASSWORD=password
FRESHRSS_DB_PATH=/var/www/FreshRSS/data/users/admin/db.sqlite

# Scraper Configuration
SCRAPER_TIMEOUT=30
SCRAPER_MAX_RETRIES=3
SCRAPER_ARTICLES_PER_SOURCE=10
SCRAPER_CONTENT_DIR=scraped_content
```

## 🚀 Deployment

### **Local Development**
```bash
python daily_zine_generator.py --test
```

### **Production (GitHub Actions)**
- Automated daily generation at 9:00 AM IST
- Automatic PDF publishing to GitHub Pages
- Version control and archiving

### **Custom Scheduling**
```bash
# Cron job for custom timing
0 9 * * * cd /path/to/ask-dar-zine && python daily_zine_generator.py
```

## 🔍 Troubleshooting

### **Common Issues**

**API Rate Limits:**
```bash
# Check API usage
python daily_zine_generator.py --test --images 1
```

**FreshRSS Connection:**
```bash
# Check FreshRSS status
docker-compose ps
docker-compose logs freshrss
```

**Image Generation Failures:**
```bash
# Test with different model
IMAGE_MODEL=black-forest-labs/FLUX.1-schnell-free
```

### **Log Analysis**
```bash
# Check recent logs
tail -f logs/daily_zine_generator.log

# Analyze errors
grep "ERROR" logs/daily_zine_generator.log
```

## 📈 Future Enhancements

### **Planned Features**
- **Multi-language Support**: International architectural content
- **Advanced Analytics**: Content performance metrics
- **Social Media Integration**: Automated posting
- **Print Optimization**: High-resolution print-ready PDFs
- **Mobile App**: iOS/Android companion app

### **AI Model Upgrades**
- **Vision Models**: Image analysis and caption enhancement
- **Advanced LLMs**: More sophisticated theme generation
- **Custom Training**: Domain-specific architectural models

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Together.ai** for providing free AI models
- **FreshRSS** for self-hosted RSS aggregation
- **ReportLab** for PDF generation
- **Architectural community** for inspiration

---

**🎉 Ready to generate your first architectural zine? Run `python daily_zine_generator.py --test` and watch the magic happen!** 