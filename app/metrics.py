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


def metric_authoritativeness(
    doc: Doc,
    query: str,
    n: int = 5,
    normalize: bool = True,
) -> List[float]:
    """
    Authoritativeness = 0.5 * Influence + 0.3 * (1 - Position) + 0.2 * Relevance
    """
    influence = impression_influence_detailed_spacy(doc, query, n, normalize=False)
    position = impression_pos_count_simple_spacy(doc, n, normalize=False)
    relevance = impression_relevance_sm_spacy(doc, query, n, normalize=False)

    scores = []
    for i in range(n):
        inv_pos = 1.0 - position[i] if position[i] <= 1.0 else 0.0
        score = 0.5 * influence[i] + 0.3 * inv_pos + 0.2 * relevance[i]
        scores.append(score)

    return _normalize(scores, normalize)


def metric_sourceability(
    doc: Doc,
    query: str,
    n: int = 5,
    normalize: bool = True,
) -> List[float]:
    """
    Source-ability = 0.4 * Word-only + 0.4 * Follow-Up + 0.2 * Relevance
    """
    word_only = impression_word_count_simple_spacy(doc, n, normalize=False)
    follow_up = impression_follow_detailed_spacy(doc, query, n, normalize=False)
    relevance = impression_relevance_sm_spacy(doc, query, n, normalize=False)

    scores = [0.4 * word_only[i] + 0.4 * follow_up[i] + 0.2 * relevance[i] for i in range(n)]
    return _normalize(scores, normalize)


def metric_uniqueness_cited(
    doc: Doc,
    query: str,
    n: int = 5,
    normalize: bool = True,
) -> List[float]:
    """
    Citation-based Uniqueness = 0.6 * Uniqueness + 0.4 * Diversity
    Requires citation-tagged content.
    """
    uniq = impression_uniqueness_detailed_spacy(doc, query, n, normalize=False)
    diversity = impression_diversity_detailed_spacy(doc, query, n, normalize=False)
    scores = [0.6 * uniq[i] + 0.4 * diversity[i] for i in range(n)]
    return _normalize(scores, normalize)


def metric_uniqueness(doc: Doc) -> float:
    """
    Whole-document uniqueness using lexical diversity + syntactic variation.
    Use this for uncited text.
    """
    return overall_uniqueness(doc)


def overall_authoritativeness(doc: Doc) -> float:
    """
    Stricter intrinsic authoritativeness score:
    Requires both high sentence length and strong lexical diversity.
    """
    sents = list(itertools.chain(*doc))
    if not sents:
        return 0.0

    total_tokens = 0
    total_types = set()
    total_length = 0
    for tokens, _, _ in sents:
        total_tokens += len(tokens)
        total_types.update(t.lower() for t in tokens if len(t) > 2)
        total_length += len(tokens)

    avg_sent_len = total_length / len(sents)
    type_token_ratio = len(total_types) / max(total_tokens, 1)

    # Cap each subscore more aggressively
    len_score = min(avg_sent_len / 30.0, 1.0)  # longer required
    type_score = min(type_token_ratio / 0.7, 1.0)  # needs to be >0.7 to max

    # Apply stricter decay: only high if both are high, otherwise diminish
    if len_score < 0.7 or type_score < 0.7:
        # If either is low, penalize heavily
        return 0.5 * len_score * 0.5 + 0.5 * type_score * 0.5
    return 0.5 * len_score + 0.5 * type_score


def overall_sourceability(doc: Doc) -> float:
    """
    Stricter sourceability: only rewards actual named entities, numerics, and true URLs.
    """
    import re

    sents = list(itertools.chain(*doc))
    if not sents:
        return 0.0

    # Use spaCy NER for named entities
    nlp_ner = spacy.load("en_core_web_sm", disable=["parser"])
    ner_text = "\n".join(sent for _, sent, _ in itertools.chain(*doc))
    ents = nlp_ner(ner_text).ents
    named_entities = {
        ent.text
        for ent in ents
        if ent.label_ in {"ORG", "GPE", "PERSON", "PRODUCT", "EVENT", "WORK_OF_ART"}
    }

    url_pattern = re.compile(r"https?://|www\.")

    num_tokens = 0
    named_entity_hits = 0
    url_tokens = 0

    for tokens, _, _ in sents:
        for tok in tokens:
            if tok.isnumeric():
                num_tokens += 1
            if tok in named_entities:
                named_entity_hits += 1
            if url_pattern.search(tok):
                url_tokens += 1

    total = max(len(sents), 1)
    score = (
        0.4 * (num_tokens / total) + 0.4 * (named_entity_hits / total) + 0.2 * (url_tokens / total)
    )
    return min(score, 1.0)


def overall_uniqueness(doc: Doc) -> float:
    """
    Stricter uniqueness: higher diversity threshold, dampened score for minor variation,
    and penalty for n-gram redundancy.
    """
    import numpy as np
    from collections import Counter

    sents = list(itertools.chain(*doc))
    if not sents:
        return 0.0

    token_counts = []
    all_tokens = []

    for tokens, _, _ in sents:
        token_counts.append(len(tokens))
        all_tokens.extend([t.lower() for t in tokens if len(t) > 2])

    total_tokens = len(all_tokens)
    types = set(all_tokens)
    type_token_ratio = len(types) / max(total_tokens, 1)
    sent_len_std = np.std(token_counts) / max(np.mean(token_counts), 1)

    # Apply stricter scaling
    capped_diversity = max(0.0, min((type_token_ratio - 0.5) / 0.4, 1.0))
    capped_std = max(0.0, min((sent_len_std - 0.3) / 1.5, 1.0))

    # Penalize n-gram redundancy
    trigrams = list(zip(all_tokens, all_tokens[1:], all_tokens[2:]))
    trigram_counts = Counter(trigrams)
    redundancy_penalty = max(trigram_counts.values()) / len(trigrams) if trigrams else 0

    base_score = 0.6 * capped_diversity + 0.4 * capped_std
    return base_score * (1 - redundancy_penalty)
