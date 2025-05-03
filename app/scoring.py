import re
import nltk


def extract_citations_new(text):
    def ecn(sentence):
        citation_pattern = r"\[[^\w\s]*\d+[^\w\s]*\]"
        return [
            int(re.findall(r"\d+", citation)[0])
            for citation in re.findall(citation_pattern, sentence)
        ]

    paras = re.split(r"\n\n", text)
    sentences = [nltk.sent_tokenize(p) for p in paras]
    words = [[(nltk.word_tokenize(s), s, ecn(s)) for s in sentence] for sentence in sentences]
    return words
