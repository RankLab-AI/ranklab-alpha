# File: app/generation.py

from openai import OpenAI
import os, uuid, time, pickle
from dotenv import load_dotenv

load_dotenv()


# Setup Venice API client (OpenAI-compatible)
openai_client = OpenAI(api_key=os.getenv("VENICE_API_KEY"), base_url="https://api.venice.ai/api/v1")

query_prompt = """Write an accurate and concise answer for the given user question, using _only_ the provided summarized web search results... [your full prompt here]"""


def generate_llm_answer(
    query, sources, num_completions=1, temperature=0.5, verbose=False, model="llama-3.3-70b"
):
    source_text = "\n\n".join([f"### Source {i + 1}:\n{s}" for i, s in enumerate(sources)])
    prompt = query_prompt.format(query=query, source_text=source_text)

    while True:
        try:
            if verbose:
                print("Calling Venice API...")
            response = openai_client.chat.completions.create(
                model=model,
                temperature=temperature,
                max_tokens=1024,
                top_p=1,
                n=num_completions,
                messages=[{"role": "user", "content": prompt}],
            )
            os.makedirs("response_usages_16k", exist_ok=True)
            with open(f"response_usages_16k/{uuid.uuid4()}.pkl", "wb") as f:
                pickle.dump(response.usage, f)
            return [choice.message.content for choice in response.choices]
        except Exception as e:
            print("Error from API:", e)
            time.sleep(15)


def generate_venice_response(
    message: str, temperature: float = 0.5, model: str = "mistral-31-24b"
) -> str:
    """
    Sends a single user message to the Venice API and returns the assistant's reply.
    """
    try:
        response = openai_client.chat.completions.create(
            model=model,
            temperature=temperature,
            max_tokens=1024,
            top_p=1,
            n=1,
            messages=[{"role": "user", "content": message}],
        )
        # Return the content of the first (and only) choice
        return response.choices[0].message.content
    except Exception as e:
        print("Error from Venice API:", e)
        # Re-raise or handle as needed; here we just return an empty string
        return ""
