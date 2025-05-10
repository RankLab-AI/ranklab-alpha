import os
import json
import requests
import time
from dotenv import load_dotenv
from rich import print
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

console = Console()


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


def display_results(brands_info):
    table = Table(title="Brand Summary Comparison", show_lines=True)
    table.add_column("Brand", style="cyan", no_wrap=True)
    table.add_column("LLM Summary")
    table.add_column("Keywords")
    table.add_column("Offerings")
    table.add_column("Criticisms")
    table.add_column("Alternatives")

    for info in brands_info:
        table.add_row(
            info["brand"],
            info["summary"],
            info["keywords"],
            info["offerings"],
            info["criticisms"],
            info["alternatives"],
        )
    console.print(table)


def main():
    print("[bold green]=== BrandGuard: LLM Insight Tool ===[/bold green]\n")

    brand = Prompt.ask("Enter your brand").strip()
    competitors = Prompt.ask("Enter competitors (comma-separated)").strip().split(",")

    all_brands = [brand] + [c.strip() for c in competitors if c.strip()]
    all_infos = []

    for b in all_brands:
        print(f"\n🔍 Querying GROQ for: [yellow]{b}[/yellow]...\n")
        result = get_groq_response(b)
        brand_info = summarize_brand(result)
        all_infos.append(brand_info)
        time.sleep(2)

    print("\n[bold green]=== Brand Summary Comparison ===[/bold green]\n")
    display_results(all_infos)

    print("\n[bold blue]=== Optional: Generate llm.txt file to guide LLM bots ===[/bold blue]")
    generate_llm = (
        Prompt.ask("Would you like to generate a llm.txt file? (yes/no)", default="no")
        .strip()
        .lower()
    )

    if generate_llm == "yes":
        agents = Prompt.ask(
            "Enter target LLMs (comma-separated, e.g., ChatGPT,Gemini)", default="ChatGPT"
        ).split(",")
        allow_paths = Prompt.ask("Paths to ALLOW (comma-separated)", default="/").split(",")
        disallow_paths = Prompt.ask(
            "Paths to DISALLOW (comma-separated)", default="/private/"
        ).split(",")
        cite_as = Prompt.ask("Canonical citation URL (optional)", default="").strip()
        policy = Prompt.ask(
            "Policy (summary, no-summary, citation-required, no-training)",
            default="citation-required",
        ).strip()

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

        with open("llm.txt", "w") as f:
            f.write(llm_txt)

        print(
            "\n[bold green]✅ llm.txt file generated and saved in the current directory.[/bold green]"
        )


if __name__ == "__main__":
    main()
