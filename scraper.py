import json
import os
import csv
import requests
import time

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

def categorize_tweet(text):
    if not GEMINI_API_KEY:
        print("CRITICAL: GEMINI_API_KEY environment variable is missing!")
        return "Product Strategy"
    
    # Updated to the active production model routing path for gemini-2.5-flash
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
    headers = {"Content-Type": "application/json"}
    
    prompt = f"""
    Categorize this tweet by startup founder Nikita Bier into exactly ONE of these topics: 
    'Viral Growth Loops', 'Product Strategy', 'Consumer Psychology', 'Fundraising & Exits', or 'Satire & Humor'.
    Respond with ONLY the category name. Do not include quotes, formatting, or extra text.
    
    Tweet: "{text}"
    """
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        res_json = response.json()
        
        if "error" in res_json:
            print(f"Gemini API Error: {res_json['error']['message']} (Code: {res_json['error']['code']})")
            return "Product Strategy"
            
        category = res_json['candidates'][0]['content']['parts'][0]['text'].strip()
        category = category.replace("*", "").replace("`", "").strip()
        
        valid_categories = ['Viral Growth Loops', 'Product Strategy', 'Consumer Psychology', 'Fundraising & Exits', 'Satire & Humor']
        if category in valid_categories:
            return category
        else:
            return "Product Strategy"
    except Exception as e:
        print(f"Network error: {e}")
        return "Product Strategy"

def main():
    csv_path = "raw_tweets.csv"
    json_path = "docs/tweets.json"
    
    if not os.path.exists(csv_path):
        print("No raw_tweets.csv found.")
        return

    database = []
    existing_ids = set()
    
    with open(csv_path, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            tweet_id = str(row.get('id') or '').strip()
            text = row.get('text') or ''
            date = row.get('date') or ''
            
            if not tweet_id or "E+" in tweet_id or tweet_id.lower() == "none" or len(text) < 15:
                continue
                
            if tweet_id not in existing_ids:
                print(f"Processing tweet ID: {tweet_id}")
                category = categorize_tweet(text)
                print(f"-> Assigned Category: {category}")
                
                database.append({
                    "id": tweet_id,
                    "text": str(text),
                    "category": category,
                    "date": str(date)
                })
                existing_ids.add(tweet_id)
                time.sleep(4.5) # Respecting the free tier pacing loop

    with open(json_path, "w", encoding='utf-8') as f:
        json.dump(database, f, indent=2, ensure_ascii=False)
    print(f"Success! Compiled {len(database)} valid insights into NikiPedia.")

if __name__ == "__main__":
    main()
