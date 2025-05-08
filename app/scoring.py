# File: app/scoring.py

from typing import Dict
from .metrics import (
    extract_citations_spacy,
    impression_wordpos_count_simple_spacy,
    impression_word_count_simple_spacy,
    impression_pos_count_simple_spacy,
)


def compute_scores(text: str, n: int = 5, normalize: bool = True) -> Dict[str, float]:
    """
    Parse `text`, extract citations via spaCy, then compute
    three GEO‐style metrics. Returns each as a percentage.
    """
    doc = extract_citations_spacy(text)

    wpos = impression_wordpos_count_simple_spacy(doc, n=n, normalize=normalize)
    wcnt = impression_word_count_simple_spacy(doc, n=n, normalize=normalize)
    ppos = impression_pos_count_simple_spacy(doc, n=n, normalize=normalize)

    # average only nonzero buckets
    def avg_percent(arr):
        nonzero = [x for x in arr if x > 0]
        if not nonzero:
            return round((1 / len(arr)) * 100, 2)
        return round(sum(nonzero) / len(nonzero) * 100, 2)

    return {
        "Word+Position": avg_percent(wpos),
        "Word-only": avg_percent(wcnt),
        "Position-only": avg_percent(ppos),
    }
