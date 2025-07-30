import requests
import json
import os
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import time
import random
from dotenv import load_dotenv
import logging
from tqdm import tqdm

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
            'User-Agent': os.getenv('SCRAPER_USER_AGENT', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
        })
        self.content_dir = os.getenv('SCRAPER_CONTENT_DIR', 'scraped_content')
        self.timeout = int(os.getenv('SCRAPER_TIMEOUT', '15'))
        self.max_retries = int(os.getenv('SCRAPER_MAX_RETRIES', '3'))
        self.max_workers = int(os.getenv('SCRAPER_MAX_WORKERS', '4'))
        self.articles_per_source = int(os.getenv('SCRAPER_ARTICLES_PER_SOURCE', '10'))
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
    
    def extract_article_data(self, article_elem, source_name, category="Architecture"):
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
            logger.warning(f"⚠️ Error extracting article data: {e}")
            return None

    def scrape_archdaily(self):
        """Scrape articles from ArchDaily"""
        url = "https://www.archdaily.com/"
        response = self.safe_request(url)
        if not response:
            return []
            
        soup = BeautifulSoup(response.content, 'html.parser')
        articles = []
        
        # Look for article elements
        article_elements = soup.find_all(['article', 'div'], class_=lambda x: x and any(word in x.lower() for word in ['post', 'article', 'story', 'entry', 'feed']))
        
        for elem in article_elements[:self.articles_per_source]:  # Limit to configured number of articles
            article_data = self.extract_article_data(elem, "ArchDaily", "Architecture")
            if article_data:
                articles.append(article_data)
                
        logger.info(f"✅ Scraped {len(articles)} articles from ArchDaily")
        return articles



    def scrape_designboom(self):
        """Scrape articles from Designboom"""
        url = "https://www.designboom.com/"
        response = self.safe_request(url)
        if not response:
            return []
            
        soup = BeautifulSoup(response.content, 'html.parser')
        articles = []
        
        # Look for article elements
        article_elements = soup.find_all(['article', 'div'], class_=lambda x: x and any(word in x.lower() for word in ['post', 'article', 'story', 'entry', 'feed']))
        
        for elem in article_elements[:self.articles_per_source]:  # Limit to configured number of articles
            article_data = self.extract_article_data(elem, "Designboom", "Design")
            if article_data:
                articles.append(article_data)
                
        logger.info(f"✅ Scraped {len(articles)} articles from Designboom")
        return articles



    def scrape_architizer(self):
        """Scrape articles from Architizer"""
        url = "https://architizer.com/"
        response = self.safe_request(url)
        if not response:
            return []
            
        soup = BeautifulSoup(response.content, 'html.parser')
        articles = []
        
        # Look for article elements
        article_elements = soup.find_all(['article', 'div'], class_=lambda x: x and any(word in x.lower() for word in ['post', 'article', 'story', 'entry', 'feed']))
        
        for elem in article_elements[:self.articles_per_source]:  # Limit to configured number of articles
            article_data = self.extract_article_data(elem, "Architizer", "Architecture")
            if article_data:
                articles.append(article_data)
                
        logger.info(f"✅ Scraped {len(articles)} articles from Architizer")
        return articles



    def scrape_interior_design(self):
        """Scrape articles from Interior Design Magazine"""
        url = "https://www.interiordesign.net/"
        response = self.safe_request(url)
        if not response:
            return []
            
        soup = BeautifulSoup(response.content, 'html.parser')
        articles = []
        
        # Look for article elements
        article_elements = soup.find_all(['article', 'div'], class_=lambda x: x and any(word in x.lower() for word in ['post', 'article', 'story', 'entry', 'feed']))
        
        for elem in article_elements[:self.articles_per_source]:  # Limit to configured number of articles
            article_data = self.extract_article_data(elem, "Interior Design", "Interior Design")
            if article_data:
                articles.append(article_data)
                
        logger.info(f"✅ Scraped {len(articles)} articles from Interior Design")
        return articles

    def scrape_architectural_record(self):
        """Scrape articles from Architectural Record"""
        url = "https://www.architecturalrecord.com/"
        response = self.safe_request(url)
        if not response:
            return []
            
        soup = BeautifulSoup(response.content, 'html.parser')
        articles = []
        
        # Look for article elements
        article_elements = soup.find_all(['article', 'div'], class_=lambda x: x and any(word in x.lower() for word in ['post', 'article', 'story', 'entry', 'feed']))
        
        for elem in article_elements[:self.articles_per_source]:  # Limit to configured number of articles
            article_data = self.extract_article_data(elem, "Architectural Record", "Architecture")
            if article_data:
                articles.append(article_data)
                
        logger.info(f"✅ Scraped {len(articles)} articles from Architectural Record")
        return articles

    def scrape_all_sources(self):
        """Scrape articles from all architectural sources sequentially"""
        sources = [
            ('ArchDaily', self.scrape_archdaily),
            ('DesignBoom', self.scrape_designboom),
            ('Architizer', self.scrape_architizer),
            ('Interior Design', self.scrape_interior_design),
            ('Architectural Record', self.scrape_architectural_record)
        ]
        
        all_articles = []
        
        # Scrape sources sequentially with progress bar
        with tqdm(total=len(sources), desc=f"📡 Scraping sources", unit="source", 
                  bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]') as pbar:
            
            for source_name, source_func in sources:
                pbar.set_description(f"📡 Scraping {source_name}")
                try:
                    articles = source_func()
                    all_articles.extend(articles)
                    pbar.set_postfix_str(f"✅ {len(articles)} articles")
                    time.sleep(2)  # Rate limiting between sources
                except Exception as e:
                    pbar.set_postfix_str(f"❌ Error")
                    logger.error(f"❌ Error scraping {source_name}: {e}")
                
                pbar.update(1)
        
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
        """Save articles to JSON file"""
        filepath = os.path.join(self.content_dir, filename)
        
        # Load existing content if file exists
        existing_articles = []
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    existing_articles = json.load(f)
            except Exception as e:
                logger.warning(f"⚠️ Could not load existing content: {e}")
        
        # Combine existing and new articles
        all_articles = existing_articles + articles
        
        # Remove duplicates based on title
        seen_titles = set()
        unique_articles = []
        for article in all_articles:
            if article['title'] not in seen_titles:
                seen_titles.add(article['title'])
                unique_articles.append(article)
        
        # Save to file
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(unique_articles, f, indent=2, ensure_ascii=False)
            logger.info(f"✅ Saved {len(unique_articles)} articles to {filename}")
        except Exception as e:
            logger.error(f"❌ Error saving content: {e}")

    def run_daily_scraping(self):
        """Run the daily scraping process"""
        logger.info("Starting daily web scraping...")
        
        # Scrape all sources
        articles = self.scrape_all_sources()
        
        if articles:
            # Save daily content
            self.save_content(articles, 'daily_content.json')
            
            # Update rolling content files
            self.update_rolling_content(articles)
            
            logger.info(f"Daily scraping completed. Scraped {len(articles)} articles.")
        else:
            logger.warning("⚠️ No articles scraped today")

    def update_rolling_content(self, new_articles):
        """Update weekly, monthly, and yearly content files"""
        # Update weekly content (last 7 days)
        self.save_content(new_articles, 'weekly_content.json')
        
        # Update monthly content (last 30 days)
        self.save_content(new_articles, 'monthly_content.json')
        
        # Update yearly content (last 365 days)
        self.save_content(new_articles, 'yearly_content.json')

def main():
    """Main function to run the scraper"""
    scraper = WebScraper()
    scraper.run_daily_scraping()

if __name__ == "__main__":
    main() 