from sys import stdin, stderr
from cmd import Cmd
from time import time
import sys, re, json
from json import dumps
from mylib.pcfg import PCFG
from mylib.eval import ParseEvaluator
from mylib.parser import Parser

'''
Created by Arradi Nur Rizal
For Syntactic Parsing Project
'''

class Prompt(Cmd):
    def preloop(self):
        super(Prompt, self).preloop()
        self.algo = "CKY"

    prompt = 'cmd>> '

    def do_exit(self, inp):
        print("Bye")
        return True

    def help_exit(self):
        print('exit the application. Shorthand: x q Ctrl-D.')

    def do_extract_grammar(self, inp):
        i = inp.split()
        treebank_file = i[0]
        grammar_file = i[1]

        start = time()
        print("Extracting grammar from " + treebank_file + " ...", file=stderr)
        pcfg = PCFG()
        pcfg.learn_from_treebank(treebank_file)
        print("Saving grammar to " + grammar_file + " ...", file=stderr)
        pcfg.save_model(grammar_file)
        print("Time: %.2fs\n" % (time() - start), file=stderr)

    def help_extract_grammar(self):
        print("usage: extract_grammar input-path-to-TREEBANK output-path-to-GRAMMAR")

    def do_eval(self, inp):
        i = inp.split()
        key_file = open(i[0])
        prediction_file = open(i[1])

        key_trees = [json.loads(l) for l in key_file]
        predicted_trees = [json.loads(l) for l in prediction_file]
        evaluator = ParseEvaluator()
        evaluator.compute_fscore(key_trees, predicted_trees)
        evaluator.output()

    def help_eval(self):
        print('''Usage: eval path-to-key_file path-to-output_file \n
            Evalute the accuracy of a output trees compared to a key file.\n''')

    def do_bulk_parse(self, inp):
        i = inp.split()
        start = time()
        grammar_file = i[0]
        print("Loading grammar from " + grammar_file + " ...", file=stderr)    
        pcfg = PCFG()
        pcfg.load_model(grammar_file)
        parser = Parser(pcfg)

        print("Parsing sentences ...", file=stderr)
        with open(i[2], "w") as tree_output:
            with open(i[1]) as input_sentences:
                for sentence in input_sentences:
                    if self.algo == "CKY":
                        print("Parsing with CKY algorithm")
                        tree = parser.parse_CKY(sentence)
                    else:
                        print("Parsing with Earley algorithm")
                        tree = parser.parse_Earley(sentence)
                    tree_output.write(dumps(tree)+"\n")

        print("Time: (%.2f)s\n" % (time() - start), file=stderr)

    def help_bulk_parse(self):
        print("usage: bulk_parse path-to-GRAMMAR-file path-to-input-sentence path-to-output")

    def do_use_CKY(self, inp):
        self.algo = "CKY"
        print("Parsing algoritm is set to ", self.algo)
        self.prompt = 'cmd:' + self.algo + '>>'

    def help_use_CKY(self):
        print("usage: use_CKY; this will switch the parse algorithm to CKY")

    def do_use_Earley(self, inp):
        self.algo = "Earley"
        print("Parsing algoritm is set to ", self.algo)
        self.prompt = 'cmd:' + self.algo + '>>'

    def help_use_Earley(self):
        print("usage: use_Earley; this will switch the parse algorithm to Earley")

    def default(self, inp):
        if inp == 'x' or inp == 'q':
            return self.do_exit(inp)

        start = time()
        grammar_file = "data/grammarfile" # this is default assumption
        print("Loading grammar from " + grammar_file + " ...", file=stderr)
        pcfg = PCFG()
        pcfg.load_model(grammar_file)
        parser = Parser(pcfg)

        print("Parsing sentences ...", file=stderr)
        if self.algo == "CKY":
            print("Parsing with CKY algorithm")
            tree = parser.parse_CKY(inp)
        else:
            print("Parsing with Earley algorithm")
            tree = parser.parse_Earley(inp)
        print(dumps(tree))
        print("Time: (%.2f)s\n" % (time() - start), file=stderr)

    do_EOF = do_exit
    help_EOF = help_exit
