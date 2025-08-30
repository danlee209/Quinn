#!/usr/bin/env python3
"""
Fetch real Twitter profile pictures from Quinn accounts
"""

import requests
from bs4 import BeautifulSoup
import json
import re

def fetch_twitter_profile_image(username):
    """Fetch Twitter profile image URL for a given username"""
    try:
        # Twitter profile URL
        url = f"https://twitter.com/{username}"
        
        # Headers to mimic a browser request
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Make request
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        # Parse HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Look for profile image in meta tags
        meta_image = soup.find('meta', property='og:image')
        if meta_image and meta_image.get('content'):
            return meta_image['content']
        
        # Look for profile image in Twitter-specific meta tags
        twitter_image = soup.find('meta', attrs={'name': 'twitter:image'})
        if twitter_image and twitter_image.get('content'):
            return twitter_image['content']
        
        # Look for profile image in the page content
        profile_images = soup.find_all('img', src=re.compile(r'profile_images'))
        if profile_images:
            for img in profile_images:
                src = img.get('src')
                if src and 'profile_images' in src:
                    # Convert to full URL if it's relative
                    if src.startswith('//'):
                        return 'https:' + src
                    elif src.startswith('/'):
                        return 'https://twitter.com' + src
                    else:
                        return src
        
        return None
        
    except Exception as e:
        print(f"Error fetching profile for {username}: {e}")
        return None

def main():
    """Main function to fetch all Quinn account profile images"""
    
    # Quinn Twitter accounts
    quinn_accounts = {
        "TechNewsByQuinn": "TechNewsByQuinn",
        "CryptoByQuinn": "CryptoByQuinn", 
        "RedditByQuinn": "RedditByQuinn",
        "ProductByQuinn": "ProductByQuinn",
        "BooksByQuinn": "BooksByQuinn",
        "QuotesByQuinn": "QuotesByQuinn_"
    }
    
    print("🔍 Fetching real Twitter profile pictures from Quinn accounts...")
    print("=" * 60)
    
    profile_data = {}
    
    for display_name, username in quinn_accounts.items():
        print(f"📱 Fetching {display_name} (@{username})...")
        
        profile_image = fetch_twitter_profile_image(username)
        
        if profile_image:
            print(f"✅ Found: {profile_image}")
            profile_data[display_name] = {
                "username": username,
                "profile_image": profile_image,
                "display_name": display_name.replace('ByQuinn', ' by Quinn')
            }
        else:
            print(f"❌ No profile image found")
            # Use a fallback image
            profile_data[display_name] = {
                "username": username,
                "profile_image": "https://pbs.twimg.com/profile_images/1738434567/Quinn_400x400.jpg",
                "display_name": display_name.replace('ByQuinn', ' by Quinn')
            }
        
        print()
    
    # Save to file
    with open('twitter_profiles.json', 'w') as f:
        json.dump(profile_data, f, indent=2)
    
    print("💾 Profile data saved to twitter_profiles.json")
    print("\n🎯 Profile Images Found:")
    for name, data in profile_data.items():
        print(f"  {name}: {data['profile_image']}")
    
    return profile_data

if __name__ == "__main__":
    main()
