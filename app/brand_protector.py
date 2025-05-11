import os
import json
import requests
import logging
import time
from dotenv import load_dotenv
from typing import List

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
    if not (agents or allow_paths or disallow_paths or cite_as or policy):
        return None
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
