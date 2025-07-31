#!/usr/bin/env python3
"""
Manual Source Addition Tool for ASK Daily Architectural Research Zine
Add architectural RSS feeds manually to expand content sources
"""

import os
import json
import argparse
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv('ask.env')

def load_existing_sources():
    """Load existing architectural sources"""
    existing_feeds_file = os.getenv('EXISTING_FEEDS_FILE', 'existing_architectural_feeds.json')
    existing_feeds = []
    
    if os.path.exists(existing_feeds_file):
        try:
            with open(existing_feeds_file, 'r') as f:
                existing_feeds = json.load(f)
            print(f"✅ Loaded {len(existing_feeds)} existing sources")
        except Exception as e:
            print(f"⚠️ Error loading existing sources: {e}")
    
    return existing_feeds

def save_sources(sources):
    """Save sources to JSON file"""
    existing_feeds_file = os.getenv('EXISTING_FEEDS_FILE', 'existing_architectural_feeds.json')
    
    try:
        with open(existing_feeds_file, 'w') as f:
            json.dump(sources, f, indent=2)
        print(f"✅ Saved {len(sources)} sources to {existing_feeds_file}")
        return True
    except Exception as e:
        print(f"❌ Error saving sources: {e}")
        return False

def add_source(name, url, category):
    """Add a single source"""
    existing_feeds = load_existing_sources()
    
    # Check if source already exists
    for feed in existing_feeds:
        if feed.get('name') == name:
            print(f"⚠️ Source '{name}' already exists")
            return False
    
    # Add new source
    new_source = {
        "name": name,
        "url": url,
        "category": category,
        "added_at": datetime.now().isoformat()
    }
    
    existing_feeds.append(new_source)
    
    if save_sources(existing_feeds):
        print(f"✅ Added source: {name} ({category})")
        return True
    return False

def list_sources():
    """List all current sources"""
    existing_feeds = load_existing_sources()
    
    if not existing_feeds:
        print("📊 No sources found")
        return
    
    # Group by category
    categories = {}
    for feed in existing_feeds:
        category = feed.get('category', 'Additional')
        if category not in categories:
            categories[category] = []
        categories[category].append(feed)
    
    print(f"📊 Current Sources ({len(existing_feeds)} total):")
    print("=" * 50)
    
    for category, feeds in categories.items():
        print(f"\n🏷️  {category} ({len(feeds)} sources):")
        for feed in feeds:
            added_at = feed.get('added_at', 'Unknown')
            if added_at != 'Unknown':
                added_at = datetime.fromisoformat(added_at).strftime('%Y-%m-%d')
            print(f"   • {feed['name']} (added: {added_at})")
            print(f"     URL: {feed['url']}")

def remove_source(name):
    """Remove a source by name"""
    existing_feeds = load_existing_sources()
    
    # Find and remove source
    for i, feed in enumerate(existing_feeds):
        if feed.get('name') == name:
            removed = existing_feeds.pop(i)
            if save_sources(existing_feeds):
                print(f"✅ Removed source: {name}")
                return True
    
    print(f"❌ Source '{name}' not found")
    return False

