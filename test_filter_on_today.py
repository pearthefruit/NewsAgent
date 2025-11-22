import sys
import os

# Setup paths
newsagent_dir = r"c:\Users\peary\OneDrive - The City University of New York\Web Scraping\NewsAgent"
sys.path.append(os.path.dirname(newsagent_dir))
os.chdir(newsagent_dir)

# Import and configure
from Common.ai_client import AIClient
import analyze_news
import shutil

# Backup the original
log_file = r"c:\Users\peary\OneDrive - The City University of New York\Web Scraping\NewsAgent\reports\2025-11-22_12-12-17\analysis_log.md"
backup_file = log_file.replace('.md', '_backup_before_filter.md')
shutil.copy(log_file, backup_file)
print(f"Backed up to: {backup_file}")

# Set the log file path
analyze_news.ANALYSIS_LOG_FILE = log_file

# Run the filter
ai_client = AIClient(use_case="test")
analyze_news.filter_analysis_log_once(ai_client)

print("\n✓ Filter complete! Check the analysis_log.md file.")
