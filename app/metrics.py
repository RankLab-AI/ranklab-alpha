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
        return [int(m) for m in re.findall(r"\[[^\w\s]*(\d+)[^\w\s]*\]", sent_text)]

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
        return [1 / len(scores)] * len(scores)
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


def impression_relevance_sm_spacy(
    doc: Doc, query: str, n: int = 5, normalize: bool = True
) -> List[float]:
    """
    Approximate relevance by token-overlap between query and each citation sentence.
    """
    # Prepare a set of query tokens (filtering out stop-words & punctuation)
    qdoc = nlp(query.lower())
    query_tokens = {tok.text for tok in qdoc if tok.is_alpha and not tok.is_stop}

    # Flatten to a list of sentences
    sents = list(itertools.chain(*doc))
    scores = [0.0] * n

    for tokens, _, cites in sents:
        if not cites:
            continue
        # count overlap
        overlap = sum(1 for t in tokens if t in query_tokens)
        # normalize by sentence length to avoid bias toward very long sentences
        score = overlap / max(len(tokens), 1)
        for c in cites:
            if 1 <= c <= n:
                scores[c - 1] += score / len(cites)

    if normalize:
        total = sum(scores)
        if total <= 0:
            return [1 / n] * n
        return [s / total for s in scores]
    else:
        return scores


def impression_influence_detailed_spacy(
    doc: Doc,
    query: str,
    n: int = 5,
    normalize: bool = True,
    idx: int = 0,  # unused; we score all citations
) -> List[float]:
    """
    Influence: sum of token–overlap between each citation's sentences and the query.
    """
    # tokenize & normalize the query
    q_doc = nlp(query.lower())
    query_tokens = {tok.text for tok in q_doc if not tok.is_stop and not tok.is_punct}

    # flatten sentences
    sents = list(itertools.chain(*doc))
    scores = [0.0] * n

    for tokens, _, cites in sents:
        # normalize and dedupe the sentence tokens
        sent_tokens = {t.lower() for t in tokens if len(t) > 2}
        overlap = sent_tokens & query_tokens
        weight = len(overlap)
        for c in cites:
            if 1 <= c <= n:
                scores[c - 1] += weight

    return _normalize(scores, normalize)


def impression_diversity_detailed_spacy(
    doc: Doc,
    query: str,  # unused here, but kept for interface consistency
    n: int = 5,
    normalize: bool = True,
    idx: int = 0,  # unused, all citations scored
) -> List[float]:
    """
    Diversity: type–token ratio for each citation’s sentences.
    """
    # flatten sentences
    sents = list(itertools.chain(*doc))

    # collect tokens per citation
    token_bags = {c: [] for c in range(1, n + 1)}
    for tokens, _, cites in sents:
        # only non-trivial tokens
        filtered = [t.lower() for t in tokens if len(t) > 2]
        for c in cites:
            if 1 <= c <= n:
                token_bags[c].extend(filtered)

    # compute type–token ratio
    scores = []
    for c in range(1, n + 1):
        bag = token_bags[c]
        if not bag:
            scores.append(0.0)
        else:
            unique = len(set(bag))
            total = len(bag)
            scores.append(unique / total)

    return _normalize(scores, normalize)


def impression_uniqueness_detailed_spacy(
    doc: Doc,
    query: str,  # unused here, but kept for signature consistency
    n: int = 5,
    normalize: bool = True,
    idx: int = 0,  # which citation to focus on for per-citation scoring
) -> List[float]:
    """
    Uniqueness: for each citation, measure how many unique tokens it contributes
    relative to the union of all citations’ tokens.
    """
    # 1) Gather token sets per citation index
    citation_tokens = {i: set() for i in range(1, n + 1)}
    for sent_tokens, _, cites in itertools.chain(*doc):
        for c in cites:
            if 1 <= c <= n:
                # add all non-stop, lowercased tokens of this sentence
                citation_tokens[c].update(t.lower() for t in sent_tokens if len(t) > 2)

    # 2) Compute union of all citation tokens
    all_tokens = set().union(*citation_tokens.values()) or set()

    # 3) For each citation, uniqueness = |its_tokens \ all_others_tokens| / |its_tokens|
    scores = []
    for c in range(1, n + 1):
        toks = citation_tokens[c]
        if not toks:
            scores.append(0.0)
            continue
        others = all_tokens - toks
        unique_count = len(toks - (all_tokens - toks))
        # If you want strictly unique compared to others:
        # unique_count = len(toks - (all_tokens - toks))
        # But since `others` = union minus self, uniqueness = |toks \ others| / |toks|
        scores.append(unique_count / len(toks))

    return _normalize(scores, normalize)


def impression_follow_detailed_spacy(
    doc: Doc,
    query: str,  # unused here, kept for signature
    n: int = 5,
    normalize: bool = True,
    idx: int = 0,  # not used, since we score *all* citations
) -> List[float]:
    """
    Follow-Up: for each citation, sum how many sentences come *after* each time it's cited.
    The more follow-on discussion, the higher the score.
    """
    # flatten sentences
    sents = list(itertools.chain(*doc))
    total_sents = len(sents)
    # initialize counters
    follow_counts = [0.0] * n

    for i, (_, _, cites) in enumerate(sents):
        # number of sentences remaining after this one
        remaining = total_sents - i - 1
        for c in cites:
            if 1 <= c <= n:
                follow_counts[c - 1] += remaining

    # if no citations at all, fall back to uniform
    return _normalize(follow_counts, normalize)
