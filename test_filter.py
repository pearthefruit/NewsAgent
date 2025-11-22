import sys
import os

# Fix Windows console encoding for Unicode
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Add parent directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from Common.ai_client import AIClient
from prompts import COMPANY_RELEVANCE_FILTER_PROMPT
import json

def filter_irrelevant_companies(analysis, ai_client):
    """
    Use Gemini 2.0 Flash to filter out irrelevant company mentions from the analysis.
    """
    # Check if there's an "Explicitly Mentioned Companies" section
    if "**1. Explicitly Mentioned Companies**" not in analysis:
        return analysis
    
    try:
        filter_prompt = COMPANY_RELEVANCE_FILTER_PROMPT + f"\n\nAnalysis to review:\n{analysis}"
        response = ai_client.analyze_text(analysis, filter_prompt, model='gemini-2.0-flash-exp')
        
        # Extract JSON from response
        json_str = response.strip()
        if "```json" in json_str:
            json_str = json_str.split("```json")[1].split("```")[0].strip()
        elif "```" in json_str:
            json_str = json_str.split("```")[1].split("```")[0].strip()
        
        # Handle empty responses
        if not json_str or json_str == '[]':
            print(f"  ✓ No companies in explicitly mentioned section")
            return analysis
        
        decisions = json.loads(json_str)
        
        # If no companies to remove, return original
        companies_to_remove = [d['ticker'] for d in decisions if d['decision'] == 'REMOVE']
        if not companies_to_remove:
            print(f"  ✓ All {len(decisions)} companies are relevant")
            return analysis
        
        print(f"  → Removing {len(companies_to_remove)} of {len(decisions)} companies")
        
        # Remove filtered companies from the table
        lines = analysis.split('\n')
        filtered_lines = []
        in_explicit_table = False
        
        for line in lines:
            if "**1. Explicitly Mentioned Companies**" in line:
                in_explicit_table = True
                filtered_lines.append(line)
                continue
            
            if in_explicit_table and line.startswith("**2."):
                in_explicit_table = False
            
            if in_explicit_table and line.startswith('|') and not line.startswith('| :'):
                should_remove = any(ticker in line.split('|')[1:3] for ticker in companies_to_remove)
                if should_remove:
                    company_name = line.split('|')[2].strip() if len(line.split('|')) > 2 else 'company'
                    print(f"  ✗ Filtered out: {company_name}")
                    continue
            
            filtered_lines.append(line)
        
        return '\n'.join(filtered_lines)
        
    except Exception as e:
        print(f"  ⚠️  Filter failed: {e}")
        print(f"      Raw AI response (first 200 chars): {response[:200] if 'response' in locals() else 'N/A'}")
        return analysis

# Main test script
log_file = r"c:\Users\peary\OneDrive - The City University of New York\Web Scraping\NewsAgent\reports\2025-11-22_12-12-17\analysis_log.md"
output_file = r"c:\Users\peary\OneDrive - The City University of New York\Web Scraping\NewsAgent\reports\2025-11-22_12-12-17\analysis_log_filtered.md"

print("Reading analysis log...")
with open(log_file, 'r', encoding='utf-8') as f:
    content = f.read()

# Split by article sections
articles = content.split('\n---\n')
print(f"Found {len(articles)} article sections\n")

ai_client = AIClient(use_case="financial_analysis")
filtered_articles = []

for i, article in enumerate(articles, 1):
    if not article.strip():
        continue
    
    # Extract title for display
    title_line = [line for line in article.split('\n') if line.startswith('## Analysis:')]
    title = title_line[0].replace('## Analysis:', '').strip() if title_line else f"Article {i}"
    
    print(f"\n[{i}/{len(articles)}] {title}")
    filtered = filter_irrelevant_companies(article, ai_client)
    filtered_articles.append(filtered)

# Write filtered version
print(f"\n\nWriting filtered log to: {output_file}")
with open(output_file, 'w', encoding='utf-8') as f:
    f.write('\n---\n'.join(filtered_articles))

print("✓ Done! Compare the files to see what was filtered.")
