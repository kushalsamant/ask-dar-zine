import json
import os
from datetime import datetime, timedelta
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class DateFilter:
    def __init__(self, content_dir='scraped_content'):
        self.content_dir = content_dir
        
    def load_content(self, filename: str) -> List[Dict[str, Any]]:
        """Load content from JSON file"""
        filepath = os.path.join(self.content_dir, filename)
        
        if not os.path.exists(filepath):
            logger.warning(f"Content file {filename} not found")
            return []
            
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = json.load(f)
            logger.info(f"Loaded {len(content)} articles from {filename}")
            return content
        except Exception as e:
            logger.error(f"Error loading {filename}: {e}")
            return []
            
    def filter_by_date_range(self, content: List[Dict[str, Any]], days_back: int) -> List[Dict[str, Any]]:
        """Filter content by date range"""
        if not content:
            return []
            
        cutoff_date = datetime.now() - timedelta(days=days_back)
        filtered_content = []
        
        for article in content:
            try:
                # Parse timestamp
                if 'timestamp' in article:
                    article_date = datetime.fromisoformat(article['timestamp'].replace('Z', '+00:00'))
                    if article_date >= cutoff_date:
                        filtered_content.append(article)
                else:
                    # If no timestamp, include it (for backward compatibility)
                    filtered_content.append(article)
            except Exception as e:
                logger.warning(f"Error parsing timestamp for article: {e}")
                # Include articles with invalid timestamps
                filtered_content.append(article)
                
        logger.info(f"Filtered {len(filtered_content)} articles from last {days_back} days")
        return filtered_content
        
    def get_daily_content(self) -> List[Dict[str, Any]]:
        """Get content from last 24 hours"""
        content = self.load_content('daily_content.json')
        return self.filter_by_date_range(content, 1)
        
    def get_weekly_content(self) -> List[Dict[str, Any]]:
        """Get content from last 7 days"""
        content = self.load_content('weekly_content.json')
        return self.filter_by_date_range(content, 7)
        
    def get_monthly_content(self) -> List[Dict[str, Any]]:
        """Get content from last 30 days"""
        content = self.load_content('monthly_content.json')
        return self.filter_by_date_range(content, 30)
        
    def get_yearly_content(self) -> List[Dict[str, Any]]:
        """Get content from last 365 days"""
        content = self.load_content('yearly_content.json')
        return self.filter_by_date_range(content, 365)
        
    def extract_topics_from_content(self, content: List[Dict[str, Any]], max_topics: int) -> List[str]:
        """Extract unique topics from content"""
        topics = set()
        
        for article in content:
            title = article.get('title', '')
            category = article.get('category', '')
            
            # Extract key topics from title
            if title:
                # Simple topic extraction - can be enhanced with NLP
                words = title.lower().split()
                # Filter out common words and extract meaningful terms
                meaningful_words = [word for word in words if len(word) > 3 and word not in 
                                 ['the', 'and', 'for', 'with', 'this', 'that', 'from', 'have', 'will', 'been']]
                
                # Take first few meaningful words as topic
                if meaningful_words:
                    topic = ' '.join(meaningful_words[:3])
                    topics.add(topic)
                    
            # Add category as topic
            if category:
                topics.add(category)
                
        # Convert to list and limit to max_topics
        topic_list = list(topics)[:max_topics]
        logger.info(f"Extracted {len(topic_list)} unique topics")
        return topic_list
        
    def get_topics_for_issue(self, issue_type: str) -> List[str]:
        """Get topics for specific issue type"""
        if issue_type == 'daily':
            content = self.get_daily_content()
            max_topics = 10  # 10 images for social media only
        elif issue_type == 'weekly':
            content = self.get_weekly_content()
            max_topics = 7
        elif issue_type == 'monthly':
            content = self.get_monthly_content()
            max_topics = 31
        elif issue_type == 'yearly':
            content = self.get_yearly_content()
            max_topics = 366
        else:
            logger.error(f"Unknown issue type: {issue_type}")
            return []
            
        return self.extract_topics_from_content(content, max_topics)
        
    def get_content_for_issue(self, issue_type: str) -> List[Dict[str, Any]]:
        """Get content for specific issue type"""
        if issue_type == 'daily':
            return self.get_daily_content()
        elif issue_type == 'weekly':
            return self.get_weekly_content()
        elif issue_type == 'monthly':
            return self.get_monthly_content()
        elif issue_type == 'yearly':
            return self.get_yearly_content()
        else:
            logger.error(f"Unknown issue type: {issue_type}")
            return []
            
    def get_topic_registry(self) -> Dict[str, List[str]]:
        """Get topic registry to track used topics"""
        registry_file = os.path.join(self.content_dir, 'topic_registry.json')
        
        if os.path.exists(registry_file):
            try:
                with open(registry_file, 'r', encoding='utf-8') as f:
                    registry = json.load(f)
                return registry
            except Exception as e:
                logger.error(f"Error loading topic registry: {e}")
                
        return {'daily': [], 'weekly': [], 'monthly': [], 'yearly': []}
        
    def update_topic_registry(self, issue_type: str, topics: List[str]):
        """Update topic registry with new topics"""
        registry = self.get_topic_registry()
        
        if issue_type in registry:
            # Add new topics
            registry[issue_type].extend(topics)
            # Keep only recent topics (last 1000 to prevent file from growing too large)
            registry[issue_type] = registry[issue_type][-1000:]
        else:
            registry[issue_type] = topics
            
        # Save updated registry
        registry_file = os.path.join(self.content_dir, 'topic_registry.json')
        try:
            with open(registry_file, 'w', encoding='utf-8') as f:
                json.dump(registry, f, indent=2, ensure_ascii=False)
            logger.info(f"Updated topic registry for {issue_type}")
        except Exception as e:
            logger.error(f"Error saving topic registry: {e}")
            
    def get_unused_topics(self, issue_type: str, required_count: int) -> List[str]:
        """Get topics that haven't been used yet"""
        registry = self.get_topic_registry()
        used_topics = set(registry.get(issue_type, []))
        
        # Get all available topics for this issue type
        all_topics = self.get_topics_for_issue(issue_type)
        
        # Filter out used topics
        unused_topics = [topic for topic in all_topics if topic not in used_topics]
        
        # If we don't have enough unused topics, generate some fallback topics
        if len(unused_topics) < required_count:
            fallback_topics = self.generate_fallback_topics(required_count - len(unused_topics))
            unused_topics.extend(fallback_topics)
            
        return unused_topics[:required_count]
        
    def generate_fallback_topics(self, count: int) -> List[str]:
        """Generate fallback topics when scraping doesn't provide enough"""
        fallback_topics = [
            "Artificial Intelligence Ethics",
            "Climate Change Technology",
            "Space Exploration",
            "Quantum Computing",
            "Biotechnology Advances",
            "Renewable Energy",
            "Digital Privacy",
            "Cybersecurity",
            "Machine Learning",
            "Robotics Innovation",
            "Neuroscience Research",
            "Genetic Engineering",
            "Sustainable Technology",
            "Blockchain Applications",
            "Virtual Reality",
            "Augmented Reality",
            "Internet of Things",
            "5G Technology",
            "Autonomous Vehicles",
            "Smart Cities",
            "Clean Energy",
            "Ocean Conservation",
            "Wildlife Protection",
            "Medical Breakthroughs",
            "Drug Discovery",
            "Precision Medicine",
            "Nanotechnology",
            "Materials Science",
            "Astrophysics",
            "Particle Physics",
            "Earth Sciences"
        ]
        
        # Return random selection of fallback topics
        import random
        return random.sample(fallback_topics, min(count, len(fallback_topics)))

def main():
    """Test the date filter"""
    filter_obj = DateFilter()
    
    # Test getting content for different issue types
    print("Daily content:", len(filter_obj.get_daily_content()))
    print("Weekly content:", len(filter_obj.get_weekly_content()))
    print("Monthly content:", len(filter_obj.get_monthly_content()))
    print("Yearly content:", len(filter_obj.get_yearly_content()))
    
    # Test getting topics
    print("Daily topics:", filter_obj.get_topics_for_issue('daily'))
    print("Weekly topics:", filter_obj.get_topics_for_issue('weekly'))

if __name__ == "__main__":
    main() 