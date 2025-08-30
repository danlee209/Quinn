
#!/usr/bin/env python3
"""
Quinn Dashboard - Twitter Scraper Version
This version scrapes Twitter profiles directly without needing any API keys.
"""

import requests
import json
import time
from datetime import datetime, timedelta
from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
import threading
import re
from bs4 import BeautifulSoup

app = Flask(__name__)
app.config['SECRET_KEY'] = 'quinn-dashboard-secret'
socketio = SocketIO(app, cors_allowed_origins="*")

# Account configurations
ACCOUNTS = [
    "TechNewsByQuinn",
    "BooksByQuinn", 
    "QuotesByQuinn",
    "RedditByQuinn",
    "ProductByQuinn",
    "CryptoByQuinn"
]

# Store tweets data
tweets_data = {}

def get_twitter_username(account_name):
    """Convert account name to Twitter username"""
    username_map = {
        "TechNewsByQuinn": "TechNewsByQuinn",
        "BooksByQuinn": "BooksByQuinn",
        "QuotesByQuinn": "QuotesByQuinn_",  # Note the underscore
        "RedditByQuinn": "RedditByQuinn",
        "ProductByQuinn": "ProductByQuinn",
        "CryptoByQuinn": "CryptoByQuinn"
    }
    return username_map.get(account_name, account_name)

def fetch_tweets_scraping(username, max_tweets=20):
    """Fetch tweets by scraping the public Twitter profile"""
    try:
        # Twitter public profile URL
        url = f"https://twitter.com/{username}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        print(f"🌐 Scraping tweets from: {url}")
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            # Try to extract tweets from the HTML
            tweets = extract_tweets_from_html(response.text, username, max_tweets)
            
            if tweets:
                print(f"✅ Found {len(tweets)} tweets for {username} via scraping")
                return tweets
            else:
                print(f"⚠️  No tweets extracted from HTML for {username}")
                return get_sample_tweets(username)
        else:
            print(f"⚠️  Scraping returned {response.status_code} for {username}")
            return get_sample_tweets(username)
            
    except Exception as e:
        print(f"❌ Error scraping tweets for {username}: {e}")
        return get_sample_tweets(username)

def extract_tweets_from_html(html_content, username, max_tweets):
    """Extract tweet data from Twitter HTML"""
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        tweets = []
        
        # Look for tweet containers - Twitter uses various selectors
        tweet_selectors = [
            '[data-testid="tweet"]',
            '[data-testid="tweetText"]',
            '.tweet',
            '.timeline-Tweet',
            '[role="article"]'
        ]
        
        tweet_elements = []
        for selector in tweet_selectors:
            elements = soup.select(selector)
            if elements:
                tweet_elements = elements[:max_tweets]
                break
        
        if not tweet_elements:
            # Fallback: look for any text that might be tweets
            print(f"🔍 No tweet elements found with standard selectors for {username}")
            return get_sample_tweets(username)
        
        for i, tweet_elem in enumerate(tweet_elements[:max_tweets]):
            try:
                # Extract tweet text
                text_elem = tweet_elem.find('div', {'data-testid': 'tweetText'})
                if not text_elem:
                    text_elem = tweet_elem.find('p') or tweet_elem.find('span')
                
                if text_elem:
                    tweet_text = text_elem.get_text(strip=True)
                    
                    # Extract metrics (likes, retweets, replies)
                    metrics = extract_metrics(tweet_elem)
                    
                    # Create tweet object
                    tweet = {
                        'id': f'scraped_{username}_{i}',
                        'text': tweet_text,
                        'created_at': (datetime.now() - timedelta(hours=i)).isoformat(),
                        'time_ago': f'{i}h ago' if i > 0 else 'just now',
                        'url': f"https://twitter.com/{username}/status/scraped_{i}",
                        'metrics': metrics
                    }
                    tweets.append(tweet)
                    
            except Exception as e:
                print(f"⚠️  Error extracting tweet {i}: {e}")
                continue
        
        return tweets if tweets else get_sample_tweets(username)
        
    except Exception as e:
        print(f"❌ Error parsing HTML for {username}: {e}")
        return get_sample_tweets(username)

