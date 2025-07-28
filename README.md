# ASK Zine Generator

An AI-powered architectural zine generator that creates PDF zines from RSS feeds and AI-generated content.

## 🔐 Security Setup

**IMPORTANT**: This project uses API keys that should never be committed to version control.

### 1. Environment Setup

1. Copy the template file:
   ```bash
   cp ask.env.template ask.env
   ```

2. Edit `ask.env` and replace the placeholder values with your actual API keys:
   - `GROQ_API_KEY`: Get from https://console.groq.com/
   - `REPLICATE_API_TOKEN`: Get from https://replicate.com/account/api-tokens
   - `TOGETHER_API_KEY`: Get from https://together.ai/ (optional)

### 2. API Key Sources

**Required:**
- **Together AI**: Visit https://together.ai/ and create an API key (for text generation)
- **Replicate**: Visit https://replicate.com/account/api-tokens and create a token (for image generation)

**Optional:**
- **Groq**: Visit https://console.groq.com/ and create an API key (alternative to Together AI)

### 3. Verify .gitignore

The `.gitignore` file should exclude:
- `ask.env` (your actual API keys)
- `*.env` files
- `logs/` directory
- `output/` directory

## 🚀 Usage

### Option 1: Auto-install (Recommended)
```bash
python zine_generator_with_log.py [optional_theme]
```

### Option 2: Manual install
```bash
pip install -r requirements.txt
python zine_generator_with_log.py [optional_theme]
```

## 📁 Project Structure

- `zine_generator_with_log.py` - Main script with logging
- `ask.env` - Your API keys (not in git)
- `ask.env.template` - Template showing required variables
- `output/` - Generated PDFs (not in git)
- `logs/` - Log files (not in git)

## 🔧 Troubleshooting

If you get API errors:
1. Check that your API keys are valid and not expired
2. Ensure you have sufficient credits/quota
3. Verify the model names are correct

## 📝 License

MIT License 