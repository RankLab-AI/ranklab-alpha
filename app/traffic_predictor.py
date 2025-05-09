from typing import List, Dict, Union
from collections import Counter
import random
from app.scoring import extract_citations_new
from app.metrics import impression_wordpos_count_simple


# Mock function to simulate related queries from LLM
def extract_related_queries(topic: str, model: str = "llama-3.2-3b") -> List[str]:
    """
    Simulates an LLM that returns AI-centric questions about a topic.
    Replace this with real LLM logic later.
    """
    mock_query_map = {
        "AI SEO": [
            "What is AI SEO?",
            "How does AI affect traditional SEO?",
            "Will AI replace SEO specialists?",
            "Best practices for optimizing content for ChatGPT",
            "How to rank in Perplexity AI"
        ],
        "Generative Engine Optimization": [
            "What is Generative Engine Optimization?",
            "How to optimize content for LLM search engines",
            "Difference between GEO and SEO",
            "How to write for AI assistants like Gemini",
            "Why should I care about AI-powered search?"
        ],
        "RankLab AI": [
            "What is RankLab AI?",
            "How does RankLab help with AI-readiness?",
            "Is RankLab better than SurferSEO for AI?",
            "Can I integrate RankLab with WordPress?",
            "Does RankLab offer API access?"
        ]
    }

    if topic in mock_query_map:
        return mock_query_map[topic]

    # Default fallback
    return [
        f"What is {topic}?",
        f"How does {topic} work?",
        f"Why should I use {topic}?",
        f"Best practices for {topic}",
        f"{topic} vs alternatives"
    ]


# Simulate citation score generation
def calculate_citation_scores(content: str) -> List[float]:
    """Uses metrics from metrics.py to generate citation likelihood scores"""
    try:
        parsed = extract_citations_new(content)
        n = 5
        scores = [round(score * 100, 2) for score in impression_wordpos_count_simple(parsed, n)]
        return scores
    except Exception as e:
        print(f"[!] Error calculating scores: {e}")
        return [random.randint(60, 90) for _ in range(5)]


# Simulate source distribution (who gets cited most?)
def get_source_distribution(topic: str) -> Dict[str, int]:
    """Returns mock source distribution data for pie chart"""
    mock_sources = {
        "AI SEO": {
            "ai-search.org": 40,
            "chatgpt-insights.blog": 30,
            "seo-journal.com": 20,
            "futureofwork.ai": 10
        },
        "Generative Engine Optimization": {
            "geoseo.org": 50,
            "ranklab.ai": 30,
            "ai-content-hub.io": 15,
            "chatbotweekly.net": 5
        },
        "RankLab AI": {
            "ranklab.ai": 70,
            "chatgpt-insights.blog": 15,
            "seo-journal.com": 10,
            "ai-reviewhub.org": 5
        }
    }

    if topic in mock_sources:
        return mock_sources[topic]

    # Fallback default sources
    return {
        "Source A": 45,
        "Source B": 30,
        "Source C": 15,
        "Source D": 10
    }


# Main predictor function used by FastAPI route
def predict_llm_traffic(content: str, topic: str, num_queries: int = 5) -> Dict[str, Union[str, int, float, List]]:
    """
    Predicts how much AI-driven traffic a piece of content could receive
    Returns structured data for visualization in Jinja2 template
    """
    # Step 1: Extract related queries based on topic
    queries = extract_related_queries(topic, model="llama-3.2-3b")

    # Step 2: Use content citations to estimate visibility
    scores = calculate_citation_scores(content)

    # Step 3: Get source distribution (for pie chart)
    source_distribution = get_source_distribution(topic)

    # Step 4: Estimate total citations
    estimated_monthly_citations = sum(scores)

    # Step 5: Find top query
    top_query_index = scores.index(max(scores)) if scores else 0
    top_query = queries[top_query_index] if top_query_index < len(queries) else "N/A"

    # Return structured data for frontend
    return {
        "topic": topic,
        "queries": queries[:num_queries],
        "scores": scores[:num_queries],
        "source_labels": list(source_distribution.keys()),
        "source_values": list(source_distribution.values()),
        "visibility_trend": generate_mock_trend(scores),
        "estimated_monthly_citations": estimated_monthly_citations,
        "top_query": top_query
    }


# Helper: Generate mock trend data for line graph
def generate_mock_trend(scores: List[float]) -> List[int]:
    base_score = sum(scores)
    trend_data = [
        int(base_score * 0.6),
        int(base_score * 0.8),
        int(base_score * 0.95),
        int(base_score * 1.0)
    ]
    return trend_data


# Helper: Wrap scoring logic
def calculate_citation_scores(content: str) -> List[float]:
    """Wrapper to extract citation-based scores using metrics"""
    try:
        parsed = extract_citations_new(content)
        n = 5
        raw_scores = impression_wordpos_count_simple(parsed, n=n)
        scaled_scores = [round(s * 100, 2) for s in raw_scores]
        return scaled_scores
    except Exception as e:
        print(f"[!] Error calculating citation scores: {e}")
        return [random.uniform(50, 90) for _ in range(5)]