import itertools
import math


def get_num_words(line):
    return len([x for x in line if len(x) > 2])


def impression_wordpos_count_simple(sentences, n=5, normalize=True):
    sentences = list(itertools.chain(*sentences))
    scores = [0 for _ in range(n)]
    for i, sent in enumerate(sentences):
        for cit in sent[2]:
            score = get_num_words(sent[0])
            score *= math.exp(-1 * i / (len(sentences) - 1)) if len(sentences) > 1 else 1
            score /= len(sent[2])
            try:
                scores[cit - 1] += score
            except:
                print(f"Citation Hallucinated: {cit}")
    total = sum(scores)
    return (
        [x / total for x in scores]
        if normalize and total != 0
        else [1 / n for _ in range(n)]
        if normalize
        else scores
    )
