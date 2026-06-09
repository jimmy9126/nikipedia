import json
import os
import csv
import requests
import time

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

def categorize_tweet(text):
    if not OPENAI_API_KEY:
        print("CRITICAL: OPENAI_API_KEY environment variable is missing!")
        return "Product Strategy"
    
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENAI_API_KEY}"
    }
    
    payload = {
        "model": "gpt-5.4-nano", # Swapped to the ultra-efficient high-volume classification model
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are an elite startup advisor analyzing tweets by builder and growth expert Nikita Bier. "
                    "Your sole task is to classify the provided tweet into exactly ONE of these 5 categories:\n\n"
                    "1. 'Viral Growth Loops': Content focused on viral mechanics, invitation systems, referral loops, acquisition tactics, retention hooks, app store optimization (ASO), or engineering high-growth features.\n"
                    "2. 'Consumer Psychology': Insights regarding why users share things, identity construction, social validation dynamics, teenager/gen-z behavior trends, onboarding dopamine triggers, and human motivations behind app use.\n"
                    "3. 'Fundraising & Exits': Content detailing venture capital relations, valuations, startup pitch decks, investor psychology, acquisition negotiations, cap tables, and startup economics.\n"
                    "4. 'Satire & Humor': Sarcastic text, tech industry memes, self-deprecating jokes, office humor, cultural observations about traveling, and shitposting that lacks concrete business lessons.\n"
                    "5. 'Product Strategy': Frameworks concerning feature prioritization, engineering updates, internal team velocity, design adjustments, analytics features, shipping code, infrastructure performance, or general product management methodologies.\n\n"
                    "CRITICAL: Output ONLY the exact category title string. Do not include quotes, preamble, extra words, periods, or markdown blocks."
                )
            },
            {
                "role": "user",
                "content": f"Tweet to analyze: \"{text}\""
            }
        ],
        "temperature": 0.0 # Strict determinism for precise labels
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        res_json = response.json()
        
        if "error" in res_json:
            print(f"OpenAI API Error: {res_json['error']['message']}")
            return "Product Strategy"
            
        category = res_json['choices'][0]['message']['content'].strip()
        
        # Clean response string aggressively of trailing artifacts
        category = category.replace("*", "").replace("`", "").replace('"', '').replace("'", "").strip()
        if category.endswith('.'):
            category = category[:-1].strip()
            
        valid_categories = ['Viral Growth Loops', 'Product Strategy', 'Consumer Psychology', 'Fundraising & Exits', 'Satire & Humor']
        
        if category in valid_categories:
            return category
        else:
            for valid in valid_categories:
                if valid.lower() == category.lower():
                    return valid
            print(f"DEBUG: Model returned unexpected variant string: '{category}'")
            return "Product Strategy"
    except Exception as e:
        print(f"Network error during API connection: {e}")
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
                print(f"Categorizing item ID: {tweet_id}")
                category = categorize_tweet(text)
                print(f"-> Result: {category}")
                
                database.append({
                    "id": tweet_id,
                    "text": str(text),
                    "category": category,
                    "date": str(date)
                })
                existing_ids.add(tweet_id)
                time.sleep(0.1) # Fast execution execution cadence

    with open(json_path, "w", encoding='utf-8') as f:
        json.dump(database, f, indent=2, ensure_ascii=False)
    print(f"Success! Compiled {len(database)} valid insights into NikiPedia.")

if __name__ == "__main__":
    main()
