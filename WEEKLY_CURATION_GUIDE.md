# Weekly Curation System Guide

## 🎯 Overview

The weekly curation system automatically selects the **best 10 images** from your daily generation and creates a curated PDF every **Thursday at 4:00 AM UTC**. This gives you a high-quality collection for marketing and portfolio purposes.

## ⏰ Schedule

- **Daily Generation:** Every day at 4:00 AM UTC
- **Weekly Curation:** Every Thursday at 4:00 AM UTC
- **Selection Period:** Monday to Sunday (previous week)

## 🔄 How It Works

### **1. Daily Generation (Every Day)**
- Generates 8 styles × 10 images = **80 images daily**
- Saves images with timestamps in `images/` folder
- Stores captions in `captions/` folder for later use

### **2. Weekly Curation (Thursdays)**
- Scans all images from Monday to Sunday
- Selects the best 10 images using smart criteria
- Creates a curated PDF with professional layout
- Generates a detailed summary report

## 🎨 Selection Criteria

The system uses intelligent selection to ensure quality and diversity:

### **Primary Criteria:**
1. **Style Diversity** - Maximum 2 images per style
2. **Recency** - Prioritizes newer images
3. **Quality** - Based on generation success rate

### **Selection Strategy:**
```
Week's Images → Sort by Date → Ensure Style Diversity → Select Top 10
```

## 📁 Output Structure

### **Daily Content:**
```
images/
├── photorealistic/
│   ├── photorealistic_image_01_20241201_040000.jpg
│   └── ...
├── anime/
├── watercolor/
└── ...

captions/
├── photorealistic_captions.txt
├── anime_captions.txt
└── ...
```

### **Weekly Curated Content:**
```
weekly_curated/
├── ASK Weekly Curated_2024-11-25 - 2024-12-01.pdf
├── weekly_summary_20241125.txt
└── ...
```

## 📊 Weekly PDF Features

### **Title Page:**
- "ASK Weekly Curated"
- Week date range
- Total images selected
- Professional branding

### **Image Pages:**
- Full-bleed images
- Professional captions
- Style and date information
- Consistent typography

### **Summary Report:**
- Complete image list
- Style distribution
- Generation dates
- Selection criteria used

## 🎯 Marketing Strategy

### **Perfect for:**
- **Weekly social media posts** - "This week's best AI architecture"
- **Portfolio building** - Curated collections
- **Client presentations** - Professional quality
- **Newsletter content** - Weekly highlights
- **Sales materials** - Premium curated content

### **Content Calendar:**
- **Monday:** Share daily generation highlights
- **Tuesday-Friday:** Individual style showcases
- **Thursday:** Weekly curated collection launch
- **Weekend:** Behind-the-scenes content

## ⚙️ Configuration

### **Environment Variables:**
```bash
# Weekly Curator Settings
WEEKLY_OUTPUT_PATH=weekly_curated
WEEKLY_TITLE_TEMPLATE=ASK Weekly Curated: {week_start} - {week_end}

# Caption Settings
CAPTION_POSITION=top-right
CAPTION_FONT_SIZE=14
CAPTION_LINE_SPACING=18
```

### **Customization Options:**
- **Selection count:** Change from 10 to any number
- **Date range:** Modify week definition (Mon-Sun vs Sun-Sat)
- **Style limits:** Adjust maximum images per style
- **PDF layout:** Customize title page and captions

## 📈 Benefits

### **For Content Creation:**
✅ **Consistent Quality** - Curated selection ensures best images  
✅ **Time Saving** - Automatic selection and PDF creation  
✅ **Professional Output** - Ready-to-use marketing materials  
✅ **Portfolio Building** - Growing collection of curated work  

### **For Marketing:**
✅ **Weekly Content** - Regular high-quality posts  
✅ **Diverse Styles** - Showcase different artistic approaches  
✅ **Professional Presentation** - PDF format for clients  
✅ **Brand Consistency** - Unified styling and captions  

### **For Business:**
✅ **Scalable Content** - Automated generation and curation  
✅ **Cost Effective** - No manual selection required  
✅ **Quality Control** - Consistent output standards  
✅ **Market Ready** - Immediate use for sales and marketing  

## 🔍 Monitoring & Analytics

### **Weekly Reports Include:**
- Total images generated
- Images selected for curation
- Style distribution
- Generation dates
- Selection criteria used

### **Quality Metrics:**
- Success rate per style
- Image generation consistency
- Selection diversity
- PDF creation success

## 🚀 Getting Started

### **1. Automatic Setup:**
The weekly curator is automatically included in the GitHub Actions workflow. No additional setup required.

### **2. Manual Testing:**
```bash
python weekly_curator.py
```

### **3. Customization:**
Edit `weekly_curator.py` to modify:
- Selection criteria
- PDF layout
- Caption generation
- Output format

## 📋 Weekly Workflow

### **Thursday 4:00 AM UTC:**
1. **Daily Generation** - Creates 80 new images
2. **Weekly Curation** - Selects best 10 from past week
3. **PDF Creation** - Generates curated collection
4. **Summary Report** - Creates detailed analysis
5. **Repository Update** - Commits all content
6. **Artifact Upload** - Makes content downloadable

### **Output:**
- **80 daily images** (8 styles × 10 images)
- **8 daily PDFs** (one per style)
- **1 weekly curated PDF** (best 10 images)
- **1 weekly summary** (detailed report)

## 🎨 Content Strategy

### **Social Media Posts:**
- **Daily:** Individual style highlights
- **Weekly:** Curated collection showcase
- **Monthly:** Style comparison posts

### **Marketing Materials:**
- **Client Proposals:** Weekly curated PDFs
- **Portfolio:** Growing collection of best work
- **Newsletters:** Weekly highlights
- **Sales:** Premium curated content

This system ensures you always have high-quality, curated content ready for any marketing or business need! 