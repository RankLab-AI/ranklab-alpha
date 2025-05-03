import openai
from os import getenv
from dotenv import load_dotenv
from firebase_admin import auth as firebase_auth

load_dotenv()

# API Keys
openai.api_key = getenv("OPENAI_API_KEY")

# Firebase JS SDK Config (for injection into login.html)
FIREBASE_JS_CONFIG = {
    "apiKey": getenv("FIREBASE_API_KEY"),
    "authDomain": getenv("FIREBASE_AUTH_DOMAIN"),
    "projectId": getenv("FIREBASE_PROJECT_ID"),
    "appId": getenv("FIREBASE_APP_ID"),
}


# Placeholder LLM treatment function
def generate_treatment(content: str, method: str) -> str:
    return f"[{method} treatment applied to content]:\n\n{content}"


# Placeholder scoring logic
def analyze_content(content: str) -> str:
    return f"Scoring analysis: [placeholder result for: '{content[:60]}...']"


# Firebase session helpers
def verify_firebase_token(token: str):
    return firebase_auth.verify_id_token(token)


def get_current_user(token: str):
    return verify_firebase_token(token)


PROMPT_TEMPLATE = "<s>[INST] <<SYS>>\n{system_prompt}\n<</SYS>>\n\n{user_msg}[/INST]"


def get_prompt(source, query):
    system_prompt = """You are a helpful, respectful and honest assistant.
Given a web source, and context, your only purpose is to summarize the source, and extract topics that may be relevant to the context. Even if a line is distinctly relevant to the context, include that in the summary. It is preferable to pick chunks of text, instead of isolated lines.
"""
    user_msg = f"### Context: ```\n{query}\n```\n\n### Source: ```\n{source}\n```\nNow summarize the text in more than 1000 words, keeping in mind the context and the purpose of the summary. Be as detailed as possible.\n"
    return PROMPT_TEMPLATE.format(system_prompt=system_prompt, user_msg=user_msg)