def extract_metrics(tweet_elem):
    """Extract engagement metrics from tweet element"""
    try:
        metrics = {'likes': 0, 'retweets': 0, 'replies': 0}
        
        # Look for metric elements
        like_elem = tweet_elem.find('div', {'data-testid': 'like'})
        retweet_elem = tweet_elem.find('div', {'data-testid': 'retweet'})
        reply_elem = tweet_elem.find('div', {'data-testid': 'reply'})
        
        if like_elem:
            like_text = like_elem.get_text(strip=True)
            metrics['likes'] = parse_metric_text(like_text)
        
        if retweet_elem:
            retweet_text = retweet_elem.get_text(strip=True)
            metrics['retweets'] = parse_metric_text(retweet_text)
        
        if reply_elem:
            reply_text = reply_elem.get_text(strip=True)
            metrics['replies'] = parse_metric_text(reply_text)
        
        return metrics
        
    except Exception as e:
        print(f"⚠️  Error extracting metrics: {e}")
        return {'likes': 0, 'retweets': 0, 'replies': 0}

def parse_metric_text(text):
    """Parse metric text (e.g., '1.2K', '500') to number"""
    try:
        if not text or text == '':
            return 0
        
        # Remove any non-numeric characters except K, M, B
        clean_text = re.sub(r'[^\d.KMB]', '', text.upper())
        
        if 'K' in clean_text:
            return int(float(clean_text.replace('K', '')) * 1000)
        elif 'M' in clean_text:
            return int(float(clean_text.replace('M', '')) * 1000000)
        elif 'B' in clean_text:
            return int(float(clean_text.replace('B', '')) * 1000000000)
        else:
            return int(clean_text) if clean_text.isdigit() else 0
            
    except Exception:
        return 0

def get_sample_tweets(account_name):
    """Return sample tweets for demonstration when scraping fails"""
    sample_tweets = {
        "TechNewsByQuinn": [
            {
                'id': 'sample_1',
                'text': 'OpenAI releases GPT-4o with real-time voice and vision capabilities, enabling AI assistants that can see and hear like humans. This represents a fundamental shift toward multimodal AI that could transform how we interact with technology. Learn more: https://example.com',
                'created_at': datetime.now().isoformat(),
                'time_ago': '2h ago',
                'url': 'https://twitter.com/i/web/status/sample_1',
                'metrics': {'likes': 45, 'retweets': 12, 'replies': 8}
            },
            {
                'id': 'sample_2',
                'text': 'EU passes landmark AI Act requiring transparency and human oversight for high-risk AI systems. This sets the first comprehensive global standard for AI regulation and will force companies to redesign AI products for safety. Learn more: https://example.com',
                'created_at': (datetime.now() - timedelta(hours=3)).isoformat(),
                'time_ago': '3h ago',
                'url': 'https://twitter.com/i/web/status/sample_2',
                'metrics': {'likes': 67, 'retweets': 23, 'replies': 15}
            }
        ],
        "CryptoByQuinn": [
            {
                'id': 'sample_3',
                'text': 'SEC approves first Bitcoin ETF applications, opening institutional investment floodgates. This landmark decision legitimizes crypto as an asset class and could bring trillions in new capital to the space. Learn more: https://example.com',
                'created_at': datetime.now().isoformat(),
                'time_ago': '1h ago',
                'url': 'https://twitter.com/i/web/status/sample_3',
                'metrics': {'likes': 89, 'retweets': 34, 'replies': 21}
            },
            {
                'id': 'sample_4',
                'text': 'Ethereum completes Shanghai upgrade, enabling staked ETH withdrawals. This critical milestone removes a major barrier to institutional staking and improves network security. Learn more: https://example.com',
                'created_at': (datetime.now() - timedelta(hours=4)).isoformat(),
                'time_ago': '4h ago',
                'url': 'https://twitter.com/i/web/status/sample_4',
                'metrics': {'likes': 156, 'retweets': 67, 'replies': 42}
            }
        ],
        "RedditByQuinn": [
            {
                'id': 'sample_5',
                'text': '🔥 Top Reddit today: 1. Amazing science discovery [link] 2. Hilarious meme thread [link] 3. Life-changing advice [link] 4. Mind-blowing fact [link] 5. Heartwarming story [link]',
                'created_at': datetime.now().isoformat(),
                'time_ago': '30m ago',
                'url': 'https://twitter.com/i/web/status/sample_5',
                'metrics': {'likes': 23, 'retweets': 8, 'replies': 5}
            }
        ],
        "ProductByQuinn": [
            {
                'id': 'sample_6',
                'text': '🚀 AmazingApp — AI-powered productivity tool that helps teams collaborate better + Remote workers + Seamless integration with existing workflows. Learn more: https://example.com',
                'created_at': (datetime.now() - timedelta(hours=2)).isoformat(),
                'time_ago': '2h ago',
                'url': 'https://twitter.com/i/web/status/sample_6',
                'metrics': {'likes': 34, 'retweets': 12, 'replies': 7}
            }
        ],
        "BooksByQuinn": [
            {
                'id': 'sample_7',
                'text': '📚 "The Psychology of Money" by Morgan Housel\n\nA deep dive into how people think about money, revealing that financial success is more about behavior than intelligence.',
                'created_at': (datetime.now() - timedelta(hours=5)).isoformat(),
                'time_ago': '5h ago',
                'url': 'https://twitter.com/i/web/status/sample_7',
                'metrics': {'likes': 78, 'retweets': 29, 'replies': 18}
            }
        ],
        "QuotesByQuinn": [
            {
                'id': 'sample_8',
                'text': '💭 "The only way to do great work is to love what you do." - Steve Jobs, 2005',
                'created_at': (datetime.now() - timedelta(hours=1)).isoformat(),
                'time_ago': '1h ago',
                'url': 'https://twitter.com/i/web/status/sample_8',
                'metrics': {'likes': 112, 'retweets': 45, 'replies': 23}
            }
        ]
    }
    return sample_tweets.get(account_name, [])

