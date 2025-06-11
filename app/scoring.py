# app/scoring.py

from typing import Dict, List
from .metrics import (
    extract_citations_spacy,
    overall_authoritativeness,
    overall_sourceability,
    overall_uniqueness,
)


def compute_scores(text: str, normalize: bool = True) -> Dict[str, float]:
    """
    Compute new RankLab metrics for whole-document content:
    - Authoritativeness
    - Source-ability
    - Uniqueness
    """
    doc = extract_citations_spacy(text)
    return {
        "Authoritativeness": round(overall_authoritativeness(doc) * 100, 2),
        "Source-ability": round(overall_sourceability(doc) * 100, 2),
        "Uniqueness": round(overall_uniqueness(doc) * 100, 2),
    }
