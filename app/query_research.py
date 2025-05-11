from typing import List, Dict, Union
from dotenv import load_dotenv
from openai import OpenAI
import os
from lamini import MemoryRAG

# Resolve project-root relative data path into an absolute path
BASE_DIR = os.path.dirname(os.path.dirname(__file__))  # e.g. project_root/app/.. → project_root
PDF_PATH = os.path.join(BASE_DIR, "data", "pdfs", "visit_london_sample.pdf")

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

# Prompt template for RAG query with citation and scoring
RAG_QUERY_PROMPT = """
<|begin_of_text|><|start_header_id|>user<|end_header_id|>\n\n
You have access to the following indexed documents and websites in your memory store.
Your task is to retrieve and summarize information about the given topic, and for each piece of information:
- Include a citation in the form [source_name] indicating which document or website URL it came from.
- Assign a relevance score (0–100) to each cited source, reflecting how relevant that source is to the topic.
Return a JSON object with two keys:
  "result": a single string summary containing the citations inline,
  "citation_scores": an object mapping source_name to its relevance percentage. \n\n What is {topic}? <|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n
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


# --- Memory RAG Integration Helpers ---


def build_memory_index(pdf_paths: List[str]) -> str:
    """
    Builds a Memory RAG index from a list of PDF file paths.
    Returns the job ID for tracking.
    """
    client = MemoryRAG("meta-llama/Llama-3.1-8B-Instruct")
    response = client.memory_index(documents=pdf_paths)
    job_id = response.get("job_id")
    if not job_id:
        raise RuntimeError("Failed to enqueue memory indexing job")
    return job_id


def query_memory(client, prompt: str) -> str:
    """
    Queries the built Memory RAG index with a prompt.
    Returns the LLM response as text.
    """
    response = client.query(prompt)
    return response.get("text", "")


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


def run_query_research_on_pages(topic: str) -> Dict[str, Union[str, List]]:
    """
    Build a Memory RAG index (if not already built) and query it for the given topic.
    Returns the raw JSON response from the memory RAG.
    """
    client = MemoryRAG(job_id=17860)
    prompt = RAG_QUERY_PROMPT.format(topic=topic)
    response = client.query(prompt)
    raw_outputs = response.get("outputs", [])
    clean_results = []
    for item in raw_outputs:
        text = item.get("output", "")
        # Strip markdown fences
        text = text.strip().replace("```json", "").replace("```", "").strip()
        # Try parsing JSON inside
        try:
            import json

            parsed = json.loads(text)
            clean_results.append(parsed)
        except Exception:
            clean_results.append({"result": text})
    return clean_results
