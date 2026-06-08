import json
import os
import requests
from datetime import datetime

# We use Gemini's Free Tier to categorize the text
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

def categorize_tweet(text):
    if not GEMINI_API_KEY:
        return "Uncategorized"
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    headers = {"Content-Type": "application/json"}
    
    prompt = f"""
    Categorize this tweet by startup founder Nikita Bier into exactly ONE of these topics: 
    'Viral Growth Loops', 'Product Strategy', 'Consumer Psychology', 'Fundraising & Exits', or 'Satire & Humor'.
    Respond with ONLY the category name.
    
    Tweet: "{text}"
    """
    
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        result = response.json()
        category = result['candidates'][0]['content']['parts'][0]['text'].strip()
        return category if category in ['Viral Growth Loops', 'Product Strategy', 'Consumer Psychology', 'Fundraising & Exits', 'Satire & Humor'] else "Product Strategy"
    except:
        return "Product Strategy"

def fetch_latest_tweets():
    # Using an open guest-token wrapper/RSS bridge to grab his public feed for free
    # For stability, we pull from an open RSS-to-JSON mirror of X profiles
    url = "https://api.rss2json.com/v1/api.json?rss_url=https://nitter.net/nikitabier/rss"
    
    try:
        response = requests.get(url, timeout=10)
        items = response.json().get('items', [])
        
        new_tweets = []
        for item in items:
            # Extracting the Tweet ID from the link
            tweet_id = item['link'].split('/')[-1].split('#')[0]
            clean_text = item['description'] # Cleans up HTML if necessary
            
            new_tweets.append({
                "id": tweet_id,
                "text": item['title'], # Fallback text snippet
                "date": item['pubDate'].split(' ')[0]
            })
        return new_tweets
    except Exception as e:
        print(f"Error fetching: {e}")
        return []

def main():
    json_path = "docs/tweets.json"
    
    # Load existing database
    if os.path.exists(json_path):
        with open(json_path, "r") as f:
            database = json.load(f)
    else:
        database = []
        
    existing_ids = {t["id"] for t in database}
    fetched = fetch_latest_tweets()
    
    has_updates = False
    for tweet in fetched:
        if tweet["id"] not in existing_ids:
            print(f"Processing new tweet: {tweet['id']}")
            tweet["category"] = categorize_tweet(tweet["text"])
            database.insert(0, tweet) # Add new ones to the top
            has_updates = True
            
    if has_updates:
        with open(json_path, "w") as f:
            json.dump(database, f, indent=2)
        print("Database updated successfully.")
    else:
        print("No new tweets found.")

if __name__ == "__main__":
    main()
