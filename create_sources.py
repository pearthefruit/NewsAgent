import pandas as pd
import os

file_path = r"c:\Users\peary\OneDrive - The City University of New York\Web Scraping\NewsAgent\sources.xlsx"

data = [
    {"Type": "rss", "URL": "https://feeds.reuters.com/reuters/businessNews", "Name": "Reuters Business", "Enabled": "yes"},
    {"Type": "url", "URL": "https://www.cnbc.com/world/?region=world", "Name": "CNBC World", "Enabled": "yes"},
    {"Type": "rss", "URL": "https://seekingalpha.com/feed.xml", "Name": "Seeking Alpha", "Enabled": "yes"}
]

df = pd.DataFrame(data)
df.to_excel(file_path, index=False)
print(f"Created {file_path}")
