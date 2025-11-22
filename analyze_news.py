import sys
import os
import feedparser
import pandas as pd
from datetime import datetime
import time
import re
from bs4 import BeautifulSoup

# Add parent directory to path to import Common modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from Common.scraper import UniversalScraper
from Common.ai_client import AIClient
from prompts import NEWS_ANALYSIS_PROMPT, FINAL_RANKING_PROMPT, COMPANY_RELEVANCE_FILTER_PROMPT

# Configuration
SOURCES_FILE = os.path.join(os.path.dirname(__file__), 'sources.xlsx')
SAVED_ARTICLES_DIR = os.path.join(os.path.dirname(__file__), 'saved_articles')

# Create timestamped folder for this run's outputs
RUN_TIMESTAMP = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
REPORTS_BASE_DIR = os.path.join(os.path.dirname(__file__), 'reports')
CURRENT_RUN_DIR = os.path.join(REPORTS_BASE_DIR, RUN_TIMESTAMP)
ANALYSIS_LOG_FILE = os.path.join(CURRENT_RUN_DIR, 'analysis_log.md')
INVESTMENT_REPORT_FILE = os.path.join(CURRENT_RUN_DIR, 'investment_report.md')

def setup_directories():
    if not os.path.exists(SAVED_ARTICLES_DIR):
        os.makedirs(SAVED_ARTICLES_DIR)
    if not os.path.exists(CURRENT_RUN_DIR):
        os.makedirs(CURRENT_RUN_DIR)
    print(f"📁 Saving this run's reports to: {CURRENT_RUN_DIR}")

def clean_filename(title):
    return re.sub(r'[\\/*?:"<>|]', "", title)[:100]

def clean_html(content):
    if not content:
        return ""
    soup = BeautifulSoup(content, "html.parser")
    return soup.get_text(separator='\n\n', strip=True)

def save_article_to_markdown(title, url, content, date_str):
    filename = f"{date_str}_{clean_filename(title)}.md"
    filepath = os.path.join(SAVED_ARTICLES_DIR, filename)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(f"# {title}\n\n")
        f.write(f"**Source**: {url}\n")
        f.write(f"**Date**: {date_str}\n\n")
        f.write("---\n\n")
        f.write(content)
    
    return filepath

def analyze_article(title, url, content, ai_client):
    print(f"Analyzing: {title}...")
    # Pass model=None to allow AIClient to try its default list (2.0 Flash -> 1.5 Flash)
    analysis = ai_client.analyze_text(content, NEWS_ANALYSIS_PROMPT, model=None)
    return analysis

