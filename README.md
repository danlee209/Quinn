<<<<<<< HEAD
# 🚀 Quinn Social Media Bot

**AI-powered social media automation with high-signal content generation**

A sophisticated social media bot that automatically generates and posts high-quality, educational content across multiple platforms using AI-powered content scoring and intelligent RSS filtering.

## ✨ Features

- **🤖 AI-Powered Content**: GPT-4 integration for intelligent content generation
- **📰 Multi-Platform Support**: TechNews, Crypto, Reddit, ProductHunt, Books, Quotes
- **🧠 Smart Content Scoring**: Algorithmic filtering for high-signal, meaningful content
- **⏰ Real-Time Updates**: 24-hour content filtering with automatic updates
- **🔄 Memory System**: Prevents duplicate content across runs
- **🌐 Web Dashboard**: Beautiful real-time dashboard with live updates
- **📱 Direct Twitter API**: Posts directly to Twitter (no webhooks needed)
- **⚡ Automation Ready**: Cron job setup for daily automation

## 🏗️ Architecture

```
Quinn/
├── src/core/main.py          # Core bot logic and content generation
├── src/utils/prompts.py      # GPT prompts and configurations
├── webapp.py                 # Flask web dashboard
├── main.py                   # CLI entry point
├── config/                   # Configuration files
├── templates/                # Web dashboard templates
├── data/                     # Memory and data files
└── logs/                     # Log files
```

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Twitter Developer Account
- OpenAI API Key

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/danlee209/Quinn.git
   cd Quinn
   ```

2. **Set up virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

5. **Set up Twitter credentials**
   ```bash
   cp config/twitter_dict.example.py config/twitter_dict.py
   # Edit with your Twitter API credentials
   ```

### Usage

#### Run the Bot
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
```

#### Start Web Dashboard
```bash
# Easy way
./start_dashboard.sh

# Manual way
python webapp.py
```

Access dashboard at: http://localhost:5001

## 🔧 Configuration

### Environment Variables (.env)
```bash
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o-mini
```

### Twitter API Setup
1. Create a Twitter Developer account
2. Create a new app
3. Generate API keys and tokens
4. Add credentials to `config/twitter_dict.py`

### Content Filtering
- **Time Range**: Configurable per account type (default: 24 hours)
- **Quality Scoring**: AI-powered content evaluation
- **Memory System**: Prevents duplicate content

## 📊 Supported Accounts

| Account | Type | Content | Update Frequency |
|---------|------|---------|------------------|
| **TechNewsByQuinn** | Tech News | High-signal technology updates | 24h filtering |
| **CryptoByQuinn** | Crypto News | Educational blockchain content | 24h filtering |
| **RedditByQuinn** | Reddit Summary | Top posts from multiple subreddits | 24h filtering |
| **ProductByQuinn** | ProductHunt | New product showcases | 48h filtering |
| **BooksByQuinn** | Book Reviews | 6-tweet book recommendation threads | On-demand |
| **QuotesByQuinn** | Inspirational | 4-tweet quote threads | On-demand |

## 🌐 Web Dashboard

The real-time web dashboard provides:
- **Live Tweet Counts** for each account
- **Real-time Content Updates** every 5 minutes
- **Interactive Tweet Display** with engagement metrics
- **Responsive Design** for all devices
- **WebSocket Support** for instant updates

## 🔄 Automation

### Cron Job Setup
```bash
# Edit crontab
crontab -e

# Add daily automation (9 AM)
0 9 * * * cd /path/to/quinn-bot && ./start_automation.sh
```

### Automation Scripts
- `setup_automation.sh` - Sets up cron jobs
- `test_automation.sh` - Tests automation setup
- `rotate_logs.sh` - Log rotation and cleanup

## 📁 Project Structure

```
Quinn/
├── main.py                    # CLI entry point
├── webapp.py                  # Flask web application
├── requirements.txt           # Python dependencies
├── .gitignore                # Git ignore patterns
├── README.md                 # This file
├── PROJECT_STRUCTURE.md      # Detailed project layout
├── start_dashboard.sh        # Dashboard startup script
├── setup_automation.sh       # Automation setup
├── test_automation.sh        # Automation testing
├── rotate_logs.sh            # Log rotation
│
├── config/                   # Configuration files
│   └── twitter_dict.py      # Twitter API credentials
│
├── src/                     # Source code
│   ├── core/
│   │   └── main.py         # Core bot logic
│   └── utils/
│       └── prompts.py      # GPT prompts
│
├── templates/               # Web dashboard templates
│   └── dashboard.html      # Main dashboard
│
├── data/                    # Data and memory files
│   ├── books_memory.json   # Books memory
│   ├── quotes_memory.json  # Quotes memory
│   ├── technews_memory.json # TechNews memory
│   ├── reddit_memory.json  # Reddit memory
│   ├── products_memory.json # Products memory
│   └── crypto_memory.json  # Crypto memory
│
└── logs/                    # Log files
```

## 🛠️ Development

### Adding New Account Types
1. Add account to `ACCOUNTS` list in `src/core/main.py`
2. Create memory loading function
3. Add content generation function
4. Update memory tracking
5. Add to web dashboard

### Customizing Content Scoring
Modify scoring functions in `src/core/main.py`:
- `calculate_content_score()` - Tech news scoring
- `calculate_crypto_content_score()` - Crypto content scoring

### Extending GPT Prompts
Edit prompts in `src/utils/prompts.py`:
- System prompts for each content type
- User prompt templates
- Content guidelines and examples

## 🔒 Security & Privacy

- **API Keys**: Never commit API keys to version control
- **Twitter Credentials**: Keep `twitter_dict.py` private
- **Environment Variables**: Use `.env` for sensitive data
- **Memory Files**: Exclude user data from commits

## 📈 Performance

- **Content Filtering**: Intelligent RSS processing
- **Memory Management**: Efficient duplicate prevention
- **Rate Limiting**: Twitter API compliance
- **Background Processing**: Non-blocking operations

## 🐛 Troubleshooting

### Common Issues

1. **401 Unauthorized Twitter Errors**
   - Check API credentials in `config/twitter_dict.py`
   - Verify Twitter app permissions
   - Refresh access tokens if expired

2. **No Content Generated**
   - Check RSS feed URLs
   - Verify OpenAI API key
   - Check content scoring thresholds

3. **Dashboard Not Loading**
   - Ensure port 5001 is available
   - Check Flask dependencies
   - Verify template files

### Debug Mode
```bash
# Enable debug logging
export QUINN_DEBUG=1
python main.py
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- OpenAI for GPT-4 API
- Twitter for social media platform
- Flask for web framework
- Tailwind CSS for styling

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/danlee209/Quinn/issues)
- **Discussions**: [GitHub Discussions](https://github.com/danlee209/Quinn/discussions)
- **Wiki**: [Project Wiki](https://github.com/danlee209/Quinn/wiki)

---

**Made with ❤️ by Quinn Bot Team**

*Automate your social media presence with AI-powered intelligence*
=======
# Quinn
Quinn - making the world just a little bit smarter
>>>>>>> b78824c5e3e28b65b93622324cd5b7f1c375ba12
