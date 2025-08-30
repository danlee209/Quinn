#!/usr/bin/env python3
"""
Quinn Dashboard - Simple Version for Vercel Deployment
This version serves static dummy data without complex scraping or background processes.
"""

from flask import Flask, render_template, jsonify
import json
from datetime import datetime, timedelta

app = Flask(__name__)

# Dummy data for all accounts
DUMMY_DATA = {
    "TechNewsByQuinn": [
        {
            'id': 'tech_1',
            'text': '🚀 OpenAI releases GPT-4o with real-time voice and vision capabilities. This represents a fundamental shift toward multimodal AI that could transform how we interact with technology.',
            'created_at': (datetime.now() - timedelta(hours=2)).isoformat(),
            'time_ago': '2h ago',
            'url': 'https://twitter.com/TechNewsByQuinn/status/tech_1',
            'metrics': {'likes': 45, 'retweets': 12, 'replies': 8}
        },
        {
            'id': 'tech_2',
            'text': '🔬 EU passes landmark AI Act requiring transparency and human oversight for high-risk AI systems. This sets the first comprehensive global standard for AI regulation.',
            'created_at': (datetime.now() - timedelta(hours=5)).isoformat(),
            'time_ago': '5h ago',
            'url': 'https://twitter.com/TechNewsByQuinn/status/tech_2',
            'metrics': {'likes': 67, 'retweets': 23, 'replies': 15}
        },
        {
            'id': 'tech_3',
            'text': '💻 Apple announces new M4 chip with 50% faster performance and advanced AI capabilities. This could revolutionize Mac performance for creative professionals.',
            'created_at': (datetime.now() - timedelta(hours=8)).isoformat(),
            'time_ago': '8h ago',
            'url': 'https://twitter.com/TechNewsByQuinn/status/tech_3',
            'metrics': {'likes': 89, 'retweets': 34, 'replies': 21}
        }
    ],
    "CryptoByQuinn": [
        {
            'id': 'crypto_1',
            'text': '₿ SEC approves first Bitcoin ETF applications, opening institutional investment floodgates. This landmark decision legitimizes crypto as an asset class.',
            'created_at': (datetime.now() - timedelta(hours=1)).isoformat(),
            'time_ago': '1h ago',
            'url': 'https://twitter.com/CryptoByQuinn/status/crypto_1',
            'metrics': {'likes': 156, 'retweets': 67, 'replies': 42}
        },
        {
            'id': 'crypto_2',
            'text': '🔗 Ethereum completes Shanghai upgrade, enabling staked ETH withdrawals. This critical milestone removes a major barrier to institutional staking.',
            'created_at': (datetime.now() - timedelta(hours=4)).isoformat(),
            'time_ago': '4h ago',
            'url': 'https://twitter.com/CryptoByQuinn/status/crypto_2',
            'metrics': {'likes': 234, 'retweets': 89, 'replies': 56}
        },
        {
            'id': 'crypto_3',
            'text': '🌊 Solana reaches new ATH with 100k+ TPS performance. Layer 2 solutions are revolutionizing blockchain scalability and user experience.',
            'created_at': (datetime.now() - timedelta(hours=7)).isoformat(),
            'time_ago': '7h ago',
            'url': 'https://twitter.com/CryptoByQuinn/status/crypto_3',
            'metrics': {'likes': 178, 'retweets': 45, 'replies': 23}
        }
    ],
    "RedditByQuinn": [
        {
            'id': 'reddit_1',
            'text': '🔥 Top Reddit today: 1. Amazing science discovery about quantum computing 2. Hilarious meme thread that went viral 3. Life-changing advice from r/personalfinance',
            'created_at': (datetime.now() - timedelta(hours=30)).isoformat(),
            'time_ago': '30m ago',
            'url': 'https://twitter.com/RedditByQuinn/status/reddit_1',
            'metrics': {'likes': 23, 'retweets': 8, 'replies': 5}
        },
        {
            'id': 'reddit_2',
            'text': '📚 r/books discussion: "What book changed your perspective on life?" Top answers include Sapiens, Man\'s Search for Meaning, and The Power of Now.',
            'created_at': (datetime.now() - timedelta(hours=3)).isoformat(),
            'time_ago': '3h ago',
            'url': 'https://twitter.com/RedditByQuinn/status/reddit_2',
            'metrics': {'likes': 45, 'retweets': 12, 'replies': 18}
        }
    ],
    "ProductByQuinn": [
        {
            'id': 'product_1',
            'text': '🚀 AmazingApp — AI-powered productivity tool that helps teams collaborate better. Features: Remote work optimization + Seamless workflow integration.',
            'created_at': (datetime.now() - timedelta(hours=2)).isoformat(),
            'time_ago': '2h ago',
            'url': 'https://twitter.com/ProductByQuinn/status/product_1',
            'metrics': {'likes': 34, 'retweets': 12, 'replies': 7}
        },
        {
            'id': 'product_2',
            'text': '💡 InnovationAlert: New startup launches revolutionary AR glasses for remote collaboration. Could this be the future of virtual meetings?',
            'created_at': (datetime.now() - timedelta(hours=6)).isoformat(),
            'time_ago': '6h ago',
            'url': 'https://twitter.com/ProductByQuinn/status/product_2',
            'metrics': {'likes': 67, 'retweets': 23, 'replies': 15}
        }
    ],
    "BooksByQuinn": [
        {
            'id': 'book_1',
            'text': '📚 "The Psychology of Money" by Morgan Housel\n\nA deep dive into how people think about money, revealing that financial success is more about behavior than intelligence.',
            'created_at': (datetime.now() - timedelta(hours=5)).isoformat(),
            'time_ago': '5h ago',
            'url': 'https://twitter.com/BooksByQuinn/status/book_1',
            'metrics': {'likes': 78, 'retweets': 29, 'replies': 18}
        },
        {
            'id': 'book_2',
            'text': '🧠 "Atomic Habits" by James Clear\n\nLearn how tiny changes in behavior can create remarkable results. The compound effect of small improvements.',
            'created_at': (datetime.now() - timedelta(hours=9)).isoformat(),
            'time_ago': '9h ago',
            'url': 'https://twitter.com/BooksByQuinn/status/book_2',
            'metrics': {'likes': 123, 'retweets': 45, 'replies': 32}
        }
    ],
    "QuotesByQuinn": [
        {
            'id': 'quote_1',
            'text': '💭 "The only way to do great work is to love what you do." - Steve Jobs, 2005\n\nPassion drives innovation and excellence.',
            'created_at': (datetime.now() - timedelta(hours=1)).isoformat(),
            'time_ago': '1h ago',
            'url': 'https://twitter.com/QuotesByQuinn/status/quote_1',
            'metrics': {'likes': 112, 'retweets': 45, 'replies': 23}
        },
        {
            'id': 'quote_2',
            'text': '🌟 "Success is not final, failure is not fatal: it is the courage to continue that counts." - Winston Churchill\n\nResilience in the face of adversity.',
            'created_at': (datetime.now() - timedelta(hours=4)).isoformat(),
            'time_ago': '4h ago',
            'url': 'https://twitter.com/QuotesByQuinn/status/quote_2',
            'metrics': {'likes': 89, 'retweets': 34, 'replies': 19}
        }
    ]
}

@app.route('/')
def dashboard():
    """Main dashboard page"""
    return render_template('dashboard_simple.html', accounts=list(DUMMY_DATA.keys()))

@app.route('/api/accounts')
def get_accounts():
    """Get list of accounts"""
    return jsonify(list(DUMMY_DATA.keys()))

@app.route('/api/tweets')
def get_tweets():
    """Get all tweets data"""
    return jsonify({
        'tweets': DUMMY_DATA,
        'last_update': datetime.now().isoformat()
    })

@app.route('/health')
def health():
    """Health check endpoint for Vercel"""
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

if __name__ == '__main__':
    print("🚀 Starting Quinn Dashboard (Simple Version)...")
    print("📱 Dashboard will be available at: http://localhost:5001")
    print("🌐 Serving static dummy data (ready for Vercel deployment)")
    
    # Start Flask app
    app.run(host='0.0.0.0', port=5001, debug=True)
