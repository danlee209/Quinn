import os, json
import requests, feedparser
from urllib.parse import urljoin, quote
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from openai import OpenAI
import urllib3
import tweepy
import time
import random
from datetime import datetime, timedelta
from config.twitter_dict import accounts_data
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ---------- Config ----------
# HIGH-SIGNAL Tech News Sources - Focused on meaningful, educational content
FEEDS = [
    # High-quality tech analysis and research
    "https://hnrss.org/frontpage?points=100&count=25",  # Higher point threshold for quality
    "https://www.techmeme.com/feed.xml",  # Tech industry analysis
    "https://feeds.arstechnica.com/arstechnica/index",  # Deep tech analysis
    
    # Reliable high-signal sources
    "https://feeds.feedburner.com/techcrunch",  # TechCrunch analysis
    "https://feeds.feedburner.com/venturebeat",  # VentureBeat insights
    "https://feeds.feedburner.com/theverge",  # The Verge tech coverage
    "https://feeds.feedburner.com/arstechnica",  # Ars Technica analysis
]

# HIGH-SIGNAL Crypto News Sources - Focused on meaningful, educational content
CRYPTO_FEEDS = [
    # Primary crypto news sources
    "https://www.coindesk.com/arc/outboundfeeds/rss/?outputType=xml",  # CoinDesk (all stories)
    "https://cointelegraph.com/rss",  # Cointelegraph (all news)
    
    # Additional high-quality crypto sources
    "https://feeds.feedburner.com/CoinDesk",  # CoinDesk feedburner
    "https://feeds.feedburner.com/Cointelegraph",  # Cointelegraph feedburner
    "https://feeds.feedburner.com/Decrypt",  # Decrypt crypto news
    "https://feeds.feedburner.com/TheBlock",  # The Block crypto analysis
    
    # Alternative reliable sources
    "https://feeds.feedburner.com/CoinTelegraph",  # Alternative Cointelegraph feed
    "https://feeds.feedburner.com/CoinDesk",  # CoinDesk alternative feed
]

# Reddit RSS feeds for top posts (using more reliable sources)
REDDIT_FEEDS = [
    "https://www.reddit.com/r/popular/.rss",
    "https://www.reddit.com/r/technology/.rss",
    "https://www.reddit.com/r/science/.rss",
    "https://www.reddit.com/r/news/.rss",
    "https://www.reddit.com/r/entertainment/.rss"
]

# ProductHunt RSS feeds for new products (using more accessible sources)
PRODUCTHUNT_FEEDS = [
    "https://feeds.feedburner.com/producthunt",
    "https://www.producthunt.com/.rss",
    "https://www.producthunt.com/rss",
    "https://feeds.feedburner.com/ProductHunt",
    "https://www.producthunt.com/feed.xml"
]

ACCOUNTS = [
    {"handle": "TechNewsByQuinn", "type": "technews"},
    {"handle": "BooksByQuinn",    "type": "books"},
    {"handle": "QuotesByQuinn",   "type": "quotes"},
    {"handle": "RedditByQuinn",   "type": "reddit"},
    {"handle": "ProductByQuinn",  "type": "product"},
    {"handle": "CryptoByQuinn",   "type": "crypto"},
]

load_dotenv()
OPENAI_API_KEY   = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL     = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

if not OPENAI_API_KEY:
    raise SystemExit("Missing OPENAI_API_KEY in .env file")

client = OpenAI(api_key=OPENAI_API_KEY)

# ---------- Time Filtering Configuration ----------
# Maximum age of content in hours (configurable per feed type)
MAX_CONTENT_AGE_HOURS = {
    "technews": 24,    # Tech news: 24 hours
    "crypto": 24,      # Crypto news: 24 hours
    "reddit": 24,      # Reddit posts: 24 hours
    "product": 48,     # ProductHunt: 48 hours (products stay relevant longer)
    "default": 24      # Default for any other types
}

# ---------- Helpers ----------
def custom_feedparser(url: str):
    """Feedparser via requests (more forgiving TLS)."""
    try:
        r = requests.get(url, timeout=10, verify=False)
        r.raise_for_status()
        return feedparser.parse(r.content)
    except Exception as e:
        print(f"[feeds] {url} -> {e}")
        return feedparser.parse("")

def filter_by_recency(feed_entries, content_type="default"):
    """Filter RSS entries to only include recent content based on configurable time limits"""
    if not feed_entries:
        return []
    
    max_hours = MAX_CONTENT_AGE_HOURS.get(content_type, MAX_CONTENT_AGE_HOURS["default"])
    cutoff_time = datetime.now() - timedelta(hours=max_hours)
    recent_entries = []
    filtered_count = 0
    
    for entry in feed_entries:
        # Try different date fields that RSS feeds commonly use
        published_time = None
        
        # Check published_parsed (most common)
        if hasattr(entry, 'published_parsed') and entry.published_parsed:
            try:
                published_time = datetime(*entry.published_parsed[:6])
            except (ValueError, TypeError):
                pass
        
        # Check updated_parsed (alternative)
        elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
            try:
                published_time = datetime(*entry.updated_parsed[:6])
            except (ValueError, TypeError):
                pass
        
        # Check published (string format)
        elif hasattr(entry, 'published') and entry.published:
            try:
                # Try to parse common date formats
                for fmt in ['%a, %d %b %Y %H:%M:%S %z', '%a, %d %b %Y %H:%M:%S', '%Y-%m-%d %H:%M:%S']:
                    try:
                        published_time = datetime.strptime(entry.published, fmt)
                        break
                    except ValueError:
                        continue
            except Exception:
                pass
        
        # If we can't determine the time, include it (better to include than exclude)
        if published_time is None:
            recent_entries.append(entry)
            continue
        
        # Filter by recency
        if published_time > cutoff_time:
            recent_entries.append(entry)
        else:
            filtered_count += 1
    
    if filtered_count > 0:
        print(f"⏰ Time filtering: {len(feed_entries)} → {len(recent_entries)} entries (filtered out {filtered_count} entries older than {max_hours}h)")
    
    return recent_entries

def fetch_candidates(limit=15):
    """Fetch and filter high-signal tech news candidates"""
    items, seen = [], set()
    
    # Collect all items first
    for url in FEEDS:
        feed = custom_feedparser(url)
        
        # Apply time filtering to get only recent content
        recent_entries = filter_by_recency(feed.entries, "technews")
        
        for it in recent_entries:
            title = getattr(it, "title", None)
            link = getattr(it, "link", None)
            if not title or not link or link in seen:
                continue
            seen.add(link)
            
            # Add source info for better filtering
            source = url.split("//")[1].split("/")[0] if "//" in url else "unknown"
            items.append({
                "title": title, 
                "link": link, 
                "source": source,
                "score": 0  # Will be calculated below
            })
    
    # Score and filter items for quality
    scored_items = []
    for item in items:
        score = calculate_content_score(item)
        if score > 0:  # Only include items with positive scores
            item["score"] = score
            scored_items.append(item)
    
    # Sort by score (highest first) and return top items
    scored_items.sort(key=lambda x: x["score"], reverse=True)
    return scored_items[:limit]

def fetch_crypto_candidates(limit=15):
    """Fetch and filter high-signal crypto news candidates"""
    items, seen = [], set()
    
    # Collect all items first
    for url in CRYPTO_FEEDS:
        feed = custom_feedparser(url)
        
        # Apply time filtering to get only recent content
        recent_entries = filter_by_recency(feed.entries, "crypto")
        
        for it in recent_entries:
            title = getattr(it, "title", None)
            link = getattr(it, "link", None)
            if not title or not link or link in seen:
                continue
            seen.add(link)
            
            # Add source info for better filtering
            source = url.split("//")[1].split("/")[0] if "//" in url else "unknown"
            items.append({
                "title": title, 
                "link": link, 
                "source": source,
                "score": 0  # Will be calculated below
            })
    
    # Score and filter items for quality
    scored_items = []
    for item in items:
        score = calculate_crypto_content_score(item)
        if score > 0:  # Only include items with positive scores
            item["score"] = score
            scored_items.append(item)
    
    # Sort by score (highest first) and return top items
    scored_items.sort(key=lambda x: x["score"], reverse=True)
    return scored_items[:limit]