def update_analysis_log(title, url, analysis):
    with open(ANALYSIS_LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(f"\n\n## Analysis: {title}\n")
        f.write(f"**Source**: {url}\n\n")
        f.write(analysis)
        f.write("\n\n---\n")

def filter_analysis_log_once(ai_client):
    """
    One-time filter of the complete analysis log to remove promotional/incidental company mentions.
    Runs after all articles are analyzed, before generating the final report.
    Uses Gemini 2.0 Flash to identify and remove spurious ticker mentions.
    """
    import re
    
    if not os.path.exists(ANALYSIS_LOG_FILE):
        return
    
    print("\n🔍 Filtering spurious company mentions from analysis log...")
    
    with open(ANALYSIS_LOG_FILE, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Patterns in the REASONING text that indicate irrelevant mentions
    exclusion_patterns = [
        r'support.*via',
        r'support.*on',
        r'subscribe.*via',
        r'promotes.*subsidiary',  # "promotes 'Locals', a Rumble subsidiary"
        r'promotes.*platform',    # "promotes X as a platform"
        r'posted.*on',
        r'shared.*on',
        r'mentioned only as.*platform',
        r'no material impact.*business',
        r'incidental.*mention',
        r'promotional purposes',
        r'medium.*no business',
    ]
    
    lines = content.split('\n')
    filtered_lines = []
    in_explicit_table = False
    companies_filtered = 0
    
    for line in lines:
        # Track when we're in an "Explicitly Mentioned Companies" table
        if "**1. Explicitly Mentioned Companies**" in line:
            in_explicit_table = True
            filtered_lines.append(line)
            continue
        
        # Check if we've left the section
        if in_explicit_table and (line.startswith("**2.") or line.startswith("**3.")):
            in_explicit_table = False
        
        # If in table and it's a data row, check reasoning column
        if in_explicit_table and line.startswith('|') and not line.startswith('| :') and not line.startswith('| Ticker'):
            parts = line.split('|')
            if len(parts) >= 6:
                reasoning = parts[5].lower()  # Reasoning column
                
                # Check if any exclusion pattern matches
                if any(re.search(pattern, reasoning, re.IGNORECASE) for pattern in exclusion_patterns):
                    ticker = parts[1].strip()
                    company = parts[2].strip()
                    print(f"  ✗ Filtered: {ticker} ({company})")
                    companies_filtered += 1
                    continue
        
        filtered_lines.append(line)
    
    if companies_filtered > 0:
        # Save filtered version
        filtered_content = '\n'.join(filtered_lines)
        with open(ANALYSIS_LOG_FILE, 'w', encoding='utf-8') as f:
            f.write(filtered_content)
        print(f"  ✓ Removed {companies_filtered} spurious mention(s)\n")
    else:
        print("  ✓ No spurious mentions found\n")

def generate_final_report(ai_client):
    print("\nGenerating Final Investment Report...")
    if not os.path.exists(ANALYSIS_LOG_FILE):
        print("No analysis log found. Skipping report generation.")
        return

    with open(ANALYSIS_LOG_FILE, 'r', encoding='utf-8') as f:
        aggregated_analysis = f.read()

    if not aggregated_analysis.strip():
        print("Analysis log is empty.")
        return

    # Split into individual analyses
    analyses = aggregated_analysis.split('\n---\n')
    analyses = [a.strip() for a in analyses if a.strip()]
    
    if not analyses:
        print("No analyses found.")
        return
    
    # Batch processing: 5 articles per batch
    batch_size = 5
    intermediate_summaries = []
    
    print(f"Processing {len(analyses)} analyses in batches of {batch_size}...")
    
    for i in range(0, len(analyses), batch_size):
        batch = analyses[i:i+batch_size]
        batch_text = '\n---\n'.join(batch)
        
        print(f"Processing batch {i//batch_size + 1} ({len(batch)} articles)...")
        
        batch_prompt = f"""
You are a senior financial analyst. Summarize the key investment themes and opportunities from the following {len(batch)} news analyses.
Focus on:
1. Most compelling buy/sell opportunities
2. Key sector trends
3. Critical risk factors

Provide a concise summary that retains the most important tickers, recommendations, and reasoning.
"""
        
        summary = ai_client.analyze_text(batch_text, batch_prompt, model='gemini-2.5-pro')
        intermediate_summaries.append(summary)
        print(f"Batch {i//batch_size + 1} complete.")
    
    # Final synthesis
    print("Generating final synthesis...")
    combined_summaries = '\n\n---\n\n'.join(intermediate_summaries)
    final_report = ai_client.analyze_text(combined_summaries, FINAL_RANKING_PROMPT, model='gemini-2.5-pro')
    
    with open(INVESTMENT_REPORT_FILE, 'w', encoding='utf-8') as f:
        f.write(final_report)
    
    print(f"Report saved to {INVESTMENT_REPORT_FILE}")

def process_rss_feed(feed_url, scraper, ai_client):
    print(f"Checking RSS: {feed_url}...")
    feed = feedparser.parse(feed_url)
    
    # Process top 20 entries to get comprehensive coverage
    for entry in feed.entries[:20]:
        title = entry.title
        link = entry.link
        date_str = datetime.now().strftime('%Y-%m-%d')
        
        # Check if already saved/analyzed (simple check by filename existence)
        filename = f"{date_str}_{clean_filename(title)}.md"
        if os.path.exists(os.path.join(SAVED_ARTICLES_DIR, filename)):
            print(f"Skipping (already processed): {title}")
            continue

        # Get Content
        content = None
        if 'content' in entry:
            try:
                content = entry.content[0].value
            except:
                pass
        elif 'summary' in entry:
            content = entry.summary
        
        # If content is short, scrape it
        if not content or len(content) < 500:
            print(f"Fetching full content for: {title}")
            content = scraper.get_text_content(link)
        
        if content:
            # Clean HTML tags if present (especially from RSS feeds)
            content = clean_html(content)
            
            save_article_to_markdown(title, link, content, date_str)
            analysis = analyze_article(title, link, content, ai_client)
            update_analysis_log(title, link, analysis)
            # Sleep to be nice to APIs and avoid rate limits
            print("Sleeping for 10s...")
            time.sleep(10)

def process_homepage(url, name, scraper, ai_client):
    """
    Scrape a homepage for article links and process each article.
    Specifically designed for ZeroHedge but can work for similar sites.
    """
    print(f"Processing homepage: {url} ({name})...")
    
    # Fetch the homepage HTML
    html = scraper.fetch_page(url)
    soup = BeautifulSoup(html, 'html.parser')
    
    # Find all article links using the selectors identified
    selectors = [
        "a[href^='/news/']",
        "a[href^='/geopolitical/']",
        "a[href^='/markets/']",
        "a[href^='/personal-finance/']"
    ]
    
    # Store as dict to avoid duplicates: {url: title}
    articles = {}
    for selector in selectors:
        links = soup.select(selector)
        for link in links:
            href = link.get('href')
            link_text = link.get_text(strip=True)
            if href and link_text:  # Only process if both URL and title exist
                # Convert relative URLs to absolute
                if href.startswith('/'):
                    full_url = f"https://www.zerohedge.com{href}"
                else:
                    full_url = href
                # Store URL as key, title as value (dict automatically handles duplicates)
                if full_url not in articles:
                    articles[full_url] = link_text
    
    print(f"Found {len(articles)} unique articles on homepage.")
    
    # Process each article
    for article_url, article_title in articles.items():
        date_str = datetime.now().strftime('%Y-%m-%d')
        
        # Check if already processed
        filename = f"{date_str}_{clean_filename(article_title)}.md"
        if os.path.exists(os.path.join(SAVED_ARTICLES_DIR, filename)):
            print(f"Skipping (already processed): {article_title}")
            continue
        
        # Scrape the article content
        print(f"Fetching article: {article_title}...")
        content = scraper.get_text_content(article_url)
        
        if content and len(content) > 200:  # Ensure it's substantial content
            # Clean and save using the actual title from the homepage
            content = clean_html(content)
            save_article_to_markdown(article_title, article_url, content, date_str)
            analysis = analyze_article(article_title, article_url, content, ai_client)
            # Filter out irrelevant company mentions
            print("  🔍 Filtering irrelevant companies...")
            filtered_analysis = filter_irrelevant_companies(analysis, ai_client)
            update_analysis_log(article_title, article_url, filtered_analysis)
            
            # Sleep to be nice to servers
            print("Sleeping for 10s...")
            time.sleep(10)
        else:
            print(f"Skipping {article_title} - insufficient content.")

def process_direct_url(url, name, scraper, ai_client):
    print(f"Processing URL: {url} ({name})...")
    # For direct URLs, we usually need to find the latest article or just scrape the page.
    # This is tricky without a specific extractor. 
    # For now, we'll just scrape the page content itself as if it's the "news".
    # A better approach would be to find links on the page, but that's complex.
    # We'll assume the URL points to a specific article or a page with relevant text.
    
    content = scraper.get_text_content(url)
    if content:
        title = f"{name} - {datetime.now().strftime('%H-%M')}"
        date_str = datetime.now().strftime('%Y-%m-%d')
        
        save_article_to_markdown(title, url, content, date_str)
        # Content from scraper is usually already text, but running it through clean_html 
        # ensures consistency and catches any stray tags.
        content = clean_html(content)
        analysis = analyze_article(title, url, content, ai_client)
        # Filter out irrelevant company mentions
        print("  🔍 Filtering irrelevant companies...")
        filtered_analysis = filter_irrelevant_companies(analysis, ai_client)
        update_analysis_log(title, url, filtered_analysis)

def main():
    setup_directories()
    
    # No need to clear the log since each run gets its own timestamped folder

    scraper = UniversalScraper(headless=True)
    ai_client = AIClient(use_case="financial_analysis")

    try:
        if not os.path.exists(SOURCES_FILE):
            print(f"Sources file not found: {SOURCES_FILE}")
            return

        df = pd.read_excel(SOURCES_FILE)
        
        for index, row in df.iterrows():
            if str(row['Enabled']).lower() != 'yes':
                continue
                
            source_type = row['Type'].lower()
            url = row['URL']
            name = row['Name']
            
            if source_type == 'rss':
                process_rss_feed(url, scraper, ai_client)
            elif source_type == 'homepage':
                process_homepage(url, name, scraper, ai_client)
            elif source_type == 'url':
                process_direct_url(url, name, scraper, ai_client)
        
        # Filter spurious company mentions before generating final report
        filter_analysis_log_once(ai_client)
        
        # Final Step
        generate_final_report(ai_client)

    finally:
        scraper.close()

if __name__ == "__main__":
    main()
