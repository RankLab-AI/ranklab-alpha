# app/scoring.py

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


def compute_scores(text: str, normalize: bool = True) -> Dict[str, float]:
    """
    Parse `text`, extract citations via spaCy, then compute
    eight GEO-style metrics over however many citations you actually have.
    """
    # 1) Extract citation-annotated Doc
    doc = extract_citations_spacy(text)

    # 2) Count how many distinct citation IDs we have
    all_cites = [c for para in doc for (_, _, cites) in para for c in cites]
    n = max(all_cites) if all_cites else 0

    if n == 0:
        # no citations → zero out every metric
        return {
            m: 0.0
            for m in [
                "Word+Position",
                "Word-only",
                "Position-only",
                "Relevance",
                "Influence",
                "Diversity",
                "Uniqueness",
                "Follow-Up",
            ]
        }

    # 3) Simple GEO metrics
    wpos = impression_wordpos_count_simple_spacy(doc, n=n, normalize=normalize)
    wcnt = impression_word_count_simple_spacy(doc, n=n, normalize=normalize)
    ppos = impression_pos_count_simple_spacy(doc, n=n, normalize=normalize)

    # 4) Detailed GEO impressions (we anchor all of them to citation #1)
    rel = impression_relevance_sm_spacy(doc, text, n=n, normalize=normalize)
    infl = impression_influence_detailed_spacy(doc, text, n=n, normalize=normalize)
    div = impression_diversity_detailed_spacy(doc, text, n=n, normalize=normalize)
    uniq = impression_uniqueness_detailed_spacy(doc, text, n=n, normalize=normalize)
    foll = impression_follow_detailed_spacy(doc, text, n=n, normalize=normalize)

    # helper to average only the non-zero buckets
    def _pct_of_bucket(scores: List[float], idx: int = 0, perc=False) -> float:
        """
        Take the normalized score for bucket `idx` and turn it into a percentage.
        """
        return scores[idx] * 100.0 if perc else scores[idx]

    return {
        "Word+Position": _pct_of_bucket(wpos),
        "Word-only": _pct_of_bucket(wcnt),
        "Position-only": _pct_of_bucket(ppos, perc=True),
        "Relevance": _pct_of_bucket(rel),
        "Influence": _pct_of_bucket(infl),
        "Diversity": _pct_of_bucket(div, perc=True),
        "Uniqueness": _pct_of_bucket(uniq, perc=True),
        "Follow-Up": _pct_of_bucket(foll),
    }