def filter_used_articles(candidates, technews_memory):
    """Filter out articles that have already been used"""
    if not candidates or not technews_memory:
        return candidates
    
    used_articles = set(technews_memory.get('used_articles', []))
    filtered_candidates = []
    
    for candidate in candidates:
        # Extract article identifier
        article_id = extract_article_identifier("", candidate['link'])
        if article_id and article_id not in used_articles:
            filtered_candidates.append(candidate)
        else:
            print(f"🚫 Filtered out used article: {candidate['title'][:60]}...")
    
    print(f"🔍 Content filtering: {len(candidates)} → {len(filtered_candidates)} candidates after removing used articles")
    return filtered_candidates

def calculate_content_score(item):
    """Calculate a quality score for content based on various factors"""
    title = item["title"].lower()
    source = item["source"].lower()
    score = 0
    
    # Source quality bonuses
    if "ieee" in source or "mit" in source or "nature" in source or "science" in source:
        score += 20  # Academic/research sources
    elif "arstechnica" in source or "techmeme" in source:
        score += 15  # High-quality tech analysis
    elif "hnrss" in source:
        score += 10  # Hacker News (already filtered by points)
    
    # Title quality indicators
    if any(word in title for word in ["research", "study", "breakthrough", "discovery", "innovation"]):
        score += 15
    if any(word in title for word in ["ai", "artificial intelligence", "machine learning", "neural"]):
        score += 10
    if any(word in title for word in ["quantum", "blockchain", "crypto", "web3"]):
        score += 8
    if any(word in title for word in ["regulation", "policy", "law", "government"]):
        score += 12
    if any(word in title for word in ["security", "privacy", "cybersecurity"]):
        score += 10
    if any(word in title for word in ["climate", "energy", "sustainability"]):
        score += 8
    
    # Penalize low-quality indicators
    if any(word in title for word in ["rumor", "leak", "gossip", "drama", "celeb"]):
        score -= 20
    if any(word in title for word in ["update", "patch", "release", "announcement"]):
        score -= 5  # Minor updates get lower scores
    if any(word in title for word in ["stock", "price", "market", "earnings"]):
        score -= 10  # Financial news is often low-signal
    
    # Bonus for longer, more descriptive titles (indicates substance)
    if len(title) > 60:
        score += 5
    
    return max(0, score)  # Don't return negative scores

def calculate_crypto_content_score(item):
    """Calculate a quality score for crypto content based on various factors"""
    title = item["title"].lower()
    source = item["source"].lower()
    score = 0
    
    # Source quality bonuses
    if "coindesk" in source or "cointelegraph" in source:
        score += 20  # Primary crypto news sources
    elif "decrypt" in source or "theblock" in source:
        score += 15  # High-quality crypto analysis
    elif "messari" in source:
        score += 18  # Crypto research and analysis
    
    # Title quality indicators for crypto
    if any(word in title for word in ["regulation", "policy", "law", "government", "sec", "cfdc"]):
        score += 15  # Regulatory news is high-signal
    if any(word in title for word in ["adoption", "institutional", "enterprise", "partnership"]):
        score += 12  # Adoption news is important
    if any(word in title for word in ["defi", "nft", "dao", "web3", "metaverse"]):
        score += 10  # Emerging crypto sectors
    if any(word in title for word in ["bitcoin", "ethereum", "blockchain", "cryptocurrency"]):
        score += 8  # Core crypto topics
    if any(word in title for word in ["security", "hack", "exploit", "audit"]):
        score += 10  # Security is critical
    if any(word in title for word in ["research", "study", "analysis", "report"]):
        score += 8  # Research content
    
    # Penalize low-quality indicators
    if any(word in title for word in ["moon", "pump", "dump", "fomo", "hodl"]):
        score -= 25  # Meme/price speculation
    if any(word in title for word in ["celebrity", "influencer", "endorsement"]):
        score -= 20  # Celebrity crypto drama
    if any(word in title for word in ["price", "market", "trading", "chart"]):
        score -= 15  # Price speculation
    if any(word in title for word in ["rumor", "leak", "unconfirmed"]):
        score -= 20  # Unverified information
    
    # Bonus for longer, more descriptive titles (indicates substance)
    if len(title) > 60:
        score += 5
    
    return max(0, score)  # Don't return negative scores

def fetch_reddit_posts(limit=20):
    """Fetch top Reddit posts from multiple subreddits"""
    posts, seen = [], set()
    
    for url in REDDIT_FEEDS:
        try:
            feed = custom_feedparser(url)
            
            # Check if feed has entries
            if not feed.entries:
                print(f"[reddit] No entries found in {url}")
                continue
            
            # Apply time filtering to get only recent content
            recent_entries = filter_by_recency(feed.entries, "reddit")
                
            for entry in recent_entries:
                title = getattr(entry, "title", None)
                link = getattr(entry, "link", None)
                
                # Extract subreddit from URL
                if link and "/r/" in link:
                    subreddit = link.split("/r/")[1].split("/")[0]
                else:
                    subreddit = "unknown"
                
                if not title or not link or link in seen:
                    continue
                    
                seen.add(link)
                posts.append({
                    "title": title,
                    "link": link,
                    "subreddit": subreddit,
                    "score": getattr(entry, "score", 0)  # Reddit score if available
                })
                
                if len(posts) >= limit:
                    break
                    
        except Exception as e:
            print(f"[reddit] Error fetching {url}: {e}")
            continue
    
    # If we couldn't get any posts, try a fallback approach
    if not posts:
        print("[reddit] Trying fallback RSS feeds...")
        fallback_feeds = [
            "https://feeds.feedburner.com/reddit/r/all",
            "https://www.reddit.com/.rss"
        ]
        
        for url in fallback_feeds:
            try:
                feed = custom_feedparser(url)
                if feed.entries:
                    for entry in feed.entries[:10]:  # Limit to 10 from fallback
                        title = getattr(entry, "title", None)
                        link = getattr(entry, "link", None)
                        
                        if title and link and link not in seen:
                            seen.add(link)
                            posts.append({
                                "title": title,
                                "link": link,
                                "subreddit": "reddit",
                                "score": 0
                            })
                            
                            if len(posts) >= limit:
                                break
                                
            except Exception as e:
                print(f"[reddit] Fallback error for {url}: {e}")
                continue
    
    return posts

def fetch_producthunt_products(limit=20):
    """Fetch new products from ProductHunt RSS feeds"""
    products, seen = [], set()
    
    for url in PRODUCTHUNT_FEEDS:
        try:
            feed = custom_feedparser(url)
            
            # Check if feed has entries
            if not feed.entries:
                print(f"[producthunt] No entries found in {url}")
                continue
            
            # Apply time filtering to get only recent content (48h for products)
            recent_entries = filter_by_recency(feed.entries, "product")
                
            for entry in recent_entries:
                title = getattr(entry, "title", None)
                link = getattr(entry, "link", None)
                description = getattr(entry, "description", "")
                
                # Extract category from description or default
                category = "productivity"  # default
                if description:
                    desc_lower = description.lower()
                    if "ai" in desc_lower or "artificial intelligence" in desc_lower:
                        category = "ai"
                    elif "design" in desc_lower or "ui" in desc_lower or "ux" in desc_lower:
                        category = "design"
                    elif "developer" in desc_lower or "code" in desc_lower or "api" in desc_lower:
                        category = "developer-tools"
                
                if not title or not link or link in seen:
                    continue
                    
                seen.add(link)
                products.append({
                    "name": title,
                    "link": link,
                    "description": description,
                    "category": category
                })
                
                if len(products) >= limit:
                    break
                    
        except Exception as e:
            print(f"[producthunt] Error fetching {url}: {e}")
            continue
    
    # If we couldn't get any products, try a fallback approach
    if not products:
        print("[producthunt] Trying fallback RSS feeds...")
        fallback_feeds = [
            "https://feeds.feedburner.com/ProductHunt",
            "https://www.producthunt.com/.rss"
        ]
        
        for url in fallback_feeds:
            try:
                feed = custom_feedparser(url)
                if feed.entries:
                    for entry in feed.entries[:10]:  # Limit to 10 from fallback
                        title = getattr(entry, "title", None)
                        link = getattr(entry, "link", None)
                        description = getattr(entry, "description", "")
                        
                        if title and link and link not in seen:
                            seen.add(link)
                            products.append({
                                "name": title,
                                "link": link,
                                "description": description,
                                "category": "productivity"
                            })
                            
                            if len(products) >= limit:
                                break
                                
            except Exception as e:
                print(f"[producthunt] Fallback error for {url}: {e}")
                continue
    
    return products

