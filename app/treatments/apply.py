# treatments/apply.py

from treatments.prompts import (
    QUOTATION_PROMPT,
    STATS_PROMPT,
    FLUENCY_PROMPT,
)

SUPPORTED_METHODS = {
    "quotation": QUOTATION_PROMPT,
    "stats": STATS_PROMPT,
    "fluency": FLUENCY_PROMPT,
}


def apply_treatment(method: str, content: str, query: str = "") -> str:
    """
    Constructs a treatment prompt for the specified method.

    Args:
        method (str): One of ['quotation', 'stats', 'fluency']
        content (str): The original content
        query (str): Optional, relevant query for contextual methods

    Returns:
        str: Final prompt to pass to the LLM
    """
    method = method.lower().strip()
    if method not in SUPPORTED_METHODS:
        raise ValueError(
            f"Unsupported method '{method}'. Choose from: {list(SUPPORTED_METHODS.keys())}"
        )

    return SUPPORTED_METHODS[method](content, query=query)
