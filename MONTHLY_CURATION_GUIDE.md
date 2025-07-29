# Monthly Curation System Guide

## 🎯 Overview

The monthly curation system automatically collects **ALL images** generated in the current month and creates a comprehensive monthly PDF on the **last day of the month at 4:00 AM UTC**. This creates a complete archive and portfolio of your monthly AI architecture work.

## ⏰ Schedule

- **Daily Generation:** Every day at 4:00 AM UTC
- **Weekly Curation:** Every Thursday at 4:00 AM UTC
- **Monthly Curation:** Last day of each month at 4:00 AM UTC
- **Collection Period:** 1st to last day of the current month

## 🔄 How It Works

### **1. Daily Generation (Every Day)**
- Generates 8 styles × 10 images = **80 images daily**
- Saves images with timestamps in `images/` folder
- Stores captions in `captions/` folder for later use

### **2. Weekly Curation (Thursdays)**
- Selects best 10 images from Monday to Sunday
- Creates curated PDF with professional layout
- Generates summary report

### **3. Monthly Curation (Last Day of Month)**
- Collects ALL images from the entire month
- Organizes by style for comprehensive presentation
- Creates complete monthly archive PDF
- Generates detailed monthly summary

## 🎨 Monthly PDF Features

### **Title Page:**
- "ASK Monthly Collection"
- Month and year
- Complete collection statement
- Total images and styles count
- Professional branding

### **Style Index Page:**
- Complete list of all styles
- Image count per style
- Easy navigation reference

### **Style Sections:**
- **Style Header Page** - Introduction to each style
- **All Images** - Complete collection organized by style
- **Chronological Order** - Images sorted by generation date
- **Professional Captions** - Detailed information for each image

### **Comprehensive Summary:**
- Complete image list
- Style distribution
- Daily generation patterns
- Monthly statistics

## 📁 Output Structure

### **Monthly Content:**
```
monthly_curated/
├── ASK Monthly Collection_December 2024.pdf
├── monthly_summary_202412.txt
└── ...
```

### **PDF Structure:**
1. **Title Page** - Monthly overview
2. **Style Index** - Complete style listing
3. **Style Sections** - Each style with all its images
4. **Comprehensive Archive** - Every image from the month

## 📊 Monthly Statistics

### **Typical Monthly Output:**
- **~2,400 images** (30 days × 80 images/day)
- **8 styles** represented
- **~300 images per style** (average)
- **Complete chronological archive**

### **Summary Report Includes:**
- Total images generated
- Images per style breakdown
- Daily distribution patterns
- Generation dates and times
- Complete file listing

## 🎯 Marketing Strategy

### **Perfect for:**
- **Monthly portfolio updates** - Complete body of work
- **Client presentations** - Comprehensive collections
- **Archival purposes** - Complete monthly records
- **Style analysis** - Compare monthly trends
- **Business reporting** - Monthly content metrics

### **Content Strategy:**
- **Monthly showcases** - "This month's complete collection"
- **Style evolution** - Track changes over time
- **Portfolio building** - Growing monthly archives
- **Client proposals** - Comprehensive work samples

## ⚙️ Configuration

### **Environment Variables:**
```bash
# Monthly Curator Settings
MONTHLY_OUTPUT_PATH=monthly_curated
MONTHLY_TITLE_TEMPLATE=ASK Monthly Collection: {month_name} {year}

# Caption Settings
CAPTION_POSITION=bottom
CAPTION_FONT_SIZE=12
CAPTION_LINE_SPACING=16
```

### **Customization Options:**
- **PDF layout** - Modify title pages and captions
- **Organization** - Change style grouping
- **Caption content** - Customize image descriptions
- **Output format** - Adjust PDF structure

## 📈 Benefits

### **For Content Creation:**
✅ **Complete Archive** - Every image preserved and organized  
✅ **Professional Presentation** - Ready-to-use monthly collections  
✅ **Portfolio Building** - Growing monthly archives  
✅ **Style Analysis** - Track trends and preferences  

### **For Marketing:**
✅ **Monthly Showcases** - Complete body of work  
✅ **Client Presentations** - Comprehensive collections  
✅ **Business Reporting** - Monthly content metrics  
✅ **Archival Records** - Complete monthly documentation  

### **For Business:**
✅ **Scalable Archives** - Automatic monthly collections  
✅ **Quality Control** - Complete monthly overview  
✅ **Client Deliverables** - Professional monthly reports  
✅ **Portfolio Growth** - Continuous archive building  

## 🔍 Monitoring & Analytics

### **Monthly Reports Include:**
- Total images generated
- Images per style
- Daily generation patterns
- Style distribution
- Complete file listing
- Generation timeline

### **Quality Metrics:**
- Monthly generation consistency
- Style diversity maintenance
- Image quality trends
- Archive completeness

## 🚀 Getting Started

### **1. Automatic Setup:**
The monthly curator is automatically included in the GitHub Actions workflow. No additional setup required.

### **2. Manual Testing:**
```bash
python monthly_curator.py
```

### **3. Customization:**
Edit `monthly_curator.py` to modify:
- PDF layout and structure
- Caption generation
- Style organization
- Output format

## 📋 Monthly Workflow

### **Last Day of Month 4:00 AM UTC:**
1. **Daily Generation** - Creates 80 new images
2. **Monthly Collection** - Gathers all month's images
3. **Style Organization** - Groups by artistic style
4. **PDF Creation** - Generates comprehensive archive
5. **Summary Report** - Creates detailed analysis
6. **Repository Update** - Commits all content
7. **Artifact Upload** - Makes content downloadable

### **Output:**
- **80 daily images** (8 styles × 10 images)
- **8 caption files** (one per style)
- **1 weekly curated PDF** (best 10 images)
- **1 monthly comprehensive PDF** (all images)
- **1 monthly summary** (detailed report)

## 🎨 Content Strategy

### **Monthly Marketing:**
- **Portfolio Updates** - Complete monthly collections
- **Client Presentations** - Comprehensive work samples
- **Style Analysis** - Monthly trend reports
- **Archive Building** - Growing content library

### **Business Applications:**
- **Monthly Reports** - Content generation metrics
- **Client Deliverables** - Professional collections
- **Portfolio Growth** - Continuous archive building
- **Style Evolution** - Track artistic development

## 📊 Monthly Archive Benefits

### **Complete Documentation:**
- Every generated image preserved
- Chronological organization
- Style-based grouping
- Professional presentation

### **Portfolio Building:**
- Growing monthly archives
- Professional collections
- Client-ready presentations
- Style evolution tracking

### **Business Intelligence:**
- Monthly generation metrics
- Style preference analysis
- Content quality trends
- Archive completeness

This system ensures you have a complete, professional archive of every month's AI architecture work, perfect for portfolio building, client presentations, and business reporting! 