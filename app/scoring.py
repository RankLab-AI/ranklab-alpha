import re


def simple_sent_tokenize(text):
    """
    Splits text into sentences using basic punctuation heuristics.
    """
    # Add space after punctuation if not followed by space already (edge case cleanup)
    text = re.sub(r"([.?!])([A-Z])", r"\1 \2", text)
    # Naive sentence splitting by punctuation
    return re.split(r"(?<=[.?!])\s+", text.strip())


def simple_word_tokenize(sentence):
    """
    Splits sentence into words using whitespace and basic punctuation.
    """
    return re.findall(r"\b\w+\b", sentence)


def extract_citations_new(text):
    """
    Extracts citation references (like [1], [2]) from each sentence.
    Returns: list of paragraphs → sentences → (tokens, raw sentence, [citation indices])
    """

    def extract_from_sentence(sentence):
        citation_pattern = r"\[[^\w\s]*\d+[^\w\s]*\]"
        return [int(match) for match in re.findall(r"\d+", sentence)]

    # Naive paragraph splitting
    paras = re.split(r"\n\s*\n", text.strip())
    sentences = [simple_sent_tokenize(p) for p in paras]

    return [
        [(simple_word_tokenize(s), s, extract_from_sentence(s)) for s in paragraph]
        for paragraph in sentences
    ]
