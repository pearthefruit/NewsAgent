import feedparser
import requests

# RSS Feed URL
rss_url = "http://feeds.feedburner.com/zerohedge/feed"

print(f"Inspecting RSS Feed: {rss_url}")

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

try:
    response = requests.get(rss_url, headers=headers, timeout=10)
    print(f"Status Code: {response.status_code}")
    print(f"Response Content (first 500 chars):\n{response.text[:500]}")
    
    if response.status_code == 200:
        feed = feedparser.parse(response.content)
        print(f"\nFeed Title: {feed.feed.get('title', 'Unknown')}")
        print(f"Number of entries: {len(feed.entries)}")
except Exception as e:
    print(f"Error: {e}")
