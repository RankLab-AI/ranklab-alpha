import os
import requests
import re
from dotenv import load_dotenv
from textblob import TextBlob
from tabulate import tabulate
from collections import Counter
import spacy
from bs4 import BeautifulSoup

# Load spaCy model
nlp = spacy.load("en_core_web_sm")

# Load API key
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

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


# GROQ API call
def get_groq_response(brand_name, model="llama3-70b-8192"):
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": f"What is {brand_name}?"}],
        "temperature": 0.7,
    }
    try:
        response = requests.post(GROQ_API_URL, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"Error from GROQ API: {e}"


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
    sentences = re.findall(r"([A-Z][^\.!?]{20,200}[\.!?])", text)
    return sentences[:max_phrases]


# DuckDuckGo search
def search_duckduckgo(query, max_results=3):
    url = "https://html.duckduckgo.com/html/"
    params = {"q": query}
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        res = requests.get(url, params=params, headers=headers)
        soup = BeautifulSoup(res.text, "html.parser")
        links = []
        for a in soup.find_all("a", class_="result__a", href=True):
            href = a["href"]
            if href.startswith("http"):
                links.append(href)
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
    api_key = os.getenv("NEWSDATA_API_KEY")
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


# Main
if __name__ == "__main__":
    print("=== Brand Protection: LLM Comparison Tool ===\n")
    main_brand = input("Enter your brand: ")
    competitors = input("Enter competitors (comma-separated): ").split(",")
    custom_risk_keywords = get_custom_keywords()

    brands = [main_brand.strip()] + [c.strip() for c in competitors]
    results = []

    for brand in brands:
        print(f"\n🔍 Querying GROQ for: {brand}...")
        reply = get_groq_response(brand)
        sentiment = TextBlob(reply).sentiment.polarity
        risks = analyze_risk(reply, custom_risk_keywords)
        sentiment_label = get_sentiment_label(reply)
        keywords = extract_keywords(reply)
        entities = extract_entities(reply)
        sources = get_sources(reply)
        news_links = fetch_news_newsdata(brand)
        reputation = calculate_reputation_score(sentiment, len(risks), len(sources))

        summary = reply.strip().replace("\n", " ")[:200] + ("..." if len(reply) > 200 else "")
        risk_summary = ", ".join(risks) if risks else "✅ None"
        sources_summary = "\n".join(sources) if sources else "No sources found."
        news_summary = "\n".join(news_links) if news_links else "No news found."

        results.append(
            [
                brand,
                summary,
                sentiment_label,
                risk_summary,
                keywords,
                entities,
                f"{reputation}/100",
                sources_summary,
                news_summary,
            ]
        )

    print("\n=== Brand Summary Comparison ===\n")
    print(
        tabulate(
            results,
            headers=[
                "Brand",
                "LLM Summary",
                "Sentiment",
                "Risk Flags",
                "Keywords",
                "Entities",
                "Reputation",
                "Sources",
                "News",
            ],
            tablefmt="grid",
        )
    )
