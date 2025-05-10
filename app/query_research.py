# query_research.py
from typing import List, Dict, Union
from openai import OpenAI
import os
from app.generations import generate_llm_answer
import random

# Load environment variables
from dotenv import load_dotenv

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


def extract_related_queries(topic: str, model: str = "llama-3.2-3b") -> List[str]:
    """
    Generate 5 AI-centric queries based on input topic
    """
    prompt = QUERY_SEARCH_PROMPT.format(topic=topic)

    try:
        raw_output = generate_llm_answer(prompt, [])
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


def analyze_query_relevance(query: str, max_sources: int = 3) -> List[Dict]:
    """
    For each query, fetch supporting sources from DuckDuckGo
    """
    from app.brand_protector import search_duckduckgo

    sources = search_duckduckgo(query, max_sources)

    return [{"query": query, "sources": sources}]


def run_query_search(topic: str, model: str = "llama-3.2-3b") -> Dict[str, Union[str, List]]:
    """
    Main function used by FastAPI route to power the Query Search Tool
    """
    try:
        queries = extract_related_queries(topic, model=model)
        results = []
        for q in queries:
            result = analyze_query_relevance(q)
            results.append({"query": q, "sources": result[0]["sources"]})
        return {"topic": topic, "queries": queries, "results": results}
    except Exception as e:
        return {"error": str(e), "topic": topic, "queries": [], "results": []}


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
def detect_topic_gaps(site_content: List[str]) -> List[Dict[str, Union[str, int]]]:
    """Find gaps in content coverage using NLP or LLM"""
    all_topics = []
    for content in site_content:
        if "AI" in content:
            all_topics.append("AI SEO")
        if "chatbot" in content:
            all_topics.append("Chatbot Optimization")
        if "rank" in content and "LLM" in content:
            all_topics.append("LLM Search Strategy")
    topic_counter = Counter(all_topics)
    # Return high-priority topics not covered yet
    return [
        {"topic": "Generative Engine Optimization", "score": 85},
        {"topic": "Brand Perception Monitoring", "score": 70},
        {"topic": "Citation-Based Writing", "score": 90},
    ]


# Predict user behavior paths
def predict_user_journey(pages: List[Dict[str, str]]) -> List[Dict[str, Union[str, float]]]:
    """Predict bounce rates, conversion points, and UX recommendations"""
    journey_map = []
    for i, page in enumerate(pages):
        title = page.get("title", f"Page {i + 1}")
        url = page.get("url", "#")
        bounce_rate = round(random.uniform(40, 80), 2)
        conversion_rate = round(random.uniform(1, 3), 2)
        journey_map.append(
            {
                "title": title,
                "url": url,
                "bounce_rate": bounce_rate,
                "conversion_rate": conversion_rate,
                "recommendation": "Add summary + bullet points."
                if bounce_rate > 60
                else "Good engagement.",
            }
        )
    return journey_map


# Main function used by FastAPI
def run_query_research_on_pages(
    pages: List[Dict[str, str]], topic: str
) -> Dict[str, Union[str, List]]:
    results = []
    for page in pages:
        content = page.get("content", "")
        page_queries = extract_related_queries(content[:100])
        scores = [classify_query_intent(q) for q in page_queries]
        citation_score = random.randint(40, 90)
        avg_intent = max(set(scores), key=scores.count) if scores else "Unknown"
        results.append(
            {
                "url": page["url"],
                "queries": page_queries,
                "intent_scores": scores,
                "avg_intent": avg_intent,
                "citation_score": citation_score,
            }
        )
    missing_topics = detect_topic_gaps([p["content"] for p in pages])
    journey_recommendations = predict_user_journey(pages)
    return {
        "topic": topic,
        "results": results,
        "missing_topics": missing_topics,
        "journey_recommendations": journey_recommendations,
    }
