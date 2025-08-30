# 🚀 Quinn Bot Deployment Guide

Complete guide to deploying your Quinn Social Media Bot on GitHub and cloud platforms.

## 📚 Table of Contents

- [GitHub Setup](#github-setup)
- [Local Development](#local-development)
- [Cloud Deployment](#cloud-deployment)
- [Environment Configuration](#environment-configuration)
- [Security Best Practices](#security-best-practices)

## 🐙 GitHub Setup

### 1. **Initialize Git Repository**

```bash
# If you haven't already
git init
git add .
git commit -m "Initial commit: Quinn Social Media Bot"

# Add your GitHub remote
git remote add origin https://github.com/yourusername/quinn-bot.git
git branch -M main
git push -u origin main
```

### 2. **Repository Structure**

Your GitHub repository should look like this:
```
quinn-bot/
├── README.md                 # ✅ Main documentation
├── DEPLOYMENT.md            # ✅ This file
├── PROJECT_STRUCTURE.md     # ✅ Project layout
├── requirements.txt         # ✅ Python dependencies
├── .gitignore              # ✅ Git ignore patterns
├── env.example             # ✅ Environment template
├── main.py                 # ✅ CLI entry point
├── webapp.py               # ✅ Flask web app
├── start_dashboard.sh      # ✅ Dashboard startup
├── setup_automation.sh     # ✅ Automation setup
├── test_automation.sh      # ✅ Automation testing
├── rotate_logs.sh          # ✅ Log rotation
│
├── config/
│   ├── twitter_dict.py     # ❌ Keep private (contains API keys)
│   └── twitter_dict.example.py  # ✅ Public template
│
├── src/
│   ├── core/
│   │   └── main.py         # ✅ Core bot logic
│   └── utils/
│       └── prompts.py      # ✅ GPT prompts
│
├── templates/
│   └── dashboard.html      # ✅ Web dashboard
│
├── data/                    # ❌ Keep private (contains usage data)
└── logs/                    # ❌ Keep private (contains logs)
```

### 3. **Git Workflow**

```bash
# Daily development workflow
git add .
git commit -m "feat: add new feature description"
git push origin main

# Before major releases
git checkout -b feature/new-account-type
# ... make changes ...
git commit -m "feat: add new account type"
git push origin feature/new-account-type
# Create pull request on GitHub
```

## 💻 Local Development

### 1. **Clone and Setup**

```bash
# Clone your repository
git clone https://github.com/yourusername/quinn-bot.git
cd quinn-bot

# Setup virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy configuration templates
cp env.example .env
cp config/twitter_dict.example.py config/twitter_dict.py

# Edit configuration files
nano .env                    # Add your OpenAI API key
nano config/twitter_dict.py # Add your Twitter credentials
```

### 2. **Development Commands**

```bash
# Run the bot
python main.py

# Start web dashboard
python webapp.py

# Check status
python main.py status

# Clear memory
python main.py clear

# Run specific accounts
python main.py technews crypto
```

## ☁️ Cloud Deployment

### 1. **Heroku Deployment**

#### **Create Heroku App**
```bash
# Install Heroku CLI
brew install heroku/brew/heroku  # macOS
# or download from: https://devcenter.heroku.com/articles/heroku-cli

# Login to Heroku
heroku login

# Create new app
heroku create quinn-bot-yourname

# Add Python buildpack
heroku buildpacks:set heroku/python
```

#### **Create Procfile**
```bash
# Create Procfile (no extension)
echo "web: python webapp.py" > Procfile
```

#### **Update webapp.py for Heroku**
```python
# Add this at the bottom of webapp.py
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    socketio.run(app, host='0.0.0.0', port=port, debug=False)
```

#### **Deploy to Heroku**
```bash
# Add all files
git add .
git commit -m "feat: add Heroku deployment support"

# Deploy
git push heroku main

# Set environment variables
heroku config:set OPENAI_API_KEY=your_actual_key
heroku config:set OPENAI_MODEL=gpt-4o-mini

# Open your app
heroku open
```

### 2. **Railway Deployment**

#### **Setup Railway**
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login to Railway
railway login

# Initialize project
railway init

# Deploy
railway up
```

#### **Railway Configuration**
Create `railway.json`:
```json
{
  "build": {
    "builder": "nixpacks"
  },
  "deploy": {
    "startCommand": "python webapp.py",
    "healthcheckPath": "/",
    "healthcheckTimeout": 300,
    "restartPolicyType": "ON_FAILURE"
  }
}
```

### 3. **DigitalOcean App Platform**

#### **Setup**
1. Go to [DigitalOcean App Platform](https://cloud.digitalocean.com/apps)
2. Click "Create App"
3. Connect your GitHub repository
4. Configure build settings:
   - **Build Command**: `pip install -r requirements.txt`
   - **Run Command**: `python webapp.py`
   - **Environment Variables**: Add your API keys

### 4. **AWS Lambda + API Gateway**

#### **Create Lambda Function**
```bash
# Install AWS CLI and configure
aws configure

# Create deployment package
pip install -r requirements.txt -t package/
cp *.py package/
cd package
zip -r ../quinn-bot-lambda.zip .
cd ..

# Create Lambda function
aws lambda create-function \
  --function-name quinn-bot \
  --runtime python3.9 \
  --handler webapp.lambda_handler \
  --zip-file fileb://quinn-bot-lambda.zip \
  --role arn:aws:iam::YOUR_ACCOUNT:role/lambda-role
```

## ⚙️ Environment Configuration

### 1. **Required Environment Variables**

```bash
# OpenAI
OPENAI_API_KEY=sk-your-actual-key-here
OPENAI_MODEL=gpt-4o-mini

# Optional
QUINN_DEBUG=0
DASHBOARD_PORT=5001
UPDATE_FREQUENCY=5
```

### 2. **Twitter API Setup**

1. **Create Twitter Developer Account**
   - Go to [Twitter Developer Portal](https://developer.twitter.com/)
   - Apply for developer access
   - Create a new app

2. **Generate API Keys**
   - Consumer Key (API Key)
   - Consumer Secret (API Secret)
   - Access Token
   - Access Token Secret

3. **Set App Permissions**
   - Read and Write permissions required
   - Enable OAuth 1.0a

4. **Update Configuration**
   ```python
   # In config/twitter_dict.py
   {
       "consumer_key": "your_actual_consumer_key",
       "consumer_secret": "your_actual_consumer_secret",
       "access_token": "your_actual_access_token",
       "access_token_secret": "your_actual_access_token_secret",
       "name": "TechNewsByQuinn"
   }
   ```

## 🔒 Security Best Practices

### 1. **Never Commit Secrets**

```bash
# ✅ Good - These files are in .gitignore
.env
config/twitter_dict.py
data/*.json
logs/

# ❌ Bad - Never commit these
git add .env
git add config/twitter_dict.py
git add data/books_memory.json
```

### 2. **Use Environment Variables**

```python
# ✅ Good
import os
api_key = os.getenv('OPENAI_API_KEY')

# ❌ Bad
api_key = "sk-your-actual-key-here"
```

### 3. **Secure Configuration**

```bash
# Set file permissions
chmod 600 .env
chmod 600 config/twitter_dict.py

# Use secrets management in production
# Heroku: heroku config:set
# Railway: railway variables set
# AWS: AWS Secrets Manager
```

## 📊 Monitoring and Logging

### 1. **Health Checks**

```python
@app.route('/health')
def health_check():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    })
```

### 2. **Logging Configuration**

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/quinn-bot.log'),
        logging.StreamHandler()
    ]
)
```

### 3. **Error Tracking**

```python
# Add Sentry for error tracking
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration

sentry_sdk.init(
    dsn="your-sentry-dsn",
    integrations=[FlaskIntegration()],
    traces_sample_rate=1.0
)
```

## 🚀 Production Deployment Checklist

- [ ] **Environment Variables**: All API keys configured
- [ ] **Twitter Credentials**: All accounts authenticated
- [ ] **Database**: Memory files backed up (if using persistent storage)
- [ ] **Logging**: Proper log rotation configured
- [ ] **Monitoring**: Health checks implemented
- [ ] **SSL**: HTTPS enabled for web dashboard
- [ ] **Rate Limiting**: Twitter API compliance
- [ ] **Backup**: Configuration and data backed up
- [ ] **Testing**: All accounts tested in production
- [ ] **Documentation**: README updated with deployment info

## 🆘 Troubleshooting

### **Common Deployment Issues**

1. **Port Already in Use**
   ```bash
   # Check what's using the port
   lsof -i :5001
   
   # Kill the process
   kill -9 <PID>
   ```

2. **Missing Dependencies**
   ```bash
   # Ensure all packages are installed
   pip install -r requirements.txt
   
   # Check for missing imports
   python -c "import flask, tweepy, openai"
   ```

3. **Twitter API Errors**
   ```bash
   # Verify credentials
   python -c "from config.twitter_dict import accounts_data; print(accounts_data)"
   
   # Check app permissions
   # Ensure Read and Write access is enabled
   ```

4. **OpenAI API Errors**
   ```bash
   # Verify API key
   echo $OPENAI_API_KEY
   
   # Test API connection
   python -c "import openai; openai.api_key='$OPENAI_API_KEY'; print('Connected')"
   ```

## 📞 Support

- **GitHub Issues**: [Create an issue](https://github.com/yourusername/quinn-bot/issues)
- **Discussions**: [Join discussions](https://github.com/yourusername/quinn-bot/discussions)
- **Documentation**: [Project Wiki](https://github.com/yourusername/quinn-bot/wiki)

---

**Happy Deploying! 🚀✨**
