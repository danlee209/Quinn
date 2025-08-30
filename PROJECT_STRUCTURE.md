# Quinn Social Media Bot - Project Structure

## 📁 Directory Organization

```
Quinn/
├── main.py                    # Main entry point with CLI options
├── requirements.txt           # Python dependencies
├── .gitignore               # Git ignore patterns
├── README.md                # Project documentation
├── PROJECT_STRUCTURE.md     # This file
├── setup_automation.sh      # Setup script for cron automation
├── test_automation.sh       # Test script for automation
├── rotate_logs.sh           # Log rotation script
├── start_dashboard.sh       # Web dashboard startup script
├── webapp.py                # Flask web application
│
├── config/                  # Configuration files
│   └── twitter_dict.py     # Twitter API credentials
│
├── src/                     # Source code
│   ├── core/
│   │   └── main.py         # Core bot logic and functions
│   └── utils/
│       └── prompts.py      # GPT prompts and configurations
│
├── data/                    # Data and memory files
│   ├── books_memory.json   # Books memory tracking
│   ├── quotes_memory.json  # Quotes memory tracking
│   ├── technews_memory.json # TechNews memory tracking
│   ├── reddit_memory.json  # Reddit memory tracking
│   ├── products_memory.json # Products memory tracking
│   └── crypto_memory.json  # Crypto memory tracking
│
├── templates/               # Web dashboard templates
│   └── dashboard.html      # Main dashboard HTML template
│
├── logs/                    # Log files
└── .venv/                  # Python virtual environment
```

## 🚀 Quick Start

```bash
# Run all accounts
python main.py

# Run specific account types
python main.py technews      # High-signal tech news
python main.py crypto        # High-signal crypto news
python main.py reddit        # Top Reddit posts
python main.py product       # ProductHunt showcase
python main.py books         # Book recommendations
python main.py quotes        # Inspirational quotes

# Run multiple accounts
python main.py technews crypto

# Utility commands
python main.py status        # Check memory status
python main.py clear         # Clear all memory
python main.py help          # Show help

# Web Dashboard
./start_dashboard.sh         # Start real-time web dashboard
# Or manually: python webapp.py
```

## 📊 Supported Accounts

1. **TechNewsByQuinn** - High-signal technology news
2. **CryptoByQuinn** - High-signal cryptocurrency news
3. **RedditByQuinn** - Top Reddit posts summary
4. **ProductByQuinn** - ProductHunt product showcase
5. **BooksByQuinn** - 6-tweet book recommendation threads
6. **QuotesByQuinn** - 4-tweet inspirational quote threads

## 🔧 Key Features

- **High-Quality Content**: AI-powered content scoring and filtering
- **Memory System**: Prevents duplicate content across runs
- **Direct Twitter API**: Posts directly to Twitter (no webhooks)
- **Rate Limiting**: Built-in delays and retry mechanisms
- **Command-Line Interface**: Flexible account selection
- **Automation Ready**: Cron job setup scripts included
- **Real-Time Web Dashboard**: Beautiful, shareable dashboard with live updates
