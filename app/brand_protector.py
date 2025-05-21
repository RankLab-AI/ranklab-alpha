import os
import json
import requests
import logging
import time
from dotenv import load_dotenv
from typing import List
import matplotlib.pyplot as plt
import groq

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"


logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
)


def get_groq_response(brand_name, model="llama3-70b-8192"):
    if not GROQ_API_KEY:
        raise EnvironmentError("❌ GROQ_API_KEY is not set in your .env file.")

    prompt = f"""
You are an expert branding analyst. Analyze the brand "{brand_name}" and return the results in this exact JSON format:

{{
  "brand": "{brand_name}",
  "description": "What is the {brand_name} brand?",
  "offerings": "What does {brand_name} offer?",
  "criticisms": "What are common criticisms of {brand_name}?",
  "alternatives": "What are alternatives to {brand_name}?"
}}
Only respond with the JSON.
"""

    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.7,
    }

    response = requests.post(GROQ_API_URL, headers=headers, json=payload)

    try:
        response.raise_for_status()
        resp_json = response.json()
        content = resp_json.get("choices", [{}])[0].get("message", {}).get("content", "").strip()

        if not content:
            raise ValueError("Empty content received from LLM")

        return json.loads(content)

    except (json.JSONDecodeError, ValueError) as e:
        return {
            "brand": brand_name,
            "description": f"⚠️ Error: {str(e)}",
            "offerings": "⚠️",
            "criticisms": "⚠️",
            "alternatives": "⚠️",
        }


def extract_keywords(text):
    return list(set(word.strip(".,!?").lower() for word in text.split() if len(word) > 4))


def summarize_brand(brand_data):
    description = brand_data.get("description", "")
    keywords = extract_keywords(description)
    return {
        "brand": brand_data.get("brand"),
        "summary": description,
        "keywords": ", ".join(keywords),
        "offerings": brand_data.get("offerings", "⚠️"),
        "criticisms": brand_data.get("criticisms", "⚠️"),
        "alternatives": brand_data.get("alternatives", "⚠️"),
    }


def generate_html_table(brands_info):
    """
    Generate an HTML table representation of brand summary comparison.
    """
    headers = ["Brand", "Summary", "Keywords", "Offerings", "Criticisms", "Alternatives"]
    html = ['<table class="collapse ba br2 b--black-10 w-100"><thead><tr>']
    for h in headers:
        html.append(f'<th class="pv2 ph3 tl f6 fw6 ttu">{h}</th>')
    html.append('</tr></thead><tbody class="lh-copy">')
    for info in brands_info:
        html.append("<tr>")
        html.append(f'<td class="pv2 ph3">{info["brand"]}</td>')
        html.append(f'<td class="pv2 ph3">{info["summary"]}</td>')
        html.append(f'<td class="pv2 ph3">{info["keywords"]}</td>')
        html.append(f'<td class="pv2 ph3">{info["offerings"]}</td>')
        html.append(f'<td class="pv2 ph3">{info["criticisms"]}</td>')
        html.append(f'<td class="pv2 ph3">{info["alternatives"]}</td>')
        html.append("</tr>")
    html.append("</tbody></table>")
    return "".join(html)


def run_brand_analysis(
    brand: str,
    competitors: List[str],
    agents: List[str] = None,
    allow_paths: List[str] = None,
    disallow_paths: List[str] = None,
    cite_as: str = "",
    policy: str = "",
):
    logging.debug("[bold green]=== BrandGuard: LLM Insight Tool ===[/bold green]\n")

    # Normalize competitors input to a list
    if isinstance(competitors, str):
        comp_list = [c.strip() for c in competitors.split(",") if c.strip()]
    else:
        comp_list = [c.strip() for c in competitors if isinstance(c, str) and c.strip()]

    # Build combined list and remove duplicates, preserving order
    combined = [brand] + comp_list
    seen = set()
    all_brands = []
    for b in combined:
        if b not in seen:
            all_brands.append(b)
            seen.add(b)
    # default empty lists if not provided
    agents = agents or []
    allow_paths = allow_paths or []
    disallow_paths = disallow_paths or []
    all_infos = []

    for b in all_brands:
        print(f"\n🔍 Querying GROQ for: [yellow]{b}[/yellow]...\n")
        result = get_groq_response(b)
        brand_info = summarize_brand(result)
        all_infos.append(brand_info)
        time.sleep(2)

    logging.debug("\n[bold green]=== Brand Summary Comparison ===[/bold green]\n")
    res_table = generate_html_table(all_infos)
    llm_txt = generate_llm_txt(agents, allow_paths, disallow_paths, cite_as, policy)

    return res_table, llm_txt


def generate_llm_txt(
    agents: List[str],
    allow_paths: List[str],
    disallow_paths: List[str],
    cite_as: str,
    policy: str,
) -> str:
    if not agents and not allow_paths and not disallow_paths and not cite_as:
        return None
    # original LLM-generation logic here, which produces `txt_blocks` as a list
    llm_txt = ""
    for agent in agents:
        llm_txt += f"User-agent: {agent.strip()}\n"
    for path in allow_paths:
        llm_txt += f"Allow: {path.strip()}\n"
    for path in disallow_paths:
        llm_txt += f"Disallow: {path.strip()}\n"
    if cite_as:
        llm_txt += f"Cite-as: {cite_as}\n"
    if policy:
        llm_txt += f"Policy: {policy}\n"
    llm_txt += "\n"
    return llm_txt

# Bubble Chart Function
def run_brand_comparison_chart():
    brands = input("🔠 Paste your comma-separated brand names: ").split(",")
    brands = [b.strip() for b in brands if b.strip()]

    topics = input("🔍 Enter 1–2 topics you'd like to compare brands on (comma-separated): ").split(",")
    topics = [t.strip() for t in topics if t.strip()]
    print(f"\n✨ Analyzing brands: {brands}")
    print(f"📊 Topics: {topics}")

    prompts = {
        topic: f"List the top 10 brands for {topic}. Just give a clean list."
        for topic in topics
    }

    def ask_groq(prompt):
        response = groq_client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        return response.choices[0].message.content

    scores = {brand: {topic: 0 for topic in topics} for brand in brands}

    for topic, prompt in prompts.items():
        print(f"\n🔍 Asking about: {topic}")
        reply = ask_groq(prompt)
        print(reply)

        lines = reply.strip().split("\n")
        for i, line in enumerate(lines[:10]):
            for brand in brands:
                if brand.lower() in line.lower():
                    rank_score = 10 - i
                    scores[brand][topic] += rank_score

        for brand in brands:
            if brand.lower() in reply.lower() and all(brand.lower() not in l.lower() for l in lines[:10]):
                scores[brand][topic] += 0.5

    x = []
    y = []
    sizes = []
    labels = []
    colors = ['#ff5733' if brand.lower() == "ranklab ai" else '#00bfff' for brand in brands]

    topic1, topic2 = topics[0], topics[1] if len(topics) > 1 else topics[0]

    for brand in brands:
        x.append(scores[brand][topic1])
        y.append(scores[brand][topic2])
        sizes.append((x[-1] + y[-1]) * 30 + 100)
        labels.append(brand)

    plt.figure(figsize=(10, 6))
    plt.scatter(x, y, s=sizes, c=colors, alpha=0.7, edgecolors='k')
    for i, label in enumerate(labels):
        plt.text(x[i], y[i], label, fontsize=9, ha='center')
    plt.xlabel(topic1)
    plt.ylabel(topic2)
    plt.title("Brand Comparison Bubble Chart")
    plt.grid(True)
    plt.tight_layout()
    plt.show()

