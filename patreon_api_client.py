#!/usr/bin/env python3
"""
Patreon API Client
Handles automated posting, analytics, and patron management.
"""

import os
import sys
import requests
import json
import logging
import time
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv('ask.env')

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

class PatreonAPIClient:
    def __init__(self):
        self.client_id = os.getenv("PATREON_CLIENT_ID")
        self.client_secret = os.getenv("PATREON_CLIENT_SECRET")
        self.access_token = os.getenv("PATREON_ACCESS_TOKEN")
        self.refresh_token = os.getenv("PATREON_REFRESH_TOKEN")
        self.campaign_id = os.getenv("PATREON_CAMPAIGN_ID")
        
        self.base_url = "https://www.patreon.com/api/oauth2/v2"
        self.session = requests.Session()
        
        if not all([self.client_id, self.client_secret, self.access_token]):
            log.error("❌ Missing Patreon API credentials")
            raise ValueError("Patreon API credentials not configured")
    
    def _get_headers(self):
        """Get headers for API requests"""
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
    
    def refresh_access_token(self):
        """Refresh access token if expired"""
        try:
            response = requests.post("https://www.patreon.com/api/oauth2/token", data={
                "grant_type": "refresh_token",
                "refresh_token": self.refresh_token,
                "client_id": self.client_id,
                "client_secret": self.client_secret
            })
            
            if response.status_code == 200:
                data = response.json()
                self.access_token = data["access_token"]
                self.refresh_token = data.get("refresh_token", self.refresh_token)
                
                # Update environment variables
                os.environ["PATREON_ACCESS_TOKEN"] = self.access_token
                os.environ["PATREON_REFRESH_TOKEN"] = self.refresh_token
                
                log.info("✅ Patreon access token refreshed")
                return True
            else:
                log.error(f"❌ Failed to refresh token: {response.status_code}")
                return False
                
        except Exception as e:
            log.error(f"❌ Error refreshing token: {e}")
            return False
    
    def get_campaign_info(self):
        """Get campaign information"""
        try:
            url = f"{self.base_url}/campaigns/{self.campaign_id}"
            response = self.session.get(url, headers=self._get_headers())
            
            if response.status_code == 200:
                data = response.json()
                log.info(f"✅ Campaign: {data['data']['attributes']['name']}")
                return data
            else:
                log.error(f"❌ Failed to get campaign: {response.status_code}")
                return None
                
        except Exception as e:
            log.error(f"❌ Error getting campaign: {e}")
            return None
    
    def get_patrons(self):
        """Get list of patrons"""
        try:
            url = f"{self.base_url}/members"
            params = {
                "include": "user,currently_entitled_tiers",
                "fields[member]": "patron_status,last_charge_status,last_charge_date,pledge_relationship_start,lifetime_support_cents,currently_entitled_amount_cents,patron_tier",
                "fields[user]": "social_connections,about,created,email,first_name,full_name,image_url,last_name,thumb_url,url,vanity",
                "fields[tier]": "amount_cents,created,description,discord_role_ids,edited,image_url,patron_count,post_count,published,published_at,remaining,requires_shipping,title,url"
            }
            
            response = self.session.get(url, headers=self._get_headers(), params=params)
            
            if response.status_code == 200:
                data = response.json()
                patrons = data.get("data", [])
                log.info(f"✅ Found {len(patrons)} patrons")
                return patrons
            else:
                log.error(f"❌ Failed to get patrons: {response.status_code}")
                return []
                
        except Exception as e:
            log.error(f"❌ Error getting patrons: {e}")
            return []
    
    def create_post(self, title, content, image_path=None, tier_ids=None, is_paid=False):
        """Create a new post on Patreon"""
        try:
            url = f"{self.base_url}/posts"
            
            post_data = {
                "data": {
                    "type": "post",
                    "attributes": {
                        "title": title,
                        "content": content,
                        "is_paid": is_paid,
                        "is_public": True
                    },
                    "relationships": {
                        "campaign": {
                            "data": {
                                "id": self.campaign_id,
                                "type": "campaign"
                            }
                        }
                    }
                }
            }
            
            # Add tier restrictions if specified
            if tier_ids:
                post_data["data"]["relationships"]["access_rules"] = {
                    "data": [{"id": tier_id, "type": "access_rule"} for tier_id in tier_ids]
                }
            
            response = self.session.post(url, headers=self._get_headers(), json=post_data)
            
            if response.status_code == 201:
                data = response.json()
                post_id = data["data"]["id"]
                log.info(f"✅ Created post: {post_id}")
                
                # Upload image if provided
                if image_path and os.path.exists(image_path):
                    self.upload_post_image(post_id, image_path)
                
                return post_id
            else:
                log.error(f"❌ Failed to create post: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            log.error(f"❌ Error creating post: {e}")
            return None
    
    def upload_post_image(self, post_id, image_path):
        """Upload image to a post"""
        try:
            # Get upload URL
            url = f"{self.base_url}/posts/{post_id}/media"
            
            with open(image_path, 'rb') as f:
                files = {'file': f}
                response = self.session.post(url, headers=self._get_headers(), files=files)
            
            if response.status_code == 201:
                log.info(f"✅ Uploaded image to post {post_id}")
                return True
            else:
                log.error(f"❌ Failed to upload image: {response.status_code}")
                return False
                
        except Exception as e:
            log.error(f"❌ Error uploading image: {e}")
            return False
    
    def get_post_analytics(self, post_id):
        """Get analytics for a specific post"""
        try:
            url = f"{self.base_url}/posts/{post_id}/analytics"
            response = self.session.get(url, headers=self._get_headers())
            
            if response.status_code == 200:
                data = response.json()
                log.info(f"✅ Got analytics for post {post_id}")
                return data
            else:
                log.error(f"❌ Failed to get analytics: {response.status_code}")
                return None
                
        except Exception as e:
            log.error(f"❌ Error getting analytics: {e}")
            return None
    
    def get_posts(self, limit=20):
        """Get recent posts"""
        try:
            url = f"{self.base_url}/posts"
            params = {
                "filter[campaign_id]": self.campaign_id,
                "sort": "-published_at",
                "page[count]": limit
            }
            
            response = self.session.get(url, headers=self._get_headers(), params=params)
            
            if response.status_code == 200:
                data = response.json()
                posts = data.get("data", [])
                log.info(f"✅ Found {len(posts)} posts")
                return posts
            else:
                log.error(f"❌ Failed to get posts: {response.status_code}")
                return []
                
        except Exception as e:
            log.error(f"❌ Error getting posts: {e}")
            return []

def create_patreon_post(image_info, caption):
    """Create a Patreon post with image and caption"""
    try:
        client = PatreonAPIClient()
        
        # Create post title
        title = f"Daily Architectural Art - {datetime.now().strftime('%B %d, %Y')}"
        
        # Format caption for Patreon
        patreon_content = f"{caption}\n\n"
        patreon_content += "🏗️ Exploring the intersection of form, function, and artistic vision.\n"
        patreon_content += "📐 Where mathematics meets creativity in built environments.\n\n"
        patreon_content += "Support this project to get access to weekly, monthly, and yearly PDF collections! 🎨"
        
        # Create post
        post_id = client.create_post(
            title=title,
            content=patreon_content,
            image_path=image_info['path'],
            is_paid=False  # Free post to attract patrons
        )
        
        if post_id:
            log.info(f"✅ Successfully posted to Patreon: {post_id}")
            return post_id
        else:
            log.error("❌ Failed to create Patreon post")
            return None
            
    except Exception as e:
        log.error(f"❌ Error creating Patreon post: {e}")
        return None

def get_patreon_analytics():
    """Get Patreon campaign analytics"""
    try:
        client = PatreonAPIClient()
        
        # Get campaign info
        campaign = client.get_campaign_info()
        if campaign:
            log.info(f"Campaign: {campaign['data']['attributes']['name']}")
        
        # Get patrons
        patrons = client.get_patrons()
        log.info(f"Total patrons: {len(patrons)}")
        
        # Get recent posts
        posts = client.get_posts(limit=10)
        log.info(f"Recent posts: {len(posts)}")
        
        return {
            'campaign': campaign,
            'patrons': patrons,
            'posts': posts
        }
        
    except Exception as e:
        log.error(f"❌ Error getting Patreon analytics: {e}")
        return None

if __name__ == "__main__":
    # Test Patreon API connection
    analytics = get_patreon_analytics()
    if analytics:
        print("✅ Patreon API integration working")
    else:
        print("❌ Patreon API integration failed") 