#!/usr/bin/env python3
"""
Twitter API Authentication Test Script
This script tests each Twitter account's credentials to identify authentication issues.
"""

import tweepy
from config.twitter_dict import accounts_data

def test_twitter_auth():
    """Test Twitter authentication for each account"""
    print("🔍 Testing Twitter API Authentication...")
    print("=" * 60)
    
    for account in accounts_data:
        print(f"\n📱 Testing: {account['name']}")
        print("-" * 40)
        
        try:
            # Create client
            client = tweepy.Client(
                consumer_key=account["consumer_key"],
                consumer_secret=account["consumer_secret"],
                access_token=account["access_token"],
                access_token_secret=account["access_token_secret"]
            )
            
            # Test 1: Get user info
            print("✅ Testing user info...")
            user = client.get_me()
            if user.data:
                print(f"   ✅ User: @{user.data.username} (ID: {user.data.id})")
                print(f"   ✅ Name: {user.data.name}")
                print(f"   ✅ Verified: {user.data.verified}")
            else:
                print("   ❌ Could not get user info")
                continue
            
            # Test 2: Get recent tweets
            print("✅ Testing tweet retrieval...")
            tweets = client.get_users_tweets(
                id=user.data.id,
                max_results=5,
                tweet_fields=['created_at', 'public_metrics']
            )
            
            if tweets.data:
                print(f"   ✅ Found {len(tweets.data)} tweets")
                for i, tweet in enumerate(tweets.data[:2]):  # Show first 2
                    print(f"   📝 Tweet {i+1}: {tweet.text[:80]}...")
            else:
                print("   ⚠️  No tweets found (account might be new)")
            
            print(f"   ✅ {account['name']} authentication successful!")
            
        except tweepy.Unauthorized as e:
            print(f"   ❌ UNAUTHORIZED: {e}")
            print("   💡 This usually means:")
            print("      - Access token is invalid/expired")
            print("      - App permissions are insufficient")
            print("      - App has been suspended")
            
        except tweepy.Forbidden as e:
            print(f"   ❌ FORBIDDEN: {e}")
            print("   💡 This usually means:")
            print("      - App doesn't have required permissions")
            print("      - Rate limit exceeded")
            print("      - Account is suspended")
            
        except tweepy.TooManyRequests as e:
            print(f"   ❌ RATE LIMITED: {e}")
            print("   💡 Wait a few minutes and try again")
            
        except Exception as e:
            print(f"   ❌ ERROR: {type(e).__name__}: {e}")
            
        print()
    
    print("=" * 60)
    print("🔍 Authentication test completed!")
    print("\n💡 If you see UNAUTHORIZED errors:")
    print("   1. Go to https://developer.twitter.com/en/portal/dashboard")
    print("   2. Check your app's permissions (should be 'Read and Write')")
    print("   3. Regenerate your access tokens")
    print("   4. Ensure your app is not suspended")

if __name__ == "__main__":
    test_twitter_auth()
