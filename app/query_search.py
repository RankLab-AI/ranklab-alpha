from typing import List, Dict
from openai import OpenAI
import os
import re
from app.utils import get_prompt
from app.generations import generate_llm_answer

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

client = OpenAI(
    api_key=os.getenv("VENICE_API_KEY"),
    base_url=os.getenv("LLM_BASE_URL", "https://api.venice.ai/api/v1")
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
            f"Blog vs website – what's the difference?"
        ]


def analyze_query_relevance(query: str, max_sources: int = 3) -> List[Dict]:
    """
    For each query, fetch supporting sources from DuckDuckGo
    """
    from app.brand_protector import search_duckduckgo
    
    sources = search_duckduckgo(query, max_sources)
    
    return [{
        "query": query,
        "sources": sources
    }]


def run_query_search(topic: str, model: str = "llama-3.2-3b") -> Dict[str, Union[str, List]]:
    """
    Main function used by FastAPI route to power the Query Search Tool
    """
    try:
        queries = extract_related_queries(topic, model=model)
        results = []
        for q in queries:
            result = analyze_query_relevance(q)
            results.append({
                "query": q,
                "sources": result[0]["sources"]
            })
        return {
            "topic": topic,
            "queries": queries,
            "results": results
        }
    except Exception as e:
        return {
            "error": str(e),
            "topic": topic,
            "queries": [],
            "results": []
        }
