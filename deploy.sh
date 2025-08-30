#!/bin/bash

# 🚀 Quinn Bot Deployment Script
# This script helps deploy your Quinn Bot to GitHub and cloud platforms

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're in the right directory
if [ ! -f "main.py" ] || [ ! -f "webapp.py" ]; then
    print_error "This script must be run from the Quinn Bot root directory"
    exit 1
fi

# Check if git is initialized
if [ ! -d ".git" ]; then
    print_status "Initializing git repository..."
    git init
    print_success "Git repository initialized"
fi

# Check git status
print_status "Checking git status..."
if [ -z "$(git status --porcelain)" ]; then
    print_success "Working directory is clean"
else
    print_warning "Working directory has uncommitted changes"
    echo "Uncommitted changes:"
    git status --short
    echo ""
    read -p "Do you want to commit these changes? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        read -p "Enter commit message: " commit_msg
        git add .
        git commit -m "$commit_msg"
        print_success "Changes committed"
    fi
fi

# Check if remote origin exists
if ! git remote get-url origin >/dev/null 2>&1; then
    print_status "No remote origin found. Please add your GitHub repository:"
    echo "Example: git remote add origin https://github.com/yourusername/quinn-bot.git"
    read -p "Enter your GitHub repository URL: " repo_url
    git remote add origin "$repo_url"
    print_success "Remote origin added: $repo_url"
fi

# Check current branch
current_branch=$(git branch --show-current)
print_status "Current branch: $current_branch"

# Ask user what they want to do
echo ""
echo "🚀 Quinn Bot Deployment Options:"
echo "1. Push to GitHub (main branch)"
echo "2. Create and push feature branch"
echo "3. Deploy to Heroku"
echo "4. Deploy to Railway"
echo "5. Setup GitHub Actions"
echo "6. Exit"
echo ""

read -p "Choose an option (1-6): " -n 1 -r
echo ""

case $REPLY in
    1)
        print_status "Pushing to GitHub main branch..."
        if [ "$current_branch" != "main" ]; then
            git checkout main || git checkout -b main
        fi
        git push -u origin main
        print_success "Successfully pushed to GitHub main branch!"
        ;;
    2)
        read -p "Enter feature branch name: " branch_name
        print_status "Creating and pushing feature branch: $branch_name"
        git checkout -b "$branch_name"
        git push -u origin "$branch_name"
        print_success "Feature branch '$branch_name' created and pushed!"
        ;;
    3)
        print_status "Setting up Heroku deployment..."
        if ! command -v heroku &> /dev/null; then
            print_error "Heroku CLI not found. Please install it first:"
            echo "macOS: brew install heroku/brew/heroku"
            echo "Other: https://devcenter.heroku.com/articles/heroku-cli"
            exit 1
        fi
        
        # Check if user is logged in to Heroku
        if ! heroku auth:whoami &> /dev/null; then
            print_status "Please log in to Heroku..."
            heroku login
        fi
        
        # Create Procfile if it doesn't exist
        if [ ! -f "Procfile" ]; then
            echo "web: python webapp.py" > Procfile
            print_success "Procfile created"
        fi
        
        # Create Heroku app
        read -p "Enter Heroku app name (or press Enter for auto-generated): " app_name
        if [ -z "$app_name" ]; then
            heroku create
        else
            heroku create "$app_name"
        fi
        
        # Set buildpack
        heroku buildpacks:set heroku/python
        
        # Deploy
        git add .
        git commit -m "feat: add Heroku deployment support" || true
        git push heroku main
        
        print_success "Heroku deployment completed!"
        print_status "Set your environment variables:"
        echo "heroku config:set OPENAI_API_KEY=your_key"
        echo "heroku config:set OPENAI_MODEL=gpt-4o-mini"
        ;;
    4)
        print_status "Setting up Railway deployment..."
        if ! command -v railway &> /dev/null; then
            print_error "Railway CLI not found. Please install it first:"
            echo "npm install -g @railway/cli"
            exit 1
        fi
        
        # Check if user is logged in to Railway
        if ! railway whoami &> /dev/null; then
            print_status "Please log in to Railway..."
            railway login
        fi
        
        # Create railway.json if it doesn't exist
        if [ ! -f "railway.json" ]; then
            cat > railway.json << EOF
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
EOF
            print_success "railway.json created"
        fi
        
        # Initialize and deploy
        railway init
        railway up
        
        print_success "Railway deployment completed!"
        print_status "Set your environment variables in the Railway dashboard"
        ;;
    5)
        print_status "Setting up GitHub Actions..."
        if [ ! -d ".github/workflows" ]; then
            mkdir -p .github/workflows
        fi
        
        if [ ! -f ".github/workflows/ci.yml" ]; then
            print_error "GitHub Actions workflow not found. Please create it manually or run this script again."
            exit 1
        fi
        
        print_status "GitHub Actions workflow found. Pushing to GitHub..."
        git add .github/
        git commit -m "ci: add GitHub Actions workflow" || true
        git push origin main
        
        print_success "GitHub Actions setup completed!"
        print_status "Check the Actions tab in your GitHub repository"
        ;;
    6)
        print_status "Exiting..."
        exit 0
        ;;
    *)
        print_error "Invalid option. Please choose 1-6."
        exit 1
        ;;
esac

echo ""
print_success "Deployment completed successfully! 🎉"
echo ""
print_status "Next steps:"
echo "1. Check your GitHub repository for updates"
echo "2. Verify all files are properly committed"
echo "3. Test your deployment if applicable"
echo "4. Update your README.md with deployment information"
echo ""
print_status "Happy coding! 🚀✨"
