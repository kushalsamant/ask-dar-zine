# GitHub Actions Setup for Daily Zine Generation

## 🚀 Overview
This setup will automatically generate images daily at 4:00 AM UTC using GitHub Actions cron jobs. PDFs are created weekly (Thursdays) and monthly (last day of month). All generated content will be committed to your repository and available as artifacts.

## 📋 Prerequisites
1. Your repository must be on GitHub (not local only)
2. You need API keys for the services you're using
3. Repository must have Actions enabled

## ⚙️ Step 1: Configure GitHub Secrets

Go to your repository → Settings → Secrets and variables → Actions → New repository secret

### Required Secrets:

#### **API Keys:**
```
GROQ_API_KEY=your_groq_api_key_here
TOGETHER_API_KEY=your_together_api_key_here
REPLICATE_API_TOKEN=your_replicate_api_token_here
```

#### **Core Configuration:**
```
TEXT_PROVIDER=groq
TEXT_MODEL=llama3-8b-8192
NUM_SPREADS=10
IMAGE_WIDTH=1024
IMAGE_HEIGHT=1024
IMAGE_DPI=300
CAPTION_POSITION=top-right
NUM_INFERENCE_STEPS=30
GUIDANCE_SCALE=7.5
OUTPUT_PATH=output
```

#### **Templates and Prompts:**
```
ZINE_TITLE_TEMPLATE=ASK Volume {theme}
PROMPT_SYSTEM=You are a visionary architectural writer and provocateur. You create compelling, artistic image prompts that capture the essence of architectural concepts with vivid, poetic language.
PROMPT_TEMPLATE=Generate {n} architectural image prompts on theme: '{theme}'. Each prompt should be a single, evocative line that describes a visual scene with artistic flair. Focus on mood, atmosphere, and architectural poetry. Do not include explanations or numbered lists - just the prompts, one per line.
CAPTION_SYSTEM=You are a masterful architectural poet and critic. You write profound, artistic captions that capture the deeper meaning and emotional resonance of architectural spaces.
CAPTION_TEMPLATE=Write exactly 6 lines, each containing exactly 6 words, that form a complete, meaningful caption for this architectural image: {prompt}. Each line should be a complete thought with poetic depth. The entire caption should tell a coherent story that reveals the architectural philosophy, emotional impact, and cultural significance of the space.
```

#### **Optional Configuration:**
```
FILTER_KEYWORDS=architecture,design,innovation
RSS_FEEDS=https://feeds.bbci.co.uk/news/rss.xml,https://rss.cnn.com/rss/edition.rss
FALLBACK_THEME=Architecture & AI
CAPTION_FONT_SIZE=14
CAPTION_LINE_SPACING=18
GROQ_API_BASE=https://api.groq.com/openai/v1
TOGETHER_API_BASE=https://api.together.xyz/v1
```

## 🔧 Step 2: Enable GitHub Actions

1. Go to your repository on GitHub
2. Click on "Actions" tab
3. If Actions are disabled, click "Enable Actions"
4. The workflow will automatically appear under "Workflows"

## ⏰ Step 3: Customize Schedule (Optional)

To change the schedule, edit `.github/workflows/daily-zine-generation.yml`:

```yaml
on:
  schedule:
    # Current: Daily at 4:00 AM UTC
    - cron: '0 4 * * *'
    
    # Other options:
    # - cron: '0 6 * * *'     # 6:00 AM UTC
    # - cron: '0 12 * * *'    # 12:00 PM UTC
    # - cron: '0 4 * * 1-5'   # Weekdays only at 4:00 AM
    # - cron: '0 */6 * * *'   # Every 6 hours
```

## 🎯 Step 4: Test the Workflow

1. Go to Actions tab
2. Click on "Daily Zine Generation"
3. Click "Run workflow" → "Run workflow"
4. Monitor the execution

## 📊 Step 5: Monitor Results

### **Generated Content:**
- **Images:** Stored in `images/` folder by style
- **Captions:** Stored in `captions/` folder by style
- **Weekly PDFs:** Stored in `weekly_curated/` folder
- **Monthly PDFs:** Stored in `monthly_curated/` folder
- **Logs:** Available in Actions run logs
- **Artifacts:** Downloadable from Actions tab

### **Repository Updates:**
- All generated content is automatically committed
- Each run creates a new commit with timestamp
- Images are preserved with timestamps to prevent overwrites

## 🔍 Troubleshooting

### **Common Issues:**

1. **API Key Errors:**
   - Check all API keys are correctly set in secrets
   - Verify API keys have sufficient credits

2. **Permission Errors:**
   - Ensure repository has Actions enabled
   - Check workflow has write permissions

3. **Schedule Not Running:**
   - GitHub Actions may have delays
   - Check Actions tab for any failed runs
   - Verify cron syntax is correct

### **Manual Trigger:**
You can always run the workflow manually:
1. Go to Actions → Daily Zine Generation
2. Click "Run workflow"
3. Select branch and run

## 📈 Benefits of GitHub Actions

✅ **No Local Resources:** Runs on GitHub's servers  
✅ **Automatic Backups:** All content committed to repo  
✅ **Version Control:** Track changes over time  
✅ **Artifact Storage:** Download generated content  
✅ **Cost Effective:** Free for public repos  
✅ **Reliable:** GitHub's infrastructure  
✅ **Notifications:** Email/webhook notifications  

## 🎨 Content Strategy

With the automated system, you'll have:
- **8 different styles** × **10 images** = **80 images daily**
- **1 weekly curated PDF** (best 10 images every Thursday)
- **1 monthly comprehensive PDF** (all images on last day of month)
- **Consistent content** for social media
- **Growing archive** of architectural concepts

Perfect for:
- Daily social media posts
- Weekly content batches
- Monthly collections
- Portfolio building

## 🔄 Next Steps

1. Set up all secrets in GitHub
2. Push the workflow file to your repository
3. Test with manual run
4. Monitor first few automated runs
5. Start using generated content for marketing!

---

**Need help?** Check the Actions tab for detailed logs and error messages. 