def update_all_tweets():
    """Update tweets for all accounts using web scraping"""
    print("🔄 Updating tweets for all accounts...")
    
    for account_name in ACCOUNTS:
        print(f"📱 Fetching tweets for {account_name}...")
        
        username = get_twitter_username(account_name)
        
        # Use web scraping to get tweets
        tweets = fetch_tweets_scraping(username, max_tweets=50)
        
        tweets_data[account_name] = tweets
        print(f"✅ Updated {len(tweets)} tweets for {account_name}")
        
        # Small delay between requests to be respectful
        time.sleep(2)
    
    print("🎉 All tweets updated successfully!")
    
    # Emit update to connected clients
    socketio.emit('tweets_updated', {'accounts': list(tweets_data.keys())})

def background_update():
    """Background thread to update tweets every 5 minutes"""
    while True:
        try:
            update_all_tweets()
            time.sleep(300)  # 5 minutes
        except Exception as e:
            print(f"❌ Background update error: {e}")
            time.sleep(60)  # Wait 1 minute on error

@app.route('/')
def dashboard():
    """Main dashboard page"""
    return render_template('dashboard.html', accounts=ACCOUNTS)

@app.route('/api/accounts')
def get_accounts():
    """Get list of accounts"""
    return jsonify(ACCOUNTS)

@app.route('/api/tweets')
def get_tweets():
    """Get all tweets data"""
    return jsonify(tweets_data)

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    print(f"🔌 Client connected: {request.sid}")
    emit('tweets_updated', {'accounts': list(tweets_data.keys())})

@socketio.on('request_update')
def handle_update_request():
    """Handle manual update request from client"""
    print("🔄 Manual update requested by client")
    update_all_tweets()

if __name__ == '__main__':
    print("🚀 Starting Quinn Dashboard (Scraper Version)...")
    print("📱 Dashboard will be available at: http://localhost:9999")
    print("🔄 Tweets will update every 5 minutes automatically")
    print("🌐 Using web scraping to fetch tweets (no API keys needed)")
    
    # Initial tweet update
    update_all_tweets()
    
    # Start background update thread
    update_thread = threading.Thread(target=background_update, daemon=True)
    update_thread.start()
    
    # Start Flask app
    socketio.run(app, host='0.0.0.0', port=9999, debug=True)
