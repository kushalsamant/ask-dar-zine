# 🏛️ ASK Daily Architectural Research Zine

**Automated Daily Generation of Architectural Research Zines with AI-Powered Content Creation**

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![GitHub Actions](https://img.shields.io/badge/GitHub%20Actions-Daily%20Generation-brightgreen.svg)](.github/workflows/daily-zine-generation.yml)

## 📖 Overview

ASK Daily Architectural Research Zine is an automated system that generates daily architectural research publications featuring:

- **50 Full-Bleed Architectural Images** in rotating styles
- **AI-Generated Poetic Captions** with deduplication
- **Web-Scraped Themes** from architectural sources
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

### 🌐 **Web Scraping Integration**
- **Architectural Sources**: RSS feeds from leading architectural websites
- **Theme Extraction**: AI-powered theme selection from scraped content
- **Content Uniqueness**: Prevents topic repetition across days
- **Fallback System**: Reliable theme generation when scraping fails

### 📊 **Progress Tracking & Analytics**
- **Real-Time Progress Bars**: Visual feedback for all operations
- **Similarity Metrics**: Caption uniqueness scoring
- **Detailed Logging**: Comprehensive execution logs
- **Performance Monitoring**: Rate limiting and API optimization

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- Together.ai API key (free tier available)
- Git

### Installation

1. **Clone the repository:**
```bash
git clone https://github.com/kushalsamant/ask-dar-zine.git
cd ask-dar-zine
```

2. **Install dependencies:**
```bash
pip install python-dotenv reportlab requests Pillow beautifulsoup4 tqdm
```

3. **Set up environment variables:**
```bash
cp ask.env.template ask.env
# Edit ask.env with your Together.ai API key
```

4. **Configure API keys:**
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

5. **Run the generator:**
```bash
python daily_zine_generator.py
```

## 📋 Pipeline Overview

The system follows a **6-step linear pipeline**:

1. **🌐 Web Scraping** → Extract architectural themes
2. **🎨 Style Selection** → Choose daily architectural style
3. **✍️ Prompt Generation** → Create 50 sophisticated image prompts
4. **🖼️ Image Generation** → Generate 50 full-bleed images
5. **📝 Caption Generation** → Create unique poetic captions
6. **📄 PDF Creation** → Compile into professional zine

## 🎨 Style Rotation

The system rotates through **30 architectural styles** based on the day of the year:

```python
STYLES = [
    'futuristic', 'minimalist', 'sketch', 'abstract', 'technical',
    'watercolor', 'anime', 'photorealistic', 'brutalist', 'organic',
    'deconstructivist', 'parametric', 'vernacular', 'modernist',
    'postmodern', 'art_deco', 'gothic', 'romanesque', 'baroque',
    'neoclassical', 'victorian', 'colonial', 'mediterranean',
    'japanese', 'chinese', 'islamic', 'indian', 'african',
    'scandinavian', 'tropical'
]
```

## 📊 Output Structure

```
ask-dar-zine/
├── daily_pdfs/                    # Generated PDFs
│   └── ASK_Daily_Architectural_Research_Zine-2025-VOL-211-Abstract.pdf
├── images/                        # Generated images by style
│   ├── abstract/
│   ├── minimalist/
│   └── ...
├── captions/                      # Generated captions
├── scraped_content/               # Web scraped articles
├── logs/                          # Execution logs
└── daily_zine_generator.py        # Main script
```

## 🤖 AI Models Used

### **Text Generation**
- **Model**: `meta-llama/Llama-3.3-70B-Instruct-Turbo-Free`
- **Provider**: Together.ai (Free tier)
- **Token Limit**: 4000 tokens for sophisticated prompts
- **Features**: Architectural expertise, poetic caption generation

### **Image Generation**
- **Model**: `black-forest-labs/FLUX.1-schnell-free`
- **Provider**: Together.ai (Free tier)
- **Resolution**: 1024x1024
- **Steps**: 4 (optimized for free tier)
- **Features**: High-quality architectural image generation

## 🔧 Configuration

### **Environment Variables**
```env
# API Configuration
TOGETHER_API_KEY=your_api_key_here
TOGETHER_API_BASE=https://api.together.xyz/v1

# Model Settings
TEXT_MODEL=meta-llama/Llama-3.3-70B-Instruct-Turbo-Free
IMAGE_MODEL=black-forest-labs/FLUX.1-schnell-free

# Image Generation
IMAGE_WIDTH=1024
IMAGE_HEIGHT=1024
INFERENCE_STEPS=4
GUIDANCE_SCALE=7.5

# Web Scraping
SCRAPER_TIMEOUT=30
SCRAPER_RETRIES=3
SCRAPER_WORKERS=1
ARTICLES_PER_SOURCE=10
```

### **Rate Limiting**
- **LLM Calls**: 1-second delay between calls
- **Image Generation**: 1-second delay between images
- **429 Errors**: 60-second wait with retry logic
- **Pipeline Steps**: 2-second delay between major steps

## 📈 Performance

### **Execution Time** (Estimated)
- **Web Scraping**: ~2-3 minutes
- **Prompt Generation**: ~1-2 minutes
- **Image Generation**: ~25-30 minutes (50 images)
- **Caption Generation**: ~5-10 minutes
- **PDF Creation**: ~1-2 minutes
- **Total**: ~35-45 minutes

### **Resource Usage**
- **Memory**: ~500MB-1GB
- **Storage**: ~100MB per PDF (50 images)
- **API Calls**: ~150 calls per run

## 🔄 Automation

### **GitHub Actions**
The repository includes automated daily generation via GitHub Actions:

```yaml
# .github/workflows/daily-zine-generation.yml
name: Daily Zine Generation
on:
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM UTC
```

### **Manual Execution**
```bash
# Run the complete pipeline
python daily_zine_generator.py

# Check logs
tail -f logs/daily_zine_*.log
```

## 🛠️ Development

### **Project Structure**
```
ask-dar-zine/
├── daily_zine_generator.py        # Main pipeline script
├── web_scraper.py                 # Web scraping functionality
├── ask.env                        # Environment configuration
├── ask.env.template               # Template for setup
├── requirements.txt               # Python dependencies
├── README.md                      # This file
└── .github/workflows/             # GitHub Actions
    └── daily-zine-generation.yml
```

### **Key Functions**
- `main()`: Orchestrates the 6-step pipeline
- `scrape_architectural_content()`: Web scraping for themes
- `generate_prompts()`: Creates 50 image prompts
- `generate_all_images()`: Sequential image generation
- `generate_all_captions()`: Caption generation with deduplication
- `create_daily_pdf()`: PDF compilation and layout

## 🎯 Use Cases

### **Architectural Research**
- Daily architectural inspiration
- Style exploration and analysis
- Design trend monitoring
- Educational content creation

### **Content Creation**
- Social media content
- Blog posts and articles
- Portfolio development
- Design presentations

### **Academic Use**
- Architecture education
- Research documentation
- Style comparison studies
- Design methodology exploration

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

### **Development Guidelines**
- Follow PEP 8 style guidelines
- Add comprehensive logging
- Include error handling
- Update documentation
- Test with different styles

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Together.ai** for providing free AI models
- **Architectural websites** for content inspiration
- **Open source community** for libraries and tools

## 📞 Support

For questions, issues, or contributions:
- **Issues**: [GitHub Issues](https://github.com/kushalsamant/ask-dar-zine/issues)
- **Discussions**: [GitHub Discussions](https://github.com/kushalsamant/ask-dar-zine/discussions)

---

**Built with ❤️ for the architectural community**

*Generate daily architectural inspiration with AI-powered creativity* 