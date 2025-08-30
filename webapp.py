#!/usr/bin/env python3
"""
Quinn Social Media Bot - Real-Time Web Dashboard
Shows all tweets from your 6 Quinn accounts with real-time updates
"""

import os
import json
import time
import threading
from datetime import datetime, timedelta
from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
import tweepy
from config.twitter_dict import accounts_data

app = Flask(__name__)
app.config['SECRET_KEY'] = 'quinn-dashboard-secret-key-2024'
socketio = SocketIO(app, cors_allowed_origins="*")

# Global storage for tweets
tweets_data = {}
last_update = {}

def fetch_recent_tweets(account_name, max_tweets=20):
    """Fetch recent tweets from a specific account"""
    try:
        # Find the account credentials
        account = next((acc for acc in accounts_data if acc["name"] == account_name), None)
        if not account:
            print(f"❌ No Twitter credentials found for {account_name}")
            return []
        
        # Authenticate with Twitter
        client = tweepy.Client(
            consumer_key=account["consumer_key"],
            consumer_secret=account["consumer_secret"],
            access_token=account["access_token"],
            access_token_secret=account["access_token_secret"]
        )
        
        # Get user ID first
        user = client.get_me()
        if not user.data:
            print(f"❌ Could not get user info for {account_name}")
            return []
        
        user_id = user.data.id
        
        # Get recent tweets
        tweets = client.get_users_tweets(
            id=user_id,
            max_results=max_tweets,
            tweet_fields=['created_at', 'public_metrics', 'context_annotations']
        )
        
        if not tweets.data:
            return []
        
        formatted_tweets = []
        for tweet in tweets.data:
            # Calculate time ago
            created_at = tweet.created_at
            now = datetime.now(created_at.tzinfo)
            time_diff = now - created_at
            
            if time_diff.days > 0:
                time_ago = f"{time_diff.days}d ago"
            elif time_diff.seconds > 3600:
                time_ago = f"{time_diff.seconds // 3600}h ago"
            elif time_diff.seconds > 60:
                time_ago = f"{time_diff.seconds // 60}m ago"
            else:
                time_ago = "just now"
            
            formatted_tweets.append({
                'id': tweet.id,
                'text': tweet.text,
                'created_at': created_at.isoformat(),
                'time_ago': time_ago,
                'url': f"https://twitter.com/i/web/status/{tweet.id}",
                'metrics': {
                    'likes': getattr(tweet.public_metrics, 'like_count', 0),
                    'retweets': getattr(tweet.public_metrics, 'retweet_count', 0),
                    'replies': getattr(tweet.public_metrics, 'reply_count', 0)
                } if hasattr(tweet, 'public_metrics') else {}
            })
        
        return formatted_tweets
        
    except Exception as e:
        print(f"❌ Error fetching tweets for {account_name}: {e}")
        return []

def update_all_tweets():
    """Update tweets for all accounts"""
    global tweets_data, last_update
    
    while True:
        try:
            print("🔄 Updating tweets for all accounts...")
            
            for account in accounts_data:
                account_name = account["name"]
                print(f"📱 Fetching tweets for {account_name}...")
                
                tweets = fetch_recent_tweets(account_name)
                if tweets:
                    tweets_data[account_name] = tweets
                    last_update[account_name] = datetime.now().isoformat()
                    print(f"✅ Updated {len(tweets)} tweets for {account_name}")
                else:
                    print(f"⚠️  No tweets found for {account_name}")
            
            # Emit update to all connected clients
            socketio.emit('tweets_updated', {
                'tweets': tweets_data,
                'last_update': last_update,
                'timestamp': datetime.now().isoformat()
            })
            
            print("🎉 All tweets updated successfully!")
            
        except Exception as e:
            print(f"❌ Error updating tweets: {e}")
        
        # Wait 5 minutes before next update
        time.sleep(300)

@app.route('/')
def dashboard():
    """Main dashboard page"""
    return render_template('dashboard.html')

@app.route('/api/tweets')
def get_tweets():
    """API endpoint to get current tweets"""
    return jsonify({
        'tweets': tweets_data,
        'last_update': last_update,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/accounts')
def get_accounts():
    """API endpoint to get account information"""
    accounts_info = []
    for account in accounts_data:
        account_info = {
            'name': account['name'],
            'handle': account['name'].replace('ByQuinn', ''),
            'type': account['name'].lower().replace('byquinn', ''),
            'tweet_count': len(tweets_data.get(account['name'], [])),
            'last_update': last_update.get(account['name'], 'Never')
        }
        accounts_info.append(account_info)
    
    return jsonify(accounts_info)

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    print(f"🔌 Client connected: {request.sid}")
    emit('connected', {'message': 'Connected to Quinn Dashboard'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    print(f"🔌 Client disconnected: {request.sid}")

def get_sample_tweets(account_name):
    """Return sample tweets for demonstration when API fails"""
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

@socketio.on('request_update')
def handle_update_request():
    """Handle manual update request from client"""
    print("🔄 Manual update requested by client")
    # Trigger immediate update
    threading.Thread(target=update_all_tweets, daemon=True).start()

if __name__ == '__main__':
    # Start background tweet update thread
    update_thread = threading.Thread(target=update_all_tweets, daemon=True)
    update_thread.start()
    
    print("🚀 Starting Quinn Dashboard...")
    print("📱 Dashboard will be available at: http://localhost:5001")
    print("🔄 Tweets will update every 5 minutes automatically")
    
    # Run the Flask app
    socketio.run(app, host='0.0.0.0', port=5001, debug=True)