def add_batch_sources():
    """Add multiple sources from a predefined list"""
    batch_sources = [
        # Academic & Research Institutions
        {"name": "AA School of Architecture", "url": "https://www.aaschool.ac.uk/feed", "category": "Academic"},
        {"name": "Berlage Institute", "url": "https://theberlage.nl/feed", "category": "Academic"},
        {"name": "TU Delft Architecture", "url": "https://www.tudelft.nl/en/architecture-and-the-built-environment/feed", "category": "Academic"},
        {"name": "UCL Bartlett", "url": "https://www.ucl.ac.uk/bartlett/feed", "category": "Academic"},
        {"name": "Cornell Architecture", "url": "https://aap.cornell.edu/feed", "category": "Academic"},
        {"name": "Princeton Architecture", "url": "https://soa.princeton.edu/feed", "category": "Academic"},
        {"name": "UC Berkeley Architecture", "url": "https://ced.berkeley.edu/architecture/feed", "category": "Academic"},
        
        # International Publications
        {"name": "Architectural Review Asia Pacific", "url": "https://www.architectural-review.com/feed", "category": "International"},
        {"name": "Architecture Australia", "url": "https://architectureau.com/feed", "category": "International"},
        {"name": "Canadian Architect", "url": "https://www.canadianarchitect.com/feed", "category": "International"},
        {"name": "Architectural Digest India", "url": "https://www.architecturaldigest.in/feed", "category": "International"},
        {"name": "Architectural Digest Middle East", "url": "https://www.architecturaldigestme.com/feed", "category": "International"},
        {"name": "Architectural Digest China", "url": "https://www.architecturaldigest.cn/feed", "category": "International"},
        
        # Specialized Research
        {"name": "Architectural Science Review", "url": "https://www.tandfonline.com/feed/rss/rjar20", "category": "Research"},
        {"name": "Journal of Architectural Education", "url": "https://www.tandfonline.com/feed/rss/rjae20", "category": "Research"},
        {"name": "Architecture Research Quarterly", "url": "https://www.cambridge.org/core/journals/architecture-research-quarterly/feed", "category": "Research"},
        {"name": "International Journal of Architectural Computing", "url": "https://journals.sagepub.com/feed/ijac", "category": "Research"},
        
        # Innovation & Technology
        {"name": "Archinect", "url": "https://archinect.com/feed", "category": "Innovation"},
        {"name": "Architecture Lab", "url": "https://www.architecturelab.net/feed", "category": "Innovation"},
        {"name": "Architecture Now", "url": "https://architecturenow.co.nz/feed", "category": "Innovation"},
        {"name": "Architecture & Design", "url": "https://www.architectureanddesign.com.au/feed", "category": "Innovation"},
        
        # Regional & Cultural
        {"name": "Architect Magazine", "url": "https://www.architectmagazine.com/rss", "category": "Regional"},
        {"name": "Architecture Week", "url": "https://www.architectureweek.com/feed", "category": "Regional"},
        
        # Emerging & Alternative
        {"name": "Architecture Foundation", "url": "https://architecturefoundation.org.uk/feed", "category": "Emerging"},
        {"name": "Architectural League", "url": "https://archleague.org/feed", "category": "Emerging"},
        {"name": "Storefront for Art and Architecture", "url": "https://storefrontnews.org/feed", "category": "Emerging"},
        {"name": "Architecture for Humanity", "url": "https://architectureforhumanity.org/feed", "category": "Emerging"},
        
        # Digital & Computational
        {"name": "Digital Architecture", "url": "https://digitalarchitecture.org/feed", "category": "Digital"},
        {"name": "Computational Architecture", "url": "https://computationalarchitecture.net/feed", "category": "Digital"},
        {"name": "Parametric Architecture", "url": "https://parametric-architecture.com/feed", "category": "Digital"},
        {"name": "Architecture and Computation", "url": "https://architectureandcomputation.com/feed", "category": "Digital"}
    ]
    
    existing_feeds = load_existing_sources()
    added_count = 0
    
    for source in batch_sources:
        # Check if already exists
        exists = any(feed.get('name') == source['name'] for feed in existing_feeds)
        
        if not exists:
            source['added_at'] = datetime.now().isoformat()
            existing_feeds.append(source)
            added_count += 1
            print(f"✅ Added: {source['name']} ({source['category']})")
        else:
            print(f"⚠️ Skipped: {source['name']} (already exists)")
    
    if save_sources(existing_feeds):
        print(f"\n🎉 Successfully added {added_count} new sources!")
        print(f"📊 Total sources: {len(existing_feeds)}")
    else:
        print("❌ Error saving sources")

def main():
    parser = argparse.ArgumentParser(description="Manual Source Addition Tool")
    parser.add_argument('--list', action='store_true', help='List all current sources')
    parser.add_argument('--add', nargs=3, metavar=('NAME', 'URL', 'CATEGORY'), help='Add a single source')
    parser.add_argument('--remove', type=str, help='Remove a source by name')
    parser.add_argument('--batch', action='store_true', help='Add batch of predefined sources')
    
    args = parser.parse_args()
    
    if args.list:
        list_sources()
    elif args.add:
        name, url, category = args.add
        add_source(name, url, category)
    elif args.remove:
        remove_source(args.remove)
    elif args.batch:
        add_batch_sources()
    else:
        print("🔧 Manual Source Addition Tool")
        print("=" * 40)
        print("Usage:")
        print("  python add_manual_sources.py --list                    # List all sources")
        print("  python add_manual_sources.py --add NAME URL CATEGORY   # Add single source")
        print("  python add_manual_sources.py --remove NAME             # Remove source")
        print("  python add_manual_sources.py --batch                   # Add batch sources")
        print("\nCategories: Academic, Research, International, Innovation, Regional, Emerging, Digital")

if __name__ == "__main__":
    main() 