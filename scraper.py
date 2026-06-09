import json
import os
import csv
import requests
import time

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

CATEGORIES = [
    "Viral Growth Loops",
    "Consumer Psychology",
    "Fundraising & Exits",
    "Satire & Humor",
    "Product Strategy"
]


def categorize_tweet(text):
    """
    Categorize a tweet into exactly one predefined category using OpenAI.
    """
    if not OPENAI_API_KEY:
        raise RuntimeError(
            "OPENAI_API_KEY environment variable is not set."
        )

    url = "https://api.openai.com/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }

    # Restoring structured definitions ensures the nano model retains razor-sharp accuracy
    payload = {
        "model": "gpt-5.4-nano-2026-03-17", # FIXED: Correct official OpenAI model string
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are an expert startup analyst examining tweets by founder Nikita Bier.\n"
                    "Classify the tweet into EXACTLY ONE of the following categories:\n\n"
                    "1. 'Viral Growth Loops': Focused on referral setups, growth hacks, invitations, and acquisition hooks.\n"
                    "2. 'Consumer Psychology': Focused on why users share, social validation, identity, and dopamine loops.\n"
                    "3. 'Fundraising & Exits': Focused on venture capital, selling companies, pitches, valuations, and cap tables.\n"
                    "4. 'Satire & Humor': Sarcastic comments, office memes, traveling observations, or tech jokes without business lessons.\n"
                    "5. 'Product Strategy': Engineering updates, product management, team workflows, features, or design tweaks.\n\n"
                    "Return ONLY the plain category name string. No quotes, periods, or formatting markdown."
                )
            },
            {
                "role": "user",
                "content": text
            }
        ],
        "max_completion_tokens": 10
    }

    try:
        response = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=30
        )

        response.raise_for_status()
        result = response.json()

        category = (
            result["choices"][0]["message"]["content"]
            .strip()
            .replace('"', '')
            .replace("'", "")
            .replace("*", "")
        )

        # Handle trailing periods cleanly if any exist
        if category.endswith('.'):
            category = category[:-1].strip()

        for valid in CATEGORIES:
            if category.lower() == valid.lower():
                return valid

        print(f"Unexpected category returned: '{category}'. Using fallback.")
        return "Product Strategy"

    except requests.exceptions.HTTPError as e:
        print(f"HTTP Error: {response.status_code}")
        print(response.text)
        return "Product Strategy"

    except Exception as e:
        print(f"Classification Error: {e}")
        return "Product Strategy"


def main():
    csv_path = "raw_tweets.csv"
    json_path = "docs/tweets.json"

    if not os.path.exists(csv_path):
        print(f"File not found: {csv_path}")
        return

    os.makedirs("docs", exist_ok=True)

    database = []
    existing_ids = set()

    # FIXED: Load existing records to preserve history and prevent destructive overwriting
    if os.path.exists(json_path):
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                database = json.load(f)
                # Keep tracking strings safely
                existing_ids = {str(t["id"]).strip() for t in database if "id" in t}
        except Exception as e:
            print(f"Notice: Could not parse existing tweets.json, starting fresh. ({e})")
            database = []

    has_new_updates = False

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            tweet_id = str(row.get("id", "")).strip()
            text = str(row.get("text", "")).strip()
            date = str(row.get("date", "")).strip()

            if not tweet_id or tweet_id.lower() == "none" or "E+" in tweet_id:
                continue

            if len(text) < 15:
                continue

            if tweet_id in existing_ids:
                continue

            print(f"Categorizing: {tweet_id}")
            category = categorize_tweet(text)
            print(f" -> {category}")

            # Append new discoveries right to the database array
            database.append(
                {
                    "id": tweet_id,
                    "text": text,
                    "category": category,
                    "date": date
                }
            )
            existing_ids.add(tweet_id)
            has_new_updates = True

            # Rapid-fire optimization for paid API pipelines
            time.sleep(0.15)

    # Only write to disk if there is genuinely fresh material to update
    if has_new_updates:
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(
                database,
                f,
                indent=2,
                ensure_ascii=False
            )
        print(f"\nSuccess!")
        print(f"Database updated. Total repository size: {len(database)} tweets.")
    else:
        print("\nSync Complete. No new unique insights discovered.")


if __name__ == "__main__":
    main()
