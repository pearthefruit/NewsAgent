import pandas as pd
import os

file_path = r"c:\Users\peary\OneDrive - The City University of New York\Web Scraping\NewsAgent\sources.xlsx"

# Define the new list of sources
data = [
    {"Type": "rss", "URL": "https://www.reddit.com/r/finance/.rss", "Name": "Reddit Finance", "Enabled": "yes"},
    {"Type": "rss", "URL": "http://feeds.feedburner.com/zerohedge/feed", "Name": "ZeroHedge", "Enabled": "yes"},
    {"Type": "rss", "URL": "https://seekingalpha.com/feed.xml", "Name": "Seeking Alpha", "Enabled": "yes"},
    {"Type": "rss", "URL": "https://www.reddit.com/r/stocks/.rss", "Name": "Reddit Stocks", "Enabled": "yes"}
]

df = pd.DataFrame(data)
df.to_excel(file_path, index=False)
print(f"Updated {file_path} with ZeroHedge (removed FT)")
