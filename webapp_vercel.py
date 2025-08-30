#!/usr/bin/env python3
"""
Quinn Dashboard - Vercel Version
This version is optimized for Vercel serverless deployment.
"""

import os
import requests
import json
from datetime import datetime, timedelta
from flask import Flask, render_template, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enable CORS for Vercel

# Account configurations
ACCOUNTS = [
    "TechNewsByQuinn",
    "BooksByQuinn", 
    "QuotesByQuinn",
    "RedditByQuinn",
    "ProductByQuinn",
    "CryptoByQuinn"
]

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

def get_sample_tweets(account_name):
    """Return sample tweets for demonstration"""
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

def get_all_tweets():
    """Get tweets for all accounts"""
    tweets_data = {}
    
    for account_name in ACCOUNTS:
        # For now, use sample data
        # In production, you could:
        # 1. Call an external API service
        # 2. Use a database
        # 3. Call a cron job service
        tweets_data[account_name] = get_sample_tweets(account_name)
    
    return tweets_data

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
    tweets_data = get_all_tweets()
    return jsonify(tweets_data)

@app.route('/api/health')
def health_check():
    """Health check endpoint for Vercel"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "Quinn Dashboard",
        "version": "1.0.0"
    })

# Vercel requires this for serverless deployment
if __name__ == '__main__':
    app.run(debug=True)
