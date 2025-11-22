import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from Common.ai_client import AIClient
from prompts import COMPANY_RELEVANCE_FILTER_PROMPT

# Test with one of the problematic examples you mentioned
test_analysis = """
**1. Explicitly Mentioned Companies**

| Ticker | Company | Sentiment | Recommendation | Reasoning |
| :--- | :--- | :--- | :--- | :--- |
| SPOT | Spotify Technology S.A. | NEUTRAL | HOLD | The article highlights the cultural relevance and massive reach of Joe Rogan. |
| RUM | Rumble Inc. | BULLISH | BUY | The article explicitly directs readers to support the publisher via 'Locals', a subsidiary of Rumble. |

**2. Implicitly Affected Companies (Second-Order)**
...
"""

ai_client = AIClient(use_case="financial_analysis")
print("Testing filter with sample analysis...\n")

filter_prompt = COMPANY_RELEVANCE_FILTER_PROMPT + f"\n\nAnalysis to review:\n{test_analysis}"
response = ai_client.analyze_text(test_analysis, filter_prompt, model='gemini-2.0-flash-exp')

print("=== RAW AI RESPONSE ===")
print(response)
print("\n=== END RESPONSE ===\n")

# Try to parse it
import json
try:
    json_str = response.strip()
    if "```json" in json_str:
        json_str = json_str.split("```json")[1].split("```")[0].strip()
    elif "```" in json_str:
        json_str = json_str.split("```")[1].split("```")[0].strip()
    
    decisions = json.loads(json_str)
    print(f"SUCCESS! Parsed {len(decisions)} decisions:")
    for d in decisions:
        print(f"  {d['ticker']}: {d['decision']} - {d['reason'][:50]}...")
except Exception as e:
    print(f"FAILED to parse: {e}")
    print(f"Attempted to parse: {json_str[:200]}")
