# File: app/scoring.py

from typing import Dict, List
from .metrics import (
    extract_citations_spacy,
    impression_wordpos_count_simple_spacy,
    impression_word_count_simple_spacy,
    impression_pos_count_simple_spacy,
    impression_relevance_sm_spacy,
    impression_influence_detailed_spacy,
    impression_diversity_detailed_spacy,
    impression_uniqueness_detailed_spacy,
    impression_follow_detailed_spacy,
)


def _avg_percent(arr: List[float]) -> float:
    """
    Average only the non-zero buckets; if all zero, return uniform 100/len(arr).
    """
    nonzero = [x for x in arr if x > 0]
    if not nonzero:
        return round(100.0 / len(arr), 2)
    return round(sum(nonzero) / len(nonzero) * 100, 2)


def compute_scores(text: str, n: int = 5, normalize: bool = True) -> Dict[str, float]:
    """
    Parse `text`, extract citations via spaCy, then compute eight GEO‐style metrics:
      - Word+Position
      - Word-only
      - Position-only
      - Relevance
      - Influence
      - Diversity
      - Uniqueness
      - Follow‐Up

    Returns each as a percentage.
    """
    # 1) Extract citation‐annotated Doc
    doc = extract_citations_spacy(text)

    # 2) Compute the three simple metrics
    wpos = impression_wordpos_count_simple_spacy(doc, n=n, normalize=normalize)
    wcnt = impression_word_count_simple_spacy(doc, n=n, normalize=normalize)
    ppos = impression_pos_count_simple_spacy(doc, n=n, normalize=normalize)

    # 3) Compute the five detailed GEO impressions (for citation #1 by default, returns per‐citation list)
    #    We then average across non‐zero buckets to get a single percent.
    rel = impression_relevance_sm_spacy(doc, text, n=n, normalize=normalize, idx=0)
    infl = impression_influence_detailed_spacy(doc, text, n=n, normalize=normalize, idx=0)
    div = impression_diversity_detailed(doc, text, n=n, normalize=normalize, idx=0)
    uniq = impression_uniqueness_detailed_spacy(doc, text, n=n, normalize=normalize, idx=0)
    foll = impression_follow_detailed_spacy(doc, text, n=n, normalize=normalize, idx=0)

    return {
        "Word+Position": _avg_percent(wpos),
        "Word-only": _avg_percent(wcnt),
        "Position-only": _avg_percent(ppos),
        "Relevance": _avg_percent(rel),
        "Influence": _avg_percent(infl),
        "Diversity": _avg_percent(div),
        "Uniqueness": _avg_percent(uniq),
        "Follow-Up": _avg_percent(foll),
    }
