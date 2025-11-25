# analyze_news

## Purpose

This module serves as the primary engine for the NewsAgent system. Its core responsibility is to orchestrate the entire financial news analysis workflow. It fetches articles from predefined sources, leverages Large Language Models (LLMs) for in-depth analysis, filters the results for relevance, and compiles the findings into structured, human-readable reports. This automated process transforms raw news data into actionable investment intelligence.

## Key Components

-   **`setup_directories()`**: Initializes the file system for a new analysis run by creating a unique, timestamped directory to store all outputs, ensuring that results from different runs are kept separate.
-   **`analyze_article()`**: Submits the text content of a single news article to the configured AI client (e.g., Gemini or OpenAI). It uses a specialized prompt to extract key information, such as mentioned stock tickers, investment sentiment, and a summary of the news.
-   **`update_analysis_log()`**: Appends the structured analysis of a single article to a cumulative log file (`analysis_log.md`) for the current run. This log serves as the master record of all processed articles.
-   **`filter_irrelevant_companies()`**: An AI-driven, first-pass filter applied to the analysis of each individual article. It uses a targeted prompt to identify and remove company mentions that are incidental or not central to the article's main topic (e.g., a social media platform mentioned as a source).
-   **`filter_analysis_log_once()`**: A rule-based, second-pass filter that runs after all articles have been analyzed. It scans the entire `analysis_log.md` file and removes spurious company mentions based on a predefined set of keywords and patterns (e.g., promotional language, platform mentions), ensuring the final report is clean and focused.

## Data Flow

The module processes data in a sequential pipeline, transforming raw news feeds into a final investment report.

| Step | Function(s) | Input | Output | Artifact(s) |
| :--- | :--- | :--- | :--- | :--- |
| **1. Initialization** | `setup_directories()` | None | A new run directory | `reports/YYYY-MM-DD_HH-MM-SS/` |
| **2. Scrape & Clean** | `UniversalScraper`, `clean_html` | News article URL from `sources.xlsx` | Cleaned article text | Markdown file in `saved_articles/` |
| **3. AI Analysis** | `analyze_article()` | Cleaned article text | Structured analysis text | In-memory text |
| **4. AI Filtering** | `filter_irrelevant_companies()` | Structured analysis text | Refined analysis text | In-memory text |
| **5. Log Aggregation** | `update_analysis_log()` | Refined analysis text | Appended content to the log file | `analysis_log.md` |
| **6. Final Filtering** | `filter_analysis_log_once()` | The complete `analysis_log.md` | A cleansed `analysis_log.md` | Overwrites `analysis_log.md` |
| **7. Report Generation** | (External to module) | The cleansed `analysis_log.md` | Final investment report | `investment_report.md` |

## Dependencies

-   **Internal Modules:**
    -   `Common.scraper.UniversalScraper`: Used to fetch and parse content from web pages and RSS feeds.
    -   `Common.ai_client.AIClient`: Provides a unified interface to interact with different LLM providers (Gemini, OpenAI).
    -   `prompts`: Contains the prompt templates required for AI analysis and filtering tasks.
-   **External Libraries:**
    -   `feedparser`: For parsing RSS/Atom feeds.
    -   `pandas`: For reading the `sources.xlsx` configuration file.
    -   `beautifulsoup4`: For cleaning and parsing HTML content from scraped articles.
    -   `openai`: The client library for interacting with OpenAI models.
-   **Dependents:**
    -   This module is typically executed as a top-level script or called by a main application runner that initiates the news analysis process.

## Configuration

This module relies on several file-based configurations and constants defined at the top of the file.

-   **`SOURCES_FILE`**: Path to `sources.xlsx`, an Excel file containing the list of RSS feeds and websites to be scraped for news.
-   **`SAVED_ARTICLES_DIR`**: The directory where cleaned, raw content of each scraped article is saved as a Markdown file for archival and debugging purposes.
-   **`REPORTS_BASE_DIR`**: The parent directory that contains all timestamped report folders.
-   **`CURRENT_RUN_DIR`**: The specific, timestamped sub-directory where all outputs for the current execution (logs, reports) are stored. This path is generated dynamically at runtime.
-   **`ANALYSIS_LOG_FILE`**: The path to the master Markdown log file for the current run, which aggregates analyses from all processed articles.
-   **`INVESTMENT_REPORT_FILE`**: The path to the final, summarized Markdown report generated at the end of the process.

## Usage Examples

This module is designed to be run as an automated script. The primary entry point will execute the entire data flow from scraping to report generation.

**Typical Execution:**

When the script is run, it performs the following without user intervention:
1.  Creates a new timestamped directory in `reports/`.
2.  Reads the news sources from `sources.xlsx`.
3.  Iterates through each source, scraping, analyzing, and filtering articles.
4.  Logs all analyses to `analysis_log.md` within the run directory.
5.  Performs a final cleanup of the log.
6.  Generates the final `investment_report.md`.

The user's primary interaction is to review the final report file located at: `reports/YYYY-MM-DD_HH-MM-SS/investment_report.md`.

---
## Change History
- **2025-11-24 14:00:03**: Initial documentation created.
