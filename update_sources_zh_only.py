import pandas as pd
import os

file_path = r"c:\Users\peary\OneDrive - The City University of New York\Web Scraping\NewsAgent\sources.xlsx"

# Only ZeroHedge enabled, others commented out via "no" in Enabled column
data = [
    {"Type": "homepage", "URL": "https://www.zerohedge.com/", "Name": "ZeroHedge", "Enabled": "yes"},
    {"Type": "rss", "URL": "https://www.reddit.com/r/finance/.rss", "Name": "Reddit Finance", "Enabled": "no"},
    {"Type": "rss", "URL": "https://seekingalpha.com/feed.xml", "Name": "Seeking Alpha", "Enabled": "no"},
    {"Type": "rss", "URL": "https://www.reddit.com/r/stocks/.rss", "Name": "Reddit Stocks", "Enabled": "no"}
]

df = pd.DataFrame(data)
df.to_excel(file_path, index=False)