def extract_image_url(page_url: str) -> str | None:
    """Get og/twitter image and convert to a fetchable JPG via proxy."""
    try:
        r = requests.get(page_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        for attr, val in [
            ("property", "twitter:image:src"),
            ("name",     "twitter:image:src"),
            ("property", "twitter:image"),
            ("name",     "twitter:image"),
            ("property", "og:image"),
            ("name",     "og:image"),
        ]:
            tag = soup.find("meta", attrs={attr: val})
            if tag and tag.get("content"):
                raw = tag["content"].replace("&amp;", "&").strip()
                abs_url = urljoin(page_url, raw)
                return f"https://images.weserv.nl/?url={quote(abs_url)}&output=jpg"
        return None
    except Exception:
        return None

# ---------- Memory System ----------
# Memory files to track used books, quotes, tech news, reddit posts, products, and crypto
BOOKS_MEMORY_FILE = "data/books_memory.json"
QUOTES_MEMORY_FILE = "data/quotes_memory.json"
TECHNEWS_MEMORY_FILE = "data/technews_memory.json"
REDDIT_MEMORY_FILE = "data/reddit_memory.json"
PRODUCTS_MEMORY_FILE = "data/products_memory.json"
CRYPTO_MEMORY_FILE = "data/crypto_memory.json"
MAX_MEMORY = 25

def load_books_memory():
    """Load the memory of used books from file"""
    try:
        if os.path.exists(BOOKS_MEMORY_FILE):
            with open(BOOKS_MEMORY_FILE, 'r') as f:
                return json.load(f)
        return {"used_books": []}
    except Exception:
        return {"used_books": []}

def load_quotes_memory():
    """Load the memory of used quotes from file"""
    try:
        if os.path.exists(QUOTES_MEMORY_FILE):
            with open(QUOTES_MEMORY_FILE, 'r') as f:
                return json.load(f)
        return {"used_quotes": []}
    except Exception:
        return {"used_quotes": []}

def load_technews_memory():
    """Load the memory of used tech news articles from file"""
    try:
        if os.path.exists(TECHNEWS_MEMORY_FILE):
            with open(TECHNEWS_MEMORY_FILE, 'r') as f:
                return json.load(f)
        return {"used_articles": []}
    except Exception:
        return {"used_articles": []}

def load_reddit_memory():
    """Load the memory of used reddit posts from file"""
    try:
        if os.path.exists(REDDIT_MEMORY_FILE):
            with open(REDDIT_MEMORY_FILE, 'r') as f:
                return json.load(f)
        return {"used_posts": []}
    except Exception:
        return {"used_posts": []}

def load_products_memory():
    """Load the memory of used products from file"""
    try:
        if os.path.exists(PRODUCTS_MEMORY_FILE):
            with open(PRODUCTS_MEMORY_FILE, 'r') as f:
                return json.load(f)
        return {"used_products": []}
    except Exception:
        return {"used_products": []}

def load_crypto_memory():
    """Load the memory of used crypto articles from file"""
    try:
        if os.path.exists(CRYPTO_MEMORY_FILE):
            with open(CRYPTO_MEMORY_FILE, 'r') as f:
                return json.load(f)
        return {"used_articles": []}
    except Exception:
        return {"used_articles": []}

def save_memory(memory, filename):
    """Save the memory to file"""
    try:
        with open(filename, 'w') as f:
            json.dump(memory, f, indent=2)
    except Exception as e:
        print(f"⚠️  Warning: Could not save memory to {filename}: {e}")

def add_to_memory(memory, item_type, item, filename):
    """Add an item to memory and maintain max size"""
    # Only add if not already in memory
    if item not in memory[f"used_{item_type}"]:
        memory[f"used_{item_type}"].append(item)
        # Keep only the last MAX_MEMORY items
        if len(memory[f"used_{item_type}"]) > MAX_MEMORY:
            memory[f"used_{item_type}"] = memory[f"used_{item_type}"][-MAX_MEMORY:]
        save_memory(memory, filename)
        print(f"📝 Added '{item}' to {filename}")
    else:
        print(f"⚠️  '{item}' already in memory - skipping duplicate")

def extract_book_title(book_data):
    """Extract book title for memory tracking"""
    try:
        return book_data.get('book_title', '')
    except:
        pass
    return None

def extract_quote_topic(quotes_data):
    """Extract quote topic for memory tracking"""
    try:
        return quotes_data.get('topic', '')
    except:
        pass
    return None

def extract_article_identifier(tweet, source_url):
    """Extract article identifier for memory tracking"""
    try:
        # Use the source URL as the identifier since it's unique
        if source_url:
            # Extract domain and path for better identification
            from urllib.parse import urlparse
            parsed = urlparse(source_url)
            # Remove fragments (#) and query parameters (?)
            clean_path = parsed.path.split('#')[0].split('?')[0]
            return f"{parsed.netloc}{clean_path}"
    except:
        pass
    return None

def extract_reddit_identifier(post_data):
    """Extract reddit post identifier for memory tracking"""
    try:
        # Use the post title and subreddit as identifier
        title = post_data.get('title', '')
        subreddit = post_data.get('subreddit', '')
        return f"{subreddit}:{title[:50]}"  # First 50 chars of title
    except:
        pass
    return None

def extract_product_identifier(product_data):
    """Extract product identifier for memory tracking"""
    try:
        # Use the product name and category as identifier
        name = product_data.get('name', '')
        category = product_data.get('category', '')
        return f"{category}:{name[:50]}"  # First 50 chars of name
    except:
        pass
    return None

def shorten_url(long_url):
    """Shorten a URL using TinyURL service"""
    try:
        # Use TinyURL's API (free, no API key required)
        response = requests.get(f"http://tinyurl.com/api-create.php?url={long_url}", timeout=10)
        if response.status_code == 200:
            short_url = response.text.strip()
            print(f"🔗 Shortened: {long_url[:50]}... → {short_url}")
            return short_url
        else:
            print(f"⚠️  URL shortening failed for {long_url[:50]}...")
            return long_url
    except Exception as e:
        print(f"⚠️  URL shortening error: {e}")
        return long_url

def shorten_multiple_urls(urls):
    """Shorten multiple URLs and return a dict mapping original to shortened"""
    shortened = {}
    for url in urls:
        if url not in shortened:
            shortened[url] = shorten_url(url)
    return shortened

def clear_memory_files():
    """Clear all memory files to start fresh"""
    try:
        for filename in [BOOKS_MEMORY_FILE, QUOTES_MEMORY_FILE, TECHNEWS_MEMORY_FILE, REDDIT_MEMORY_FILE, PRODUCTS_MEMORY_FILE, CRYPTO_MEMORY_FILE]:
            if os.path.exists(filename):
                os.remove(filename)
                print(f"🗑️  Cleared {filename}")
        print("✅ All memory files cleared. Next run will start fresh!")
    except Exception as e:
        print(f"❌ Error clearing memory files: {e}")

def show_memory_status():
    """Show current memory status for all types"""
    print("\n📊 Memory Status:")
    print("=" * 50)
    
    # Books memory
    books_memory = load_books_memory()
    print(f"📚 Books: {len(books_memory['used_books'])}/{MAX_MEMORY}")
    if books_memory['used_books']:
        print(f"   Recent: {', '.join(books_memory['used_books'][-3:])}")
    
    # Quotes memory
    quotes_memory = load_quotes_memory()
    print(f"💭 Quotes: {len(quotes_memory['used_quotes'])}/{MAX_MEMORY}")
    if quotes_memory['used_quotes']:
        print(f"   Recent: {', '.join(quotes_memory['used_quotes'][-3:])}")
    
    # TechNews memory
    technews_memory = load_technews_memory()
    print(f"📰 TechNews: {len(technews_memory['used_articles'])}/{MAX_MEMORY}")
    if technews_memory['used_articles']:
        print(f"   Recent: {', '.join(technews_memory['used_articles'][-3:])}")
    
    # Reddit memory
    reddit_memory = load_reddit_memory()
    print(f"🔴 Reddit: {len(reddit_memory['used_posts'])}/{MAX_MEMORY}")
    if reddit_memory['used_posts']:
        print(f"   Recent: {', '.join(reddit_memory['used_posts'][-3:])}")
    
    # Products memory
    products_memory = load_products_memory()
    print(f"🚀 Products: {len(products_memory['used_products'])}/{MAX_MEMORY}")
    if products_memory['used_products']:
        print(f"   Recent: {', '.join(products_memory['used_products'][-3:])}")
    
    # Crypto memory
    crypto_memory = load_crypto_memory()
    print(f"₿ Crypto: {len(crypto_memory['used_articles'])}/{MAX_MEMORY}")
    if crypto_memory['used_articles']:
        print(f"   Recent: {', '.join(crypto_memory['used_articles'][-3:])}")
    
    print("=" * 50)
    
    # Show time filtering configuration
    print("\n⏰ Time Filtering Configuration:")
    print("=" * 30)
    for content_type, hours in MAX_CONTENT_AGE_HOURS.items():
        if content_type != "default":
            print(f"   {content_type.capitalize()}: {hours}h max age")
    print("=" * 30)

# ---------- Twitter Integration ----------
def post_to_twitter(tweet_text, account_name):
    """Post single tweet directly to Twitter"""
    try:
        # Find the account credentials
        account = next((acc for acc in accounts_data if acc["name"] == account_name), None)
        if not account:
            print(f"❌ No Twitter credentials found for {account_name}")
            return False
        
        # Authenticate with Twitter
        client = tweepy.Client(
            consumer_key=account["consumer_key"],
            consumer_secret=account["consumer_secret"],
            access_token=account["access_token"],
            access_token_secret=account["access_token_secret"]
        )
        
        # Post the tweet
        response = client.create_tweet(text=tweet_text)
        
        print(f"✅ Successfully posted to Twitter: {account_name}")
        print(f"Tweet URL: https://twitter.com/i/web/status/{response.data['id']}")
        return True
        
    except Exception as e:
        print(f"❌ Error posting to Twitter {account_name}: {e}")
        return False

def post_tweet_thread(tweets, account_name):
    """Post a series of tweets as a thread with rate limiting protection"""
    try:
        # Find the account credentials
        account = next((acc for acc in accounts_data if acc["name"] == account_name), None)
        if not account:
            print(f"❌ No Twitter credentials found for {account_name}")
            return False
        
        # Authenticate with Twitter
        client = tweepy.Client(
            consumer_key=account["consumer_key"],
            consumer_secret=account["consumer_secret"],
            access_token=account["access_token"],
            access_token_secret=account["access_token_secret"]
        )
        
        # Post the first tweet
        print(f"🐦 Posting Tweet 1/{len(tweets)}...")
        response = client.create_tweet(text=tweets[0])
        first_tweet_id = response.data['id']
        print(f"✅ Tweet 1 posted: https://twitter.com/i/web/status/{first_tweet_id}")
        
        # Post the remaining tweets as replies to create the thread
        previous_tweet_id = first_tweet_id
        
        for i, tweet in enumerate(tweets[1:], 2):
            print(f"🐦 Posting Tweet {i}/{len(tweets)}...")
            
            # Add delay between tweets to avoid rate limiting
            if i > 2:  # Skip delay for first reply
                print(f"   ⏳ Waiting 3 seconds to avoid rate limiting...")
                time.sleep(3)
            
            try:
                response = client.create_tweet(
                    text=tweet,
                    in_reply_to_tweet_id=previous_tweet_id
                )
                tweet_id = response.data['id']
                print(f"✅ Tweet {i} posted: https://twitter.com/i/web/status/{tweet_id}")
                previous_tweet_id = tweet_id
                
            except Exception as e:
                if "429" in str(e):
                    print(f"⚠️  Rate limited on Tweet {i}. Waiting 120 seconds...")
                    time.sleep(120)
                    # Try again after waiting
                    try:
                        response = client.create_tweet(
                            text=tweet,
                            in_reply_to_tweet_id=previous_tweet_id
                        )
                        tweet_id = response.data['id']
                        print(f"✅ Tweet {i} posted after retry: https://twitter.com/i/web/status/{tweet_id}")
                        previous_tweet_id = tweet_id
                    except Exception as retry_e:
                        print(f"❌ Failed to post Tweet {i} even after retry: {retry_e}")
                        return False
                else:
                    print(f"❌ Error posting Tweet {i}: {e}")
                    return False
        
        print(f"\n🎉 Successfully posted {len(tweets)}-tweet thread to Twitter: {account_name}")
        print(f"📱 Thread starts at: https://twitter.com/i/web/status/{first_tweet_id}")
        return True
        
    except Exception as e:
        print(f"❌ Error posting tweet thread to Twitter {account_name}: {e}")
        return False

# ---------- OpenAI Writers ----------
def write_technews(candidates: list[dict]) -> dict:
    """Generate high-signal, meaningful tech news content"""
    cjson = json.dumps(candidates[:8])  # keep prompt small
    
    # Import the enhanced prompt from prompts.py
    from utils.prompts import TECHNEWS_SYSTEM_PROMPT
    
    user = f"""Candidates (JSON array) - These have been pre-scored for quality:
{cjson}

IMPORTANT: These candidates have been pre-filtered for high-signal content. 
Choose the story that has the GREATEST REAL-WORLD IMPACT and EDUCATIONAL VALUE.

Focus on:
- Breakthrough technologies that change how we work/live
- Major industry transformations
- Scientific advances with practical applications
- Policy changes that affect tech development
- Economic shifts that alter the tech landscape

Return ONLY the JSON object specified above."""
    
    resp = client.chat.completions.create(
        model=OPENAI_MODEL,
        response_format={"type": "json_object"},
        messages=[{"role":"system","content":TECHNEWS_SYSTEM_PROMPT},
                  {"role":"user","content":user}],
        temperature=0.4,  # Lower temperature for more focused, factual content
    )
    raw = resp.choices[0].message.content or "{}"
    obj = json.loads(raw)
    # Ensure link text appended if model omitted it
    if obj.get("source_url") and "Learn more:" not in obj.get("tweet",""):
        obj["tweet"] = f'{obj["tweet"]} Learn more: {obj["source_url"]}'
    return obj

def write_crypto(candidates: list[dict]) -> dict:
    """Generate high-signal, meaningful crypto news content"""
    cjson = json.dumps(candidates[:8])  # keep prompt small
    
    # Import the enhanced prompt from prompts.py
    from utils.prompts import CRYPTO_SYSTEM_PROMPT
    
    user = f"""Candidates (JSON array) - These have been pre-scored for quality:
{cjson}

IMPORTANT: These candidates have been pre-filtered for high-signal content. 
Choose the story that has the GREATEST REAL-WORLD IMPACT and EDUCATIONAL VALUE.

Focus on:
- Regulatory developments that affect crypto adoption
- Institutional adoption and enterprise partnerships
- Security breakthroughs and vulnerabilities
- DeFi, NFT, and Web3 innovations
- Research and analysis on blockchain technology

Return ONLY the JSON object specified above."""
    
    resp = client.chat.completions.create(
        model=OPENAI_MODEL,
        response_format={"type": "json_object"},
        temperature=0.4,  # Lower temperature for more focused, factual content
        messages=[{"role":"system","content":CRYPTO_SYSTEM_PROMPT},
                  {"role":"user","content":user}],
    )
    raw = resp.choices[0].message.content or "{}"
    obj = json.loads(raw)
    # Ensure link text appended if model omitted it
    if obj.get("source_url") and "Learn more:" not in obj.get("tweet",""):
        obj["tweet"] = f'{obj["tweet"]} Learn more: {obj["source_url"]}'
    return obj

def write_books_thread():
    """Generate a 6-tweet thread about a book recommendation"""
    # Influential books list
    INFLUENTIAL_BOOKS = [
        '"Meditations" by Marcus Aurelius',
        '"The Art of War" by Sun Tzu',
        '"1984" by George Orwell',
        '"The Great Gatsby" by F. Scott Fitzgerald',
        '"To Kill a Mockingbird" by Harper Lee',
        '"The Catcher in the Rye" by J.D. Salinger',
        '"Pride and Prejudice" by Jane Austen',
        '"The Lord of the Rings" by J.R.R. Tolkien',
        '"The Hobbit" by J.R.R. Tolkien',
        '"The Alchemist" by Paulo Coelho',
        '"The Little Prince" by Antoine de Saint-Exupéry',
        '"Animal Farm" by George Orwell',
        '"Brave New World" by Aldous Huxley',
        '"Fahrenheit 451" by Ray Bradbury',
        '"The Handmaid\'s Tale" by Margaret Atwood',
        '"The Bell Jar" by Sylvia Plath',
        '"Slaughterhouse-Five" by Kurt Vonnegut',
        '"Catch-22" by Joseph Heller',
        '"The Grapes of Wrath" by John Steinbeck',
        '"Of Mice and Men" by John Steinbeck'
    ]
    
    # Load memory to avoid recently used books
    books_memory = load_books_memory()
    used_books = books_memory.get('used_books', [])
    
    # Filter out recently used books
    available_books = [book for book in INFLUENTIAL_BOOKS if book not in used_books]
    
    # If all books have been used recently, reset memory and use all books
    if not available_books:
        print("🔄 All books have been used recently. Resetting book memory...")
        books_memory['used_books'] = []
        save_memory(books_memory, BOOKS_MEMORY_FILE)
        available_books = INFLUENTIAL_BOOKS
    
    print(f"📚 Available books: {len(available_books)} out of {len(INFLUENTIAL_BOOKS)}")
    if used_books:
        print(f"📝 Recently used: {', '.join(used_books[-3:])}")  # Show last 3 used
    
    # Add stronger instruction to avoid duplicates
    system = f"""Return ONLY valid JSON exactly as:
{{"book_title":"...","author":"...","summary":"...","takeaways":["takeaway1","takeaway2","takeaway3","takeaway4","takeaway5"]}}

Role: Editor of "Books by Quinn".
Choose ONE book from this curated list and create a comprehensive 6-tweet thread.

CRITICAL: You MUST choose from these available books ONLY. Do NOT repeat recently used books:
{chr(10).join([f"- {book}" for book in available_books])}

Requirements:
- book_title: Just the book title (no quotes)
- author: Just the author name
- summary: A compelling 1-2 sentence summary of the book's main message (keep under 200 characters)
- takeaways: Array of 5 powerful, actionable insights from the book

Rules for takeaways:
- Each should be 1-2 sentences max
- Focus on practical wisdom and life lessons
- Make them universally applicable
- Avoid generic advice - be specific and insightful
- Each should stand alone as valuable insight
- Keep each takeaway under 250 characters to ensure room for numbering

IMPORTANT: Choose a DIFFERENT book from the available list above.

SUGGESTION: Consider choosing {random.choice(available_books) if available_books else 'a different book'} for variety.
"""

    try:
        resp = client.chat.completions.create(
            model=OPENAI_MODEL,
            response_format={"type": "json_object"},
            messages=[{"role": "system", "content": system}],
            temperature=0.7,
        )
        
        raw = resp.choices[0].message.content or "{}"
        obj = json.loads(raw)
        return obj
        
    except Exception as e:
        print(f"❌ Error generating content: {e}")
        return None

def create_books_thread(book_data):
    """Create the 6 tweets for the books thread"""
    tweets = []
    
    # Tweet 1: Book title + author + summary
    tweet1 = f"📚 **{book_data['book_title']}** by {book_data['author']}\n\n{book_data['summary']}"
    tweets.append(tweet1)
    
    # Tweets 2-6: Top 5 takeaways
    for i, takeaway in enumerate(book_data['takeaways'], 1):
        tweet = f"{i}. {takeaway}"
        tweets.append(tweet)
    
    return tweets

def write_quotes_thread():
    """Generate a 4-tweet thread with quotes on a specific topic"""
    # Load memory to avoid recently used topics
    quotes_memory = load_quotes_memory()
    used_topics = quotes_memory.get('used_quotes', [])
    
    # Available topics
    ALL_TOPICS = [
        "Leadership", "Perseverance", "Love & Romance", "Success", 
        "Wisdom", "Courage", "Creativity", "Friendship", 
        "Change", "Happiness", "Purpose", "Resilience"
    ]
    
    # Filter out recently used topics
    available_topics = [topic for topic in ALL_TOPICS if topic not in used_topics]
    
    # If all topics have been used recently, reset memory and use all topics
    if not available_topics:
        print("🔄 All topics have been used recently. Resetting quotes memory...")
        quotes_memory['used_quotes'] = []
        save_memory(quotes_memory, QUOTES_MEMORY_FILE)
        available_topics = ALL_TOPICS
    
    print(f"💭 Available topics: {len(available_topics)} out of {len(ALL_TOPICS)}")
    if used_topics:
        print(f"📝 Recently used: {', '.join(used_topics[-3:])}")  # Show last 3 used
    
    system = f"""Return ONLY valid JSON exactly as:
{{"topic":"...","quotes":[{{"quote":"...","author":"...","year":"..."}},{{"quote":"...","author":"...","year":"..."}},{{"quote":"...","author":"...","year":"..."}}]}}

Role: Editor of "Quotes by Quinn".
Choose ONE compelling topic and provide the 3 most powerful quotes on that subject.

CRITICAL: You MUST choose from these available topics ONLY. Do NOT repeat recently used topics:
{chr(10).join([f"- {topic}" for topic in available_topics])}

Requirements:
- topic: Choose one of the topics above
- quotes: Array of 3 powerful quotes on that topic
- Each quote should include: quote text, author name, and year
- Focus on the highest signal, most impactful quotes
- Choose quotes that are universally applicable and timeless

Rules for quotes:
- Each quote should be 1-2 sentences max
- Focus on practical wisdom and life lessons
- Make them inspiring and thought-provoking
- Use realistic years (e.g., 1800-2020 range)
- Each should stand alone as valuable insight
- Keep each quote under 200 characters to ensure room for author/year

IMPORTANT: Choose a DIFFERENT topic from the available list above.

SUGGESTION: Consider choosing {random.choice(available_topics) if available_topics else 'a different topic'} for variety.
"""

    try:
        resp = client.chat.completions.create(
            model=OPENAI_MODEL,
            response_format={"type": "json_object"},
            messages=[{"role": "system", "content": system}],
            temperature=0.7,
        )
        
        raw = resp.choices[0].message.content or "{}"
        obj = json.loads(raw)
        return obj
        
    except Exception as e:
        print(f"❌ Error generating content: {e}")
        return None

def create_quotes_thread(quotes_data):
    """Create the 4 tweets for the quotes thread"""
    tweets = []
    
    # Tweet 1: Topic introduction
    topic = quotes_data['topic']
    tweet1 = f"💭 Most important quotes on {topic}"
    tweets.append(tweet1)
    
    # Tweets 2-4: Top 3 quotes with author and year
    for i, quote_data in enumerate(quotes_data['quotes'], 1):
        quote = quote_data['quote']
        author = quote_data['author']
        year = quote_data['year']
        tweet = f"{i}. \"{quote}\" - {author}, {year}"
        tweets.append(tweet)
    
    return tweets

def write_reddit_summary(reddit_posts):
    """Generate a single tweet summarizing the top 5 Reddit posts"""
    # Take top 5 posts
    top_posts = reddit_posts[:5]
    
    # Shorten all URLs first to save space
    print("🔗 Shortening Reddit URLs to save space...")
    urls_to_shorten = [post['link'] for post in top_posts]
    shortened_urls = shorten_multiple_urls(urls_to_shorten)
    
    # Update posts with shortened URLs
    for post in top_posts:
        post['short_link'] = shortened_urls.get(post['link'], post['link'])
    
    system = """Return ONLY valid JSON exactly as:
{"tweet":"...","summary":"..."}

Role: Editor of "Reddit by Quinn".
Create a single tweet summarizing the top 5 Reddit posts of the day.

CRITICAL REQUIREMENTS:
- tweet: Must be ≤ 280 characters total (this is a hard limit)
- Include all 5 posts with their shortened links
- Use extremely short, concise descriptions
- Focus on the most essential information only

Format: "🔥 Top Reddit today: [very brief summary] 1. [3-5 word title] [short_link] 2. [3-5 word title] [short_link] ..."

Rules:
- Each post description should be 3-5 words maximum
- Use abbreviations and short forms where possible
- Prioritize shortened links over descriptions
- Test character count before returning
- If over 280 chars, make descriptions even shorter
"""

    # Prepare post data for GPT with shortened URLs
    posts_data = []
    for i, post in enumerate(top_posts, 1):
        posts_data.append({
            "number": i,
            "title": post['title'],
            "subreddit": post['subreddit'],
            "link": post['short_link']  # Use shortened URL
        })
    
    user = f"""Top 5 Reddit posts to summarize (with shortened URLs):
{json.dumps(posts_data, indent=2)}

Create a single tweet summarizing these posts with all shortened links included."""
    
    try:
        resp = client.chat.completions.create(
            model=OPENAI_MODEL,
            response_format={"type": "json_object"},
            messages=[{"role": "system", "content": system},
                      {"role": "user", "content": user}],
            temperature=0.7,
        )
        
        raw = resp.choices[0].message.content or "{}"
        obj = json.loads(raw)
        
        # Add the posts data for memory tracking
        obj['posts'] = top_posts
        
        return obj
        
    except Exception as e:
        print(f"❌ Error generating Reddit content: {e}")
        return None

def write_product_summary(product_list):
    """Generate a single tweet about a standout product from ProductHunt"""
    # Take the first product (most recent)
    if not product_list:
        return None
        
    product = product_list[0]
    
    # Shorten the product URL
    print("🔗 Shortening ProductHunt URL...")
    short_url = shorten_url(product['link'])
    
    system = """Return ONLY valid JSON exactly as:
{"tweet":"...","summary":"..."}

Role: Editor of "Product by Quinn".
Create a single tweet about a ProductHunt product.

CRITICAL REQUIREMENTS:
- tweet: Must be ≤ 280 characters total (this is a hard limit)
- Format: "🚀 [Product Name] — [What it does in 1 sentence] + [Ideal user in 3-5 words] + [1 standout feature in 5-8 words] + Learn more: [shortened_url]"
- Keep descriptions concise but informative
- Focus on the most compelling aspects

Rules:
- Product name: Keep it short
- What it does: 1 clear sentence
- Ideal user: 3-5 words maximum
- Standout feature: 5-8 words maximum
- Always end with "Learn more: [URL]"
- Test character count before returning
"""

    user = f"""ProductHunt product to feature:
Name: {product['name']}
Category: {product['category']}
Description: {product['description'][:200]}...
Link: {short_url}

Create a tweet following the exact format specified above."""

    try:
        resp = client.chat.completions.create(
            model=OPENAI_MODEL,
            response_format={"type": "json_object"},
            messages=[{"role": "system", "content": system},
                      {"role": "user", "content": user}],
            temperature=0.7,
        )
        
        raw = resp.choices[0].message.content or "{}"
        obj = json.loads(raw)
        
        # Add the product data for memory tracking
        obj['product'] = product
        
        return obj
        
    except Exception as e:
        print(f"❌ Error generating product content: {e}")
        return None

# ---------- Main execution ----------
def run_specific_accounts(account_types: list[str]):
    """Run only specific account types"""
    print(f"🚀 Running specific accounts: {', '.join(account_types)}")
    print()
    
    # Load memory for all types
    books_memory = load_books_memory()
    quotes_memory = load_quotes_memory()
    technews_memory = load_technews_memory()
    reddit_memory = load_reddit_memory()
    products_memory = load_products_memory()
    crypto_memory = load_crypto_memory()
    
    # Show memory status for requested types
    for account_type in account_types:
        if account_type == "books":
            print(f"📚 Books memory: {len(books_memory['used_books'])} books used in last {MAX_MEMORY} runs")
        elif account_type == "quotes":
            print(f"💭 Quotes memory: {len(quotes_memory['used_quotes'])} quotes used in last {MAX_MEMORY} runs")
        elif account_type == "technews":
            print(f"📰 TechNews memory: {len(technews_memory['used_articles'])} articles used in last {MAX_MEMORY} runs")
        elif account_type == "reddit":
            print(f"🔴 Reddit memory: {len(reddit_memory['used_posts'])} posts used in last {MAX_MEMORY} runs")
        elif account_type == "product":
            print(f"🚀 Products memory: {len(products_memory['used_products'])} products used in last {MAX_MEMORY} runs")
        elif account_type == "crypto":
            print(f"₿ Crypto memory: {len(crypto_memory['used_articles'])} articles used in last {MAX_MEMORY} runs")
    print()
    
    # Process only the requested account types
    for account in ACCOUNTS:
        handle = account["handle"]
        account_type = account["type"]
        
        if account_type not in account_types:
            continue
            
        print(f"--- Processing {handle} ({account_type}) ---")
        
        # Show content quality info for TechNews
        if account_type == "technews":
            cands = fetch_candidates()
            if not cands:
                print("No candidates found; skipping TechNews.")
                continue
            print(f"📊 Content Quality: {len(cands)} pre-scored candidates")
            
            # Filter out already used articles BEFORE generating content
            cands = filter_used_articles(cands, technews_memory)
            if not cands:
                print("❌ No new articles available after filtering; all candidates have been used recently.")
                continue
                
            if cands:
                top_candidate = cands[0]
                print(f"🏆 Top candidate: {top_candidate['title'][:80]}... (Score: {top_candidate['score']})")
                print(f"📰 Source: {top_candidate['source']}")
                print()
        
        try:
            if account_type == "technews":
                # Generate and post TechNews as single tweet
                choice = write_technews(cands)
                tweet = choice.get("tweet", "").strip()
                src = choice.get("source_url")
                image_url = extract_image_url(src) if src else None

                print(f"Tweet: {tweet}")
                print(f"Source: {src}")
                print(f"Image: {image_url or '(none)'}")
                
                # Track in memory BEFORE posting to prevent duplicates
                article_id = extract_article_identifier(tweet, src)
                if article_id:
                    add_to_memory(technews_memory, "articles", article_id, TECHNEWS_MEMORY_FILE)
                    print(f"📝 Added article '{article_id}' to technews memory")
                
                # Post directly to Twitter
                print("\n🐦 Posting TechNews directly to Twitter...")
                post_to_twitter(tweet, handle)
                
            elif account_type == "books":
                # Generate and post Books as 6-tweet thread
                choice = write_books_thread()
                if not choice:
                    print("❌ Failed to generate book content")
                    continue
                
                print(f"📖 Generated Book Thread:")
                print(f"Book: {choice['book_title']} by {choice['author']}")
                print(f"Summary: {choice['summary']}")
                print(f"\nTop 5 Takeaways:")
                for i, takeaway in enumerate(choice['takeaways'], 1):
                    print(f"{i}. {takeaway}")
                
                # Create the tweet thread
                tweets = create_books_thread(choice)
                
                print(f"\n🐦 Tweet Thread Preview:")
                for i, tweet in enumerate(tweets, 1):
                    print(f"\n--- Tweet {i}/6 ({len(tweet)} chars) ---")
                    print(tweet)
                
                # Track in memory
                book_title = extract_book_title(choice)
                if book_title:
                    add_to_memory(books_memory, "books", book_title, BOOKS_MEMORY_FILE)
                    print(f"📝 Added '{book_title}' to books memory")
                
                # Post thread directly to Twitter
                print(f"\n🐦 Posting book thread to Twitter...")
                success = post_tweet_thread(tweets, handle)
                if not success:
                    print("⚠️  Book thread posting failed - this may be due to duplicate content or rate limiting")
                    print("   The book has been added to memory to prevent future duplicates")
                
            elif account_type == "quotes":
                # Generate and post Quotes as 4-tweet thread
                choice = write_quotes_thread()
                if not choice:
                    print("❌ Failed to generate quotes content")
                    continue
                
                print(f"💭 Generated Quotes Thread:")
                print(f"Topic: {choice['topic']}")
                print(f"\nTop 3 Quotes:")
                for i, quote_data in enumerate(choice['quotes'], 1):
                    print(f"{i}. \"{quote_data['quote']}\" - {quote_data['author']}, {quote_data['year']}")
                
                # Create the tweet thread
                tweets = create_quotes_thread(choice)
                
                print(f"\n🐦 Tweet Thread Preview:")
                for i, tweet in enumerate(tweets, 1):
                    print(f"\n--- Tweet {i}/4 ({len(tweet)} chars) ---")
                    print(tweet)
                
                # Track in memory
                quote_topic = extract_quote_topic(choice)
                if quote_topic:
                    add_to_memory(quotes_memory, "quotes", quote_topic, QUOTES_MEMORY_FILE)
                    print(f"📝 Added topic '{quote_topic}' to quotes memory")
                
                # Post thread directly to Twitter
                print(f"\n🐦 Posting quotes thread to Twitter...")
                success = post_tweet_thread(tweets, handle)
                if not success:
                    print("⚠️  Quotes thread posting failed - this may be due to duplicate content or rate limiting")
                    print("   The topic has been added to memory to prevent future duplicates")
                
            elif account_type == "reddit":
                # Generate and post Reddit summary as single tweet
                reddit_posts = fetch_reddit_posts(limit=20)
                if not reddit_posts:
                    print("❌ Failed to fetch Reddit posts")
                    continue
                
                print(f"🔴 Fetched {len(reddit_posts)} Reddit posts")
                print(f"Top 5 posts:")
                for i, post in enumerate(reddit_posts[:5], 1):
                    print(f"{i}. r/{post['subreddit']}: {post['title'][:60]}...")
                
                choice = write_reddit_summary(reddit_posts)
                if not choice:
                    print("❌ Failed to generate Reddit content")
                    continue
                
                tweet = choice.get("tweet", "").strip()
                print(f"\n🔴 Generated Reddit Summary:")
                print(f"Tweet: {tweet}")
                print(f"Character count: {len(tweet)}/280")
                
                # Track in memory
                for post in choice.get('posts', []):
                    post_id = extract_reddit_identifier(post)
                    if post_id:
                        add_to_memory(reddit_memory, "posts", post_id, REDDIT_MEMORY_FILE)
                
                # Post directly to Twitter
                print(f"\n🐦 Posting Reddit summary to Twitter...")
                success = post_to_twitter(tweet, handle)
                if not success:
                    print("⚠️  Reddit summary posting failed")
                
            elif account_type == "product":
                # Generate and post ProductHunt product as single tweet
                product_list = fetch_producthunt_products(limit=10)
                if not product_list:
                    print("❌ Failed to fetch ProductHunt products")
                    continue
                
                print(f"🚀 Fetched {len(product_list)} ProductHunt products")
                print(f"Top product: {product_list[0]['name']} ({product_list[0]['category']})")
                
                choice = write_product_summary(product_list)
                if not choice:
                    print("❌ Failed to generate product content")
                    continue
                
                tweet = choice.get("tweet", "").strip()
                print(f"\n🚀 Generated Product Summary:")
                print(f"Tweet: {tweet}")
                print(f"Character count: {len(tweet)}/280")
                
                # Track in memory
                product_id = extract_product_identifier(choice.get('product', {}))
                if product_id:
                    add_to_memory(products_memory, "products", product_id, PRODUCTS_MEMORY_FILE)
                
                # Post directly to Twitter
                print(f"\n🐦 Posting product summary to Twitter...")
                success = post_to_twitter(tweet, handle)
                if not success:
                    print("⚠️  Product summary posting failed")
                
            elif account_type == "crypto":
                # Generate and post Crypto as single tweet
                crypto_cands = fetch_crypto_candidates()
                if not crypto_cands:
                    print("❌ No crypto candidates found; skipping Crypto.")
                    continue
                print(f"📊 Crypto Content Quality: {len(crypto_cands)} pre-scored candidates")
                
                # Filter out already used articles BEFORE generating content
                crypto_cands = filter_used_articles(crypto_cands, crypto_memory)
                if not crypto_cands:
                    print("❌ No new crypto articles available after filtering; all candidates have been used recently.")
                    continue
                    
                if crypto_cands:
                    top_candidate = crypto_cands[0]
                    print(f"🏆 Top candidate: {top_candidate['title'][:80]}... (Score: {top_candidate['score']})")
                    print(f"📰 Source: {top_candidate['source']}")
                    print()
                
                choice = write_crypto(crypto_cands)
                tweet = choice.get("tweet", "").strip()
                src = choice.get("source_url")
                image_url = extract_image_url(src) if src else None

                print(f"Tweet: {tweet}")
                print(f"Source: {src}")
                print(f"Image: {image_url or '(none)'}")
                
                # Track in memory BEFORE posting to prevent duplicates
                article_id = extract_article_identifier(tweet, src)
                if article_id:
                    add_to_memory(crypto_memory, "articles", article_id, CRYPTO_MEMORY_FILE)
                    print(f"📝 Added article '{article_id}' to crypto memory")
                
                # Post directly to Twitter
                print("\n🐦 Posting Crypto directly to Twitter...")
                success = post_to_twitter(tweet, handle)
                if not success:
                    print("⚠️  Crypto posting failed")
                
            else:
                print(f"Unknown account type: {account_type}")
                continue
            
            print()
            
            # Add delay between account types to avoid overwhelming Twitter's API
            if account_type != "technews":  # Skip delay after technews since it's first
                print("⏳ Waiting 5 seconds before processing next account...")
                time.sleep(5)
                print()
            
        except Exception as e:
            print(f"❌ Error processing {handle}: {e}")
            print()

def main():
    """Run all account types"""
    cands = fetch_candidates()
    if not cands:
        print("No candidates found; exiting.")
        return

    print(f"Found {len(cands)} candidates from RSS feeds\n")

    # Load memory for books, quotes, tech news, reddit posts, and products
    books_memory = load_books_memory()
    quotes_memory = load_quotes_memory()
    technews_memory = load_technews_memory()
    reddit_memory = load_reddit_memory()
    products_memory = load_products_memory()
    print(f"📚 Books memory: {len(books_memory['used_books'])} books used in last {MAX_MEMORY} runs")
    print(f"💭 Quotes memory: {len(quotes_memory['used_quotes'])} quotes used in last {MAX_MEMORY} runs")
    print(f"📰 TechNews memory: {len(technews_memory['used_articles'])} articles used in last {MAX_MEMORY} runs")
    print(f"🔴 Reddit memory: {len(reddit_memory['used_posts'])} posts used in last {MAX_MEMORY} runs")
    print(f"🚀 Products memory: {len(products_memory['used_products'])} products used in last {MAX_MEMORY} runs\n")

    # Process each account type
    for account in ACCOUNTS:
        handle = account["handle"]
        account_type = account["type"]
        
        print(f"--- Processing {handle} ({account_type}) ---")
        
        # Show content quality info for TechNews
        if account_type == "technews":
            print(f"📊 Content Quality: {len(cands)} pre-scored candidates")
            
            # Filter out already used articles BEFORE generating content
            cands = filter_used_articles(cands, technews_memory)
            if not cands:
                print("❌ No new articles available after filtering; all candidates have been used recently.")
                continue
                
            if cands:
                top_candidate = cands[0]
                print(f"🏆 Top candidate: {top_candidate['title'][:80]}... (Score: {top_candidate['score']})")
                print(f"📰 Source: {top_candidate['source']}")
                print()
        
        try:
            if account_type == "technews":
                # Generate and post TechNews as single tweet
                choice = write_technews(cands)
                tweet = choice.get("tweet", "").strip()
                src = choice.get("source_url")
                image_url = extract_image_url(src) if src else None

                print(f"Tweet: {tweet}")
                print(f"Source: {src}")
                print(f"Image: {image_url or '(none)'}")
                
                # Track in memory BEFORE posting to prevent duplicates
                article_id = extract_article_identifier(tweet, src)
                if article_id:
                    add_to_memory(technews_memory, "articles", article_id, TECHNEWS_MEMORY_FILE)
                    print(f"📝 Added article '{article_id}' to technews memory")
                
                # Post directly to Twitter
                print("\n🐦 Posting TechNews directly to Twitter...")
                post_to_twitter(tweet, handle)
                
            elif account_type == "books":
                # Generate and post Books as 6-tweet thread
                choice = write_books_thread()
                if not choice:
                    print("❌ Failed to generate book content")
                    continue
                
                print(f"📖 Generated Book Thread:")
                print(f"Book: {choice['book_title']} by {choice['author']}")
                print(f"Summary: {choice['summary']}")
                print(f"\nTop 5 Takeaways:")
                for i, takeaway in enumerate(choice['takeaways'], 1):
                    print(f"{i}. {takeaway}")
                
                # Create the tweet thread
                tweets = create_books_thread(choice)
                
                print(f"\n🐦 Tweet Thread Preview:")
                for i, tweet in enumerate(tweets, 1):
                    print(f"\n--- Tweet {i}/6 ({len(tweet)} chars) ---")
                    print(tweet)
                
                # Track in memory
                book_title = extract_book_title(choice)
                if book_title:
                    add_to_memory(books_memory, "books", book_title, BOOKS_MEMORY_FILE)
                    print(f"📝 Added '{book_title}' to books memory")
                
                # Post thread directly to Twitter
                print(f"\n🐦 Posting book thread to Twitter...")
                success = post_tweet_thread(tweets, handle)
                if not success:
                    print("⚠️  Book thread posting failed - this may be due to duplicate content or rate limiting")
                    print("   The book has been added to memory to prevent future duplicates")
                
            elif account_type == "quotes":
                # Generate and post Quotes as 4-tweet thread
                choice = write_quotes_thread()
                if not choice:
                    print("❌ Failed to generate quotes content")
                    continue
                
                print(f"💭 Generated Quotes Thread:")
                print(f"Topic: {choice['topic']}")
                print(f"\nTop 3 Quotes:")
                for i, quote_data in enumerate(choice['quotes'], 1):
                    print(f"{i}. \"{quote_data['quote']}\" - {quote_data['author']}, {quote_data['year']}")
                
                # Create the tweet thread
                tweets = create_quotes_thread(choice)
                
                print(f"\n🐦 Tweet Thread Preview:")
                for i, tweet in enumerate(tweets, 1):
                    print(f"\n--- Tweet {i}/4 ({len(tweet)} chars) ---")
                    print(tweet)
                
                # Track in memory
                quote_topic = extract_quote_topic(choice)
                if quote_topic:
                    add_to_memory(quotes_memory, "quotes", quote_topic, QUOTES_MEMORY_FILE)
                    print(f"📝 Added topic '{quote_topic}' to quotes memory")
                
                # Post thread directly to Twitter
                print(f"\n🐦 Posting quotes thread to Twitter...")
                success = post_tweet_thread(tweets, handle)
                if not success:
                    print("⚠️  Quotes thread posting failed - this may be due to duplicate content or rate limiting")
                    print("   The topic has been added to memory to prevent future duplicates")
                
            elif account_type == "reddit":
                # Generate and post Reddit summary as single tweet
                reddit_posts = fetch_reddit_posts(limit=20)
                if not reddit_posts:
                    print("❌ Failed to fetch Reddit posts")
                    continue
                
                print(f"🔴 Fetched {len(reddit_posts)} Reddit posts")
                print(f"Top 5 posts:")
                for i, post in enumerate(reddit_posts[:5], 1):
                    print(f"{i}. r/{post['subreddit']}: {post['title'][:60]}...")
                
                choice = write_reddit_summary(reddit_posts)
                if not choice:
                    print("❌ Failed to generate Reddit content")
                    continue
                
                tweet = choice.get("tweet", "").strip()
                print(f"\n🔴 Generated Reddit Summary:")
                print(f"Tweet: {tweet}")
                print(f"Character count: {len(tweet)}/280")
                
                # Track in memory
                for post in choice.get('posts', []):
                    post_id = extract_reddit_identifier(post)
                    if post_id:
                        add_to_memory(reddit_memory, "posts", post_id, REDDIT_MEMORY_FILE)
                
                # Post directly to Twitter
                print(f"\n🐦 Posting Reddit summary to Twitter...")
                success = post_to_twitter(tweet, handle)
                if not success:
                    print("⚠️  Reddit summary posting failed")
                
            elif account_type == "product":
                # Generate and post ProductHunt product as single tweet
                product_list = fetch_producthunt_products(limit=10)
                if not product_list:
                    print("❌ Failed to fetch ProductHunt products")
                    continue
                
                print(f"🚀 Fetched {len(product_list)} ProductHunt products")
                print(f"Top product: {product_list[0]['name']} ({product_list[0]['category']})")
                
                choice = write_product_summary(product_list)
                if not choice:
                    print("❌ Failed to generate product content")
                    continue
                
                tweet = choice.get("tweet", "").strip()
                print(f"\n🚀 Generated Product Summary:")
                print(f"Tweet: {tweet}")
                print(f"Character count: {len(tweet)}/280")
                
                # Track in memory
                product_id = extract_product_identifier(choice.get('product', {}))
                if product_id:
                    add_to_memory(products_memory, "products", product_id, PRODUCTS_MEMORY_FILE)
                
                # Post directly to Twitter
                print(f"\n🐦 Posting product summary to Twitter...")
                success = post_to_twitter(tweet, handle)
                if not success:
                    print("⚠️  Product summary posting failed")
                
            else:
                print(f"Unknown account type: {account_type}")
                continue
            
            print()
            
            # Add delay between account types to avoid overwhelming Twitter's API
            if account_type != "technews":  # Skip delay after technews since it's first
                print("⏳ Waiting 5 seconds before processing next account...")
                time.sleep(5)
                print()
            
        except Exception as e:
            print(f"❌ Error processing {handle}: {e}")
            print()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "clear":
            clear_memory_files()
        elif command == "status":
            show_memory_status()
        elif command == "help":
            print("""
🔧 Quinn Social Media Bot - Command Line Options:

Usage:
  python main.py           # Run the full bot
  python main.py clear     # Clear all memory files
  python main.py status    # Show memory status
  python main.py help      # Show this help

Memory Management:
  - clear: Removes all memory files to start fresh
  - status: Shows current memory usage for all content types
  - help: Displays this help message

Examples:
  python main.py clear     # Start fresh with no memory
  python main.py status    # Check what's been used recently
            """)
        else:
            print(f"❌ Unknown command: {command}")
            print("Use 'python main.py help' for available commands")
    else:
        main()
