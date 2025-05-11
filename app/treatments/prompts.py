# treatments/prompts.py

QUOTATION_PROMPT = """
You are an expert editor improving web content for AI visibility.

Retain any existing citation markers (e.g., [1], [2], etc.) present in the content wherever possible.

Take the following content and enhance it by inserting at least one direct quotation
from a reliable source (e.g., a report, article, or expert opinion).
Use a citation format like [1], [2], etc. to clearly attribute the quote.

The quotation should reinforce a key claim or insight in the content, and appear prominently.

Content:
\"\"\"
{content}
\"\"\"
Enhanced with Quotation:
"""

STATS_PROMPT = """
You are a content strategist optimizing copy for credibility and AI ranking.

Retain any existing citation markers (e.g., [1], [2], etc.) present in the content wherever possible.

Improve the following content by inserting at least one impactful statistic or data point
from a credible source. Use citation format like [1], [2] to attribute it.

The stat should support a major point or argument and help increase trust and visibility.

Content:
\"\"\"
{content}
\"\"\"
Enhanced with Statistic:
"""

FLUENCY_PROMPT = """
You are a language model specializing in fluency and natural language rewriting.

Rewrite the following content to improve sentence structure, clarity, and flow,
while keeping the original meaning unchanged. Maintain a professional and engaging tone.

Do not add citations or quotes — focus only on rewriting for better fluency.

However, preserve any existing citation markers (e.g., [1], [2], etc.) if they appear in the original content.

Content:
\"\"\"
{content}
\"\"\"
Fluency-Optimized Version:
"""

KEYWORD_STUFFING_PROMPT = """
Here is the source content that you need to update:
\"\"\"
{content}
\"\"\"

## Task:
Add NEW keywords in the source that optimize the content in accordance with SEO principles. These keywords must not already be in the text.

## Guidelines:
1. Identify 5–10 relevant SEO keywords to insert.
2. Keywords should be naturally embedded in existing sentences.
3. Preserve sentence structure and original meaning.
4. Do not remove or reorder content.
5. Output only the updated content in triple backticks.
6. Retain all existing citation markers (e.g., [1], [2], etc.) in the output where they appear.

Updated Output:
<updated text>
"""
