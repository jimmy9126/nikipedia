import json
import os
import csv
import requests

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

def categorize_tweet(text):
    if not GEMINI_API_KEY:
        print("WARNING: GEMINI_API_KEY environment variable is missing!")
        return "Product Strategy"
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    headers = {"Content-Type": "application/json"}
    
    prompt = f"""
    Categorize this tweet by startup founder Nikita Bier into exactly ONE of these topics: 
    'Viral Growth Loops', 'Product Strategy', 'Consumer Psychology', 'Fundraising & Exits', or 'Satire & Humor'.
    Respond with ONLY the category name. Do not include quotes or punctuation.
    
    Tweet: "{text}"
    """
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        res_json = response.json()
        
        # If the API returned an error message, print it clearly in logs
        if "error" in res_json:
            print(f"Gemini API Error: {res_json['error']['message']}")
            return "Product Strategy"
            
        category = res_json['candidates'][0]['content']['parts'][0]['text'].strip()
        valid_categories = ['Viral Growth Loops', 'Product Strategy', 'Consumer Psychology', 'Fundraising & Exits', 'Satire & Humor']
        return category if category in valid_categories else "Product Strategy"
    except Exception as e:
        print(f"Network/Parsing Error during categorization: {e}")
        return "Product Strategy"

def main():
    csv_path = "raw_tweets.csv"
    json_path = "docs/tweets.json"
    
    if not os.path.exists(csv_path):
        print("No raw_tweets.csv file detected in root folder. Skipping sync.")
        return

    if os.path.exists(json_path):
        with open(json_path, "r") as f:
            database = json.load(f)
    else:
        database = []
        
    existing_ids = {str(t["id"]) for t in database}
    has_updates = False
    
    with open(csv_path, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            tweet_id = str(row.get('id') or row.get('tweet_id') or row.get('post_id')).strip()
            text = row.get('text') or row.get('tweetContent') or row.get('content')
            date = row.get('created_at') or row.get('date') or row.get('timestamp')
            
            # Filter out blank/short noise tweets right here
            if not tweet_id or not text or len(str(text).strip()) < 15:
                continue
                
            if tweet_id not in existing_ids:
                print(f"Categorizing new item: {tweet_id}")
                clean_date = date.split('T')[0] if 'T' in str(date) else str(date)
                category = categorize_tweet(text)
                
                database.append({
                    "id": tweet_id,
                    "text": str(text),
                    "category": category,
                    "date": clean_date
                })
                has_updates = True

    if has_updates:
        with open(json_path, "w") as f:
            json.dump(database, f, indent=2)
        print("Success! Local JSON database has been updated.")
    else:
        print("All entries in the CSV already exist inside the database.")

if __name__ == "__main__":
    main()
