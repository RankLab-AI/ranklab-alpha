from os import getenv
import requests
import re
from collections import Counter

from textblob import TextBlob
import spacy
from bs4 import BeautifulSoup
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


def get_venice_response(brand_name: str, model: str = "llama-3.2-3b") -> str:
    try:
        response = openai_client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": f"What is {brand_name}?"}],
            temperature=0.7,
            max_tokens=1024,
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


# DuckDuckGo search
def search_duckduckgo(query, max_results=3):
    url = "https://lite.duckduckgo.com/lite/"
    params = {"q": query}
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        res = requests.get(url, params=params, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")
        links = []
        for a in soup.find_all("a", href=True):
            if a.text and a["href"].startswith("http"):
                links.append(a["href"])
            if len(links) >= max_results:
                break
        return links
    except Exception as e:
        return [f"Search error: {e}"]


# Source-checking
def get_sources(text):
    phrases = extract_search_phrases(text)
    sources = []
    for phrase in phrases:
        search_results = search_duckduckgo(phrase)
        if search_results:
            sources.append(f'Search for "{phrase}":\n  - ' + "\n  - ".join(search_results))
        else:
            sources.append(f'No search results found for "{phrase}"')
    return sources


# GNews search (demo key)
def fetch_news_newsdata(query, max_articles=3):
    api_key = getenv("NEWSDATA_API_KEY")
    url = f"https://newsdata.io/api/1/news?apikey={api_key}&q={query}&language=en"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            return [article["link"] for article in data.get("results", [])[:max_articles]]
        else:
            return [f"News error: {response.status_code}"]
    except Exception as e:
        return [f"News fetch error: {e}"]


def run_brand_analysis(brand: str, keywords: list[str]) -> list:
    reply = get_venice_response(brand)
    sentiment = TextBlob(reply).sentiment.polarity
    risks = analyze_risk(reply, keywords)
    sentiment_label = get_sentiment_label(reply)
    keywords_out = extract_keywords(reply)
    entities = extract_entities(reply)
    sources = get_sources(reply)
    news_links = fetch_news_newsdata(brand)
    reputation = calculate_reputation_score(sentiment, len(risks), len(sources))

    summary = reply.strip().replace("\n", " ")[:200] + ("..." if len(reply) > 200 else "")
    risk_summary = ", ".join(risks) if risks else "✅ None"

    sources_filtered = [s for s in sources if "http" in s]
    news_filtered = [n for n in news_links if n.startswith("http")]

    has_sources = bool(sources_filtered)
    has_news = bool(news_filtered)

    sources_summary = "\n".join(sources_filtered)
    news_summary = "\n".join(news_filtered)

    return [
        brand,  # 0
        summary,  # 1
        sentiment_label,  # 2
        risk_summary,  # 3
        keywords_out,  # 4
        entities,  # 5
        f"{reputation}/100",  # 6
        sources_summary,  # 7
        news_summary,  # 8
        has_sources,  # 9
        has_news,  # 10
    ]
