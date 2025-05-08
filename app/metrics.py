# File: app/metrics.py

import re
import math
import itertools
import spacy
from typing import List, Tuple

# 1) Load spaCy & add a sentencizer so that .sents works
nlp = spacy.load("en_core_web_sm", disable=["parser", "ner"])
if not nlp.has_pipe("sentencizer"):
    nlp.add_pipe("sentencizer")

# Types
Sentence = Tuple[List[str], str, List[int]]  # tokens, text, citations
Paragraph = List[Sentence]
Doc = List[Paragraph]


def extract_citations_spacy(text: str) -> Doc:
    """
    Splits on blank lines → paragraphs, uses spaCy sentencizer → sentences,
    tokenizes each sentence into word tokens, and pulls out [1], [2], … citations.
    """

    def _citations(sent_text: str) -> List[int]:
        matches = re.findall(r"\[[^\w\s]*(\d+)[^\w\s]*\]", sent_text)
        return [int(m) for m in matches]

    paras = [p.strip() for p in text.split("\n\n") if p.strip()]
    doc: Doc = []
    for p in paras:
        sp = nlp(p)
        para: Paragraph = []
        for sent in sp.sents:
            txt = sent.text.strip()
            if not txt:
                continue
            toks = [token.text for token in sent if not token.is_space]
            cites = _citations(txt)
            para.append((toks, txt, cites))
        if para:
            doc.append(para)
    return doc


def _normalize(scores: List[float], normalize: bool) -> List[float]:
    if not normalize:
        return scores
    total = sum(scores)
    if total <= 0:
        n = len(scores)
        return [1 / n] * n
    return [s / total for s in scores]


def impression_wordpos_count_simple_spacy(
    doc: Doc, n: int = 5, normalize: bool = True
) -> List[float]:
    """
    Word+Position: each citation’s score = word_count * exp(-pos_decay) / #cites
    """
    sents = list(itertools.chain(*doc))
    scores = [0.0] * n
    L = max(1, len(sents) - 1)
    for i, (tokens, _, cites) in enumerate(sents):
        wc = sum(1 for t in tokens if len(t) > 2)
        decay = math.exp(-i / L)
        for c in cites:
            if 1 <= c <= n:
                scores[c - 1] += (wc * decay) / len(cites)
    return _normalize(scores, normalize)


def impression_word_count_simple_spacy(doc: Doc, n: int = 5, normalize: bool = True) -> List[float]:
    """
    Word-only: each citation’s score = word_count / #cites
    """
    sents = list(itertools.chain(*doc))
    scores = [0.0] * n
    for tokens, _, cites in sents:
        wc = sum(1 for t in tokens if len(t) > 2)
        for c in cites:
            if 1 <= c <= n:
                scores[c - 1] += wc / len(cites)
    return _normalize(scores, normalize)


def impression_pos_count_simple_spacy(doc: Doc, n: int = 5, normalize: bool = True) -> List[float]:
    """
    Position-only: each citation’s score = exp(-pos_decay) / #cites
    """
    sents = list(itertools.chain(*doc))
    scores = [0.0] * n
    L = max(1, len(sents) - 1)
    for i, (_, _, cites) in enumerate(sents):
        decay = math.exp(-i / L)
        for c in cites:
            if 1 <= c <= n:
                scores[c - 1] += decay / len(cites)
    return _normalize(scores, normalize)
