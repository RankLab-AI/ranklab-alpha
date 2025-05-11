from typing import List, Dict, Union
from dotenv import load_dotenv
from openai import OpenAI
import os

load_dotenv()

client = OpenAI(
    api_key=os.getenv("VENICE_API_KEY"),
    base_url=os.getenv("LLM_BASE_URL", "https://api.venice.ai/api/v1"),
)

# Prompt template to find related queries
QUERY_SEARCH_PROMPT = """
You are an expert in understanding how large language models (LLMs) process information.
Your task is to return a list of questions that users commonly ask about the following topic:

Topic: {topic}

Return exactly 5 distinct questions that:
- Are likely to be asked in AI chatbots like ChatGPT or Gemini
- Can be answered using factual data
- Represent common user intents (informational, comparative, instructional)

Format as JSON array:
["question 1", "question 2", ...]
"""

# Prompt template to find missing topics
TOPIC_COV_PROMPT = """
You are an expert in content analysis.
Given the following existing topics and questions that are covered, identify 5 important related topics or subtopics that are missing
and would add value. For each, provide a relevance score out of 100.

Covered items:
{topics}

Output as a JSON array of objects:
[
  {{ "topic": "Topic A", "score": 80 }},
  {{ "topic": "Topic B", "score": 75 }},
  ...
]
"""


def extract_related_queries(topic: str) -> List[str]:
    """
    Generate 5 AI-centric queries based on input topic
    """
    prompt = QUERY_SEARCH_PROMPT.format(topic=topic)

    try:
        from app.generations import generate_venice_response

        raw_output = generate_venice_response(prompt)
        # Try to parse JSON
        if isinstance(raw_output, list):
            return raw_output[:5]
        elif isinstance(raw_output, str):
            # Remove any markdown formatting
            clean_output = raw_output.strip().replace("```json", "").replace("```", "")
            return eval(clean_output)[:5]
        else:
            raise ValueError("Unexpected output format from LLM")
    except Exception as e:
        print(f"Error extracting queries: {e}")
        # Fallback to defaults
        return [
            f"How do I start a blog?",
            f"What are the best tools for blogging?",
            f"Step-by-step guide to blogging",
            f"Why should I start a blog?",
            f"Blog vs website – what's the difference?",
        ]


# Classify query intent
def classify_query_intent(query: str) -> str:
    info_keywords = ["what", "how", "why", "explain"]
    nav_keywords = ["where", "contact", "login", "support"]
    trans_keywords = ["buy", "price", "order", "download"]
    query = query.lower()
    if any(word in query for word in info_keywords):
        return "Informational"
    elif any(word in query for word in nav_keywords):
        return "Navigational"
    elif any(word in query for word in trans_keywords):
        return "Transactional"
    else:
        return "Unknown"


# Detect missing topics
def detect_topic_gaps(topics: List[str]) -> List[Dict[str, Union[str, int]]]:
    """
    Use an LLM to find topics not covered by the provided content.
    Returns a list of dicts with 'topic' and 'score'.
    """
    from app.generations import generate_venice_response

    try:
        # format topics as markdown unordered list
        topics_md = "\n".join(f"- {t}" for t in topics)
        raw = generate_venice_response(TOPIC_COV_PROMPT.format(topics=topics_md))
        # Clean markdown if needed
        if isinstance(raw, str):
            cleaned = raw.strip().replace("```json", "").replace("```", "")
            return eval(cleaned)
        elif isinstance(raw, list):
            return raw
    except Exception as e:
        print(f"Error detecting topic gaps: {e}")

    # Fallback static topics
    return [
        {"topic": "Generative Engine Optimization", "score": 85},
        {"topic": "Brand Perception Monitoring", "score": 70},
        {"topic": "Citation-Based Writing", "score": 90},
    ]


# Main function used by FastAPI
def run_query_research_on_topic(topic: str, source_count: int = 5) -> Dict[str, Union[str, List]]:
    """
    Simplified: generate related queries and intents based on the single topic.
    """
    # Generate 5 related queries for the topic
    queries = extract_related_queries(topic)

    # Classify each query's intent
    intent_labels = [classify_query_intent(q) for q in queries]

    # Determine average intent (most frequent)
    avg_intent = max(set(intent_labels), key=intent_labels.count) if intent_labels else "Unknown"

    # Placeholder citation score (zero for now)
    citation_scores = [0 for _ in queries]

    # Detect topic gaps using the topic as content
    missing_topics = detect_topic_gaps([topic])

    return {
        "topic": topic,
        "queries": queries,
        "intent_labels": intent_labels,
        "avg_intent": avg_intent,
        "citation_scores": citation_scores,
        "missing_topics": missing_topics,
    }
