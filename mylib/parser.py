"""
Extension of
CKY algorithm from the "Natural Language Processing" course by Michael Collins
https://class.coursera.org/nlangp-001/class
"""
from collections import defaultdict
from pprint import pprint

from mylib.tokenizer import PennTreebankTokenizer
from mylib.earley import Earley

def argmax(lst):
    return max(lst) if lst else (0.0, None)

def backtrace(back, bp):
    # ADD YOUR CODE HERE
    # Extract the tree from the backpointers
    if not back:
        return None
    if len(back) == 6:
        (C, C1, C2, Min, Mid, Max) = back
        return [C, backtrace(bp[Min, Mid, C1], bp),
                backtrace(bp[Mid+1, Max, C2], bp)]
    else:
        (C, C1, Min, Min) = back
        return [C, C1]

def CKY(pcfg, norm_words):
    # NOTE: norm_words is a list of pairs (norm, word), where word is the word
    #       occurring in the input sentence and norm is either the same word,
    #       if it is a known word according to the grammar, or the string _RARE_.
    #       Thus, norm should be used for grammar lookup but word should be used
    #       in the output tree.

    # Initialize your charts (for scores and backpointers)
    x, n = [("", "")] + norm_words, len(norm_words)
    pi = defaultdict(float)
    bp = defaultdict(tuple)

    # Code for adding the words to the chart
    for Min in range(1, n+1):
        for C in pcfg.N:
            norm, word = x[Min]
            if (C, norm) in pcfg.q1:
                pi[Min, Min, C] = pcfg.q1[C, norm]
                bp[Min, Min, C] = (C, word, Min, Min)
    # Code for the dynamic programming part, where larger and larger subtrees are built
    for l in range(1, n):
        for Min in range(1, n-l+1):
            Max = Min+l
            for C in pcfg.N:
                score, back = argmax([(
                    pcfg.q2[C, C1, C2] * pi[Min, Mid, C1] * pi[Mid+1, Max, C2],
                    (C, C1, C2, Min, Mid, Max)
                    ) for Mid in range(Min, Max)
                        for C1, C2 in pcfg.binary_rules[C]
                            if pi[Min, Mid, C1] > 0.0
                            if pi[Mid+1, Max, C2] > 0.0
                ])

                if score > 0.0:
                    bp[Min, Max, C], pi[Min, Max, C] = back, score
    # Below is one option for retrieving the best trees,
    # assuming we only want trees with the "S" category
    # This is a simplification, since not all sentences are of the category "S"
    # The exact arguments also depends on how you implement your back-pointer chart.
    # Below it is also assumed that it is called "bp"
    #return backtrace(bp[0, n, "S"], bp)
    _, top = max([(pi[1, n, C], bp[1, n, C]) for C in pcfg.N])
    return backtrace(top, bp)

class Parser:
    def __init__(self, pcfg):
        self.pcfg = pcfg
        self.tokenizer = PennTreebankTokenizer()

    def normalize_sentence(self, sentence):
        words = self.tokenizer.tokenize(sentence)
        norm_words = []
        for word in words:                # rare words normalization + keep word
            norm_words.append((self.pcfg.norm_word(word), word))
        return norm_words

    def parse_CKY(self, sentence):
        tree = CKY(self.pcfg, self.normalize_sentence(sentence))
        tree[0] = tree[0].split("|")[0]
        return tree

    def parse_Earley(self, sentence):
        earley = Earley(self.pcfg, self.normalize_sentence(sentence))
        tree = earley.parse()
        tree[0] = tree[0].split("|")[0]
        return tree

def display_tree(tree):
    pprint(tree)
