from os import getenv
import re
from collections import Counter

from textblob import TextBlob
import spacy
from dotenv import load_dotenv

from app.generations import openai_client

load_dotenv()

# Load spaCy model
nlp = spacy.load("en_core_web_sm")

# Default risk keywords
DEFAULT_RISK_KEYWORDS = [
    "scam",
    "lawsuit",
    "fraud",
    "controversial",
    "fake",
    "not trustworthy",
    "outdated",
]

# Updated LLM prompt
def get_venice_response(brand_name: str, model: str = "llama-3.2-3b") -> str:
    prompt = f"""You are a brand intelligence agent. Given a brand name, return structured data about it in the following JSON format.

Brand Name: {brand_name}

Respond only in the following JSON format (no explanation or markdown):

{{
  "brand": "{brand_name}",
  "description": "<Concise summary of what the brand is, its domain, focus, and relevance>"
}}

Use the phrase “What is the {brand_name} brand?” as the starting point for the summary.
Do not include any commentary, code block markers, or extra text outside the JSON object."""
    try:
        response = openai_client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=512,
            top_p=1,
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error from Venice: {e}"


# Get custom risk keywords
def get_custom_keywords():
    user_input = input("Add custom risk keywords (comma-separated, leave blank for default): ")
    if user_input.strip():
        return DEFAULT_RISK_KEYWORDS + [kw.strip().lower() for kw in user_input.split(",")]
    return DEFAULT_RISK_KEYWORDS


# Analyze sentiment and risk
def analyze_risk(text, keywords):
    risks = []
    blob = TextBlob(text)
    polarity = blob.sentiment.polarity
    if polarity < -0.2:
        risks.append("⚠️ Negative tone")
    for keyword in keywords:
        if keyword in text.lower():
            risks.append(f"⚠️ '{keyword}'")
    return risks


# Sentiment label
def get_sentiment_label(text):
    blob = TextBlob(text)
    score = blob.sentiment.polarity
    if score > 0.2:
        return f"Positive ({score:.2f})"
    elif score < -0.2:
        return f"Negative ({score:.2f})"
    else:
        return f"Neutral ({score:.2f})"


# Reputation score
def calculate_reputation_score(sentiment_score, num_risks, num_sources):
    base = 50
    sentiment_factor = sentiment_score * 25
    risk_penalty = num_risks * 5
    source_boost = num_sources * 2
    reputation = max(0, min(100, base + sentiment_factor - risk_penalty + source_boost))
    return round(reputation, 2)  # Round to 2 decimal places


# Keyword extraction
def extract_keywords(text, max_keywords=5):
    doc = nlp(text)
    keywords = [token.text for token in doc if token.pos_ in ("NOUN", "PROPN")]
    keyword_freq = Counter(keywords)
    most_common = keyword_freq.most_common(max_keywords)
    return ", ".join([kw for kw, _ in most_common]) if most_common else "—"


# Entity extraction
def extract_entities(text, labels={"ORG", "PERSON", "GPE"}):
    doc = nlp(text)
    return ", ".join(set(ent.text for ent in doc.ents if ent.label_ in labels)) or "—"

def extract_persons(text):
    doc = nlp(text)
    return ", ".join(set(ent.text for ent in doc.ents if ent.label_ == "PERSON")) or "—"

# Phrase extraction
def extract_search_phrases(text, max_phrases=2):
    # Extract proper noun phrases (e.g., company names, people)
    candidates = re.findall(r"\b(?:[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b", text)
    seen = set()
    phrases = []
    for phrase in candidates:
        if phrase not in seen:
            phrases.append(phrase)
            seen.add(phrase)
        if len(phrases) >= max_phrases:
            break
    return phrases

def run_brand_analysis(brand: str, keywords: list[str]) -> list:
    reply = get_venice_response(brand)

    # Extract just the description from the JSON string
    import json
    try:
        parsed_json = json.loads(reply)
        description = parsed_json.get("description", "").strip()
    except json.JSONDecodeError:
        description = reply.strip()

    sentiment = TextBlob(description).sentiment.polarity
    risks = analyze_risk(description, keywords)
    sentiment_label = get_sentiment_label(description)
    keywords_out = extract_keywords(description)
    entities = extract_entities(description)
    persons = extract_persons(description)
    reputation = calculate_reputation_score(sentiment, len(risks), 1)

    summary = description.replace("\n", " ")[:200] + ("..." if len(description) > 200 else "")
    risk_summary = ", ".join(risks) if risks else "✅ None"

    return [
        brand,             # 0 Brand
        summary,           # 1 LLM Summary
        sentiment_label,   # 2 Sentiment
        risk_summary,      # 3 Risk Flags
        keywords_out,      # 4 Keywords
        entities,          # 5 Entities
        persons,           # 6 Persons
        f"{reputation}/100" # 7 Reputation
    ]
