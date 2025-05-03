# metrics.py

import itertools
import math


def get_num_words(tokens):
    """
    Counts non-trivial tokens (length > 2).
    """
    return len([t for t in tokens if len(t) > 2])


def impression_wordpos_count_simple(sentences, n=5, normalize=True):
    """
    GEO-style metric that scores citations based on word count and position (decay).
    """
    sentences = list(itertools.chain(*sentences))
    scores = [0] * n
    for i, sent in enumerate(sentences):
        for cit in sent[2]:
            score = get_num_words(sent[0])
            score *= math.exp(-1 * i / max(1, len(sentences) - 1))
            score /= len(sent[2])
            try:
                scores[cit - 1] += score
            except IndexError:
                print(f"[warn] Hallucinated citation: {cit}")
    total = sum(scores)
    return normalize_scores(scores, total, n, normalize)


def impression_word_count_simple(sentences, n=5, normalize=True):
    """
    GEO-style metric based on total word weight assigned to citations.
    """
    sentences = list(itertools.chain(*sentences))
    scores = [0] * n
    for sent in sentences:
        for cit in sent[2]:
            score = get_num_words(sent[0]) / len(sent[2])
            try:
                scores[cit - 1] += score
            except IndexError:
                print(f"[warn] Hallucinated citation: {cit}")
    total = sum(scores)
    return normalize_scores(scores, total, n, normalize)


def impression_pos_count_simple(sentences, n=5, normalize=True):
    """
    GEO-style metric that uses position decay only (ignores word count).
    """
    sentences = list(itertools.chain(*sentences))
    scores = [0] * n
    for i, sent in enumerate(sentences):
        for cit in sent[2]:
            score = math.exp(-1 * i / max(1, len(sentences) - 1)) / len(sent[2])
            try:
                scores[cit - 1] += score
            except IndexError:
                print(f"[warn] Hallucinated citation: {cit}")
    total = sum(scores)
    return normalize_scores(scores, total, n, normalize)


def normalize_scores(scores, total, n, normalize):
    if normalize:
        if total == 0:
            return [1 / n] * n
        return [s / total for s in scores]
    return scores
