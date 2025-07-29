import requests
import json
import os
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import time
import random
from dotenv import load_dotenv
import logging
import concurrent.futures
from urllib.parse import urljoin, urlparse

# Load environment variables
load_dotenv('ask.env')

# Setup logging with better configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

class WebScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.content_dir = 'scraped_content'
        self.timeout = 15
        self.max_retries = 3
        self.ensure_content_dir()
        
    def ensure_content_dir(self):
        """Ensure the content directory exists"""
        if not os.path.exists(self.content_dir):
            os.makedirs(self.content_dir)
            logger.info(f"✅ Created content directory: {self.content_dir}")
    
    def safe_request(self, url, retries=None):
        """Make a safe HTTP request with retry logic"""
        if retries is None:
            retries = self.max_retries
            
        for attempt in range(retries):
            try:
                logger.info(f"📡 Fetching {url} (attempt {attempt + 1}/{retries})")
                response = self.session.get(url, timeout=self.timeout)
                response.raise_for_status()
                return response
            except requests.exceptions.Timeout:
                logger.warning(f"⚠️ Timeout for {url} (attempt {attempt + 1})")
                if attempt < retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
            except requests.exceptions.RequestException as e:
                logger.error(f"❌ Request failed for {url}: {e}")
                if attempt < retries - 1:
                    time.sleep(2 ** attempt)
            except Exception as e:
                logger.error(f"❌ Unexpected error for {url}: {e}")
                if attempt < retries - 1:
                    time.sleep(2 ** attempt)
        
        logger.error(f"❌ Failed to fetch {url} after {retries} attempts")
        return None
    
    def extract_article_data(self, article_elem, source_name, category="Technology"):
        """Extract article data from HTML element"""
        try:
            # Try different selectors for title
            title_elem = (
                article_elem.find('h1') or 
                article_elem.find('h2') or 
                article_elem.find('h3') or
                article_elem.find('a')
            )
            
            if not title_elem:
                return None
                
            title = title_elem.get_text(strip=True)
            if not title or len(title) < 10:  # Filter out very short titles
                return None
            
            # Get URL
            link = title_elem if title_elem.name == 'a' else title_elem.find('a')
            url = link.get('href') if link else None
            
            if url and not url.startswith('http'):
                # Handle relative URLs
                url = urljoin(f"https://{source_name.lower().replace(' ', '')}.com", url)
            
            if not url:
                return None
            
            return {
                'title': title,
                'url': url,
                'source': source_name,
                'timestamp': datetime.now().isoformat(),
                'category': category
            }
            
        except Exception as e:
            logger.debug(f"Failed to extract article data: {e}")
            return None
            
    def scrape_tech_crunch(self):
        """Scrape TechCrunch for tech news"""
        try:
            url = "https://techcrunch.com/"
            response = self.safe_request(url)
            if not response:
                return []
            
            soup = BeautifulSoup(response.content, 'html.parser')
            articles = []
            
            # Look for articles in various containers
            article_selectors = [
                'article',
                '.post-block',
                '.wp-block-tc23-post-picker-item'
            ]
            
            for selector in article_selectors:
                for article in soup.select(selector)[:10]:
                    article_data = self.extract_article_data(article, 'TechCrunch')
                    if article_data:
                        articles.append(article_data)
                        if len(articles) >= 10:
                            break
                if len(articles) >= 10:
                    break
            
            logger.info(f"✅ Scraped {len(articles)} articles from TechCrunch")
            return articles
            
        except Exception as e:
            logger.error(f"❌ Error scraping TechCrunch: {e}")
            return []
            
    def scrape_ars_technica(self):
        """Scrape Ars Technica for tech and science news"""
        try:
            url = "https://arstechnica.com/"
            response = self.safe_request(url)
            if not response:
                return []
            
            soup = BeautifulSoup(response.content, 'html.parser')
            articles = []
            
            # Look for articles in various containers
            article_selectors = [
                'article',
                '.listing',
                '.post'
            ]
            
            for selector in article_selectors:
                for article in soup.select(selector)[:10]:
                    article_data = self.extract_article_data(article, 'Ars Technica')
                    if article_data:
                        articles.append(article_data)
                        if len(articles) >= 10:
                            break
                if len(articles) >= 10:
                    break
            
            logger.info(f"✅ Scraped {len(articles)} articles from Ars Technica")
            return articles
            
        except Exception as e:
            logger.error(f"❌ Error scraping Ars Technica: {e}")
            return []
            
    def scrape_science_daily(self):
        """Scrape Science Daily for science news"""
        try:
            url = "https://www.sciencedaily.com/"
            response = self.safe_request(url)
            if not response:
                return []
            
            soup = BeautifulSoup(response.content, 'html.parser')
            articles = []
            
            # Look for latest headlines
            headline_selectors = [
                '.latest-head',
                '.headlines',
                'h3 a'
            ]
            
            for selector in headline_selectors:
                for headline in soup.select(selector)[:10]:
                    article_data = self.extract_article_data(headline, 'Science Daily', 'Science')
                    if article_data:
                        articles.append(article_data)
                        if len(articles) >= 10:
                            break
                if len(articles) >= 10:
                    break
            
            logger.info(f"✅ Scraped {len(articles)} articles from Science Daily")
            return articles
            
        except Exception as e:
            logger.error(f"❌ Error scraping Science Daily: {e}")
            return []
            
    def scrape_reddit_science(self):
        """Scrape Reddit r/science for trending topics"""
        try:
            url = "https://www.reddit.com/r/science/hot.json"
            response = self.session.get(url, timeout=10)
            data = response.json()
            
            articles = []
            for post in data['data']['children'][:10]:
                post_data = post['data']
                title = post_data.get('title', '')
                url = f"https://reddit.com{post_data.get('permalink', '')}"
                
                if title:
                    articles.append({
                        'title': title,
                        'url': url,
                        'source': 'Reddit r/science',
                        'timestamp': datetime.now().isoformat(),
                        'category': 'Science'
                    })
            
            return articles
        except Exception as e:
            logger.error(f"Error scraping Reddit: {e}")
            return []
            
    def scrape_wired(self):
        """Scrape Wired for tech and science news"""
        try:
            url = "https://www.wired.com/"
            response = self.safe_request(url)
            if not response:
                return []
            
            soup = BeautifulSoup(response.content, 'html.parser')
            articles = []
            
            # Look for articles in various containers
            article_selectors = [
                'article',
                '.listing',
                '.post'
            ]
            
            for selector in article_selectors:
                for article in soup.select(selector)[:10]:
                    article_data = self.extract_article_data(article, 'Wired')
                    if article_data:
                        articles.append(article_data)
                        if len(articles) >= 10:
                            break
                if len(articles) >= 10:
                    break
            
            logger.info(f"✅ Scraped {len(articles)} articles from Wired")
            return articles
            
        except Exception as e:
            logger.error(f"❌ Error scraping Wired: {e}")
            return []
            
    def scrape_verge(self):
        """Scrape The Verge for tech news"""
        try:
            url = "https://www.theverge.com/"
            response = self.safe_request(url)
            if not response:
                return []
            
            soup = BeautifulSoup(response.content, 'html.parser')
            articles = []
            
            # Look for articles in various containers
            article_selectors = [
                'article',
                '.listing',
                '.post'
            ]
            
            for selector in article_selectors:
                for article in soup.select(selector)[:10]:
                    article_data = self.extract_article_data(article, 'The Verge')
                    if article_data:
                        articles.append(article_data)
                        if len(articles) >= 10:
                            break
                if len(articles) >= 10:
                    break
            
            logger.info(f"✅ Scraped {len(articles)} articles from The Verge")
            return articles
            
        except Exception as e:
            logger.error(f"❌ Error scraping The Verge: {e}")
            return []
            
    def scrape_nature(self):
        """Scrape Nature for science news"""
        try:
            url = "https://www.nature.com/news"
            response = self.safe_request(url)
            if not response:
                return []
            
            soup = BeautifulSoup(response.content, 'html.parser')
            articles = []
            
            # Look for articles in various containers
            article_selectors = [
                'article',
                '.listing',
                '.post'
            ]
            
            for selector in article_selectors:
                for article in soup.select(selector)[:10]:
                    article_data = self.extract_article_data(article, 'Nature')
                    if article_data:
                        articles.append(article_data)
                        if len(articles) >= 10:
                            break
                if len(articles) >= 10:
                    break
            
            logger.info(f"✅ Scraped {len(articles)} articles from Nature")
            return articles
            
        except Exception as e:
            logger.error(f"❌ Error scraping Nature: {e}")
            return []
            
    def scrape_scientific_american(self):
        """Scrape Scientific American for science news"""
        try:
            url = "https://www.scientificamerican.com/"
            response = self.safe_request(url)
            if not response:
                return []
            
            soup = BeautifulSoup(response.content, 'html.parser')
            articles = []
            
            # Look for articles in various containers
            article_selectors = [
                'article',
                '.listing',
                '.post'
            ]
            
            for selector in article_selectors:
                for article in soup.select(selector)[:10]:
                    article_data = self.extract_article_data(article, 'Scientific American')
                    if article_data:
                        articles.append(article_data)
                        if len(articles) >= 10:
                            break
                if len(articles) >= 10:
                    break
            
            logger.info(f"✅ Scraped {len(articles)} articles from Scientific American")
            return articles
            
        except Exception as e:
            logger.error(f"❌ Error scraping Scientific American: {e}")
            return []
            
    def scrape_reddit_technology(self):
        """Scrape Reddit r/technology for trending tech topics"""
        try:
            url = "https://www.reddit.com/r/technology/hot.json"
            response = self.session.get(url, timeout=10)
            data = response.json()
            
            articles = []
            for post in data['data']['children'][:10]:
                post_data = post['data']
                title = post_data.get('title', '')
                url = f"https://reddit.com{post_data.get('permalink', '')}"
                
                if title:
                    articles.append({
                        'title': title,
                        'url': url,
                        'source': 'Reddit r/technology',
                        'timestamp': datetime.now().isoformat(),
                        'category': 'Technology'
                    })
            
            return articles
        except Exception as e:
            logger.error(f"Error scraping Reddit r/technology: {e}")
            return []
            
    def scrape_reddit_futurology(self):
        """Scrape Reddit r/Futurology for future tech topics"""
        try:
            url = "https://www.reddit.com/r/Futurology/hot.json"
            response = self.session.get(url, timeout=10)
            data = response.json()
            
            articles = []
            for post in data['data']['children'][:10]:
                post_data = post['data']
                title = post_data.get('title', '')
                url = f"https://reddit.com{post_data.get('permalink', '')}"
                
                if title:
                    articles.append({
                        'title': title,
                        'url': url,
                        'source': 'Reddit r/Futurology',
                        'timestamp': datetime.now().isoformat(),
                        'category': 'Technology'
                    })
            
            return articles
        except Exception as e:
            logger.error(f"Error scraping Reddit r/Futurology: {e}")
            return []
            
    def scrape_all_sources(self):
        """Scrape all sources and combine results"""
        logger.info("Starting web scraping from all sources...")
        
        all_articles = []
        
        # Scrape each source - 10 top sources
        sources = [
            self.scrape_tech_crunch,
            self.scrape_ars_technica,
            self.scrape_science_daily,
            self.scrape_wired,
            self.scrape_verge,
            self.scrape_nature,
            self.scrape_scientific_american,
            self.scrape_reddit_science,
            self.scrape_reddit_technology,
            self.scrape_reddit_futurology
        ]
        
        for source_func in sources:
            try:
                articles = source_func()
                all_articles.extend(articles)
                logger.info(f"Scraped {len(articles)} articles from {source_func.__name__}")
                time.sleep(random.uniform(1, 3))  # Be respectful to servers
            except Exception as e:
                logger.error(f"Error with {source_func.__name__}: {e}")
                
        # Remove duplicates based on title
        seen_titles = set()
        unique_articles = []
        for article in all_articles:
            if article['title'] not in seen_titles:
                seen_titles.add(article['title'])
                unique_articles.append(article)
                
        logger.info(f"Total unique articles scraped: {len(unique_articles)}")
        return unique_articles
        
    def save_content(self, articles, filename):
        """Save scraped content to JSON file"""
        filepath = os.path.join(self.content_dir, filename)
        
        # Load existing content if file exists
        existing_content = []
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    existing_content = json.load(f)
            except Exception as e:
                logger.error(f"Error loading existing content: {e}")
                
        # Add new articles
        all_content = existing_content + articles
        
        # Save to file
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(all_content, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved {len(articles)} articles to {filename}")
        except Exception as e:
            logger.error(f"Error saving content: {e}")
            
    def run_daily_scraping(self):
        """Run daily scraping and save content"""
        logger.info("Starting daily web scraping...")
        
        # Scrape all sources
        articles = self.scrape_all_sources()
        
        if articles:
            # Save to daily content file
            self.save_content(articles, 'daily_content.json')
            
            # Update rolling content files
            self.update_rolling_content(articles)
            
            logger.info(f"Daily scraping completed. Scraped {len(articles)} articles.")
        else:
            logger.warning("No articles scraped today.")
            
    def update_rolling_content(self, new_articles):
        """Update weekly, monthly, and yearly content files"""
        # Load existing content
        weekly_file = os.path.join(self.content_dir, 'weekly_content.json')
        monthly_file = os.path.join(self.content_dir, 'monthly_content.json')
        yearly_file = os.path.join(self.content_dir, 'yearly_content.json')
        
        # Add new articles to each file
        for filename in [weekly_file, monthly_file, yearly_file]:
            existing_content = []
            if os.path.exists(filename):
                try:
                    with open(filename, 'r', encoding='utf-8') as f:
                        existing_content = json.load(f)
                except Exception as e:
                    logger.error(f"Error loading {filename}: {e}")
                    
            # Add new articles
            all_content = existing_content + new_articles
            
            # Save updated content
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(all_content, f, indent=2, ensure_ascii=False)
                logger.info(f"Updated {filename}")
            except Exception as e:
                logger.error(f"Error saving {filename}: {e}")

def main():
    """Main function to run the scraper"""
    scraper = WebScraper()
    scraper.run_daily_scraping()

if __name__ == "__main__":
    main() 