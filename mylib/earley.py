'''
A module that implements the Earley Algorithm
'''

from mylib.pcfg import PCFG
from mylib.eval import ParseError

class State():
    '''
    A State is something records the current grammar rule, the dot position and the span
    '''
    def __init__(self, lhs='', rhs=None, start_idx=0, end_idx=0, dot_idx=0):
        '''
        Initialize a state.

        Args:
            lhs (string): The left-hand symbol.
            rhs (list): The right-hand symbols in a list.
            start_idx: The start index of the state in the sentence.
            end_idx: The dot index in the scope of the whole sentence.
            dot_idx: The dot index in the scope of current state.
        '''
        self.uid = 0
        self.lhs = lhs
        if rhs is None:
            self.rhs = []
        else:
            self.rhs = rhs
        self.start_idx = start_idx
        self.end_idx = end_idx
        self.dot_idx = dot_idx
        self.backpointers = []
        self.fwd_prob = 0
        self.in_prob = 0
        self.word = ''

    def __eq__(self, other):
        if not isinstance(other, State):
            return False
        return self.lhs == other.lhs and \
            self.rhs == other.rhs and \
            self.start_idx == other.start_idx and \
            self.end_idx == other.end_idx and \
            self.dot_idx == other.dot_idx

    def next_cat(self) -> str:
        '''
        Get the next right-hand symbol from the constituents predicted by this rule.

        Returns:
            string: The next right-hand symbol, or None if it's already completed.
        '''
        if self.is_completed():
            return None
        return self.rhs[self.dot_idx]

    def is_completed(self) -> bool:
        '''
        Check if the state is completed, which means the dot is already to the\\
        right of all its constituents.

        Returns:
            bool: True if it's completed, otherwise False.
        '''
        return self.dot_idx >= len(self.rhs)

class Chart():
    '''
    A Chart keeps tracks of all of the states during parsing
    '''
    def __init__(self):
        '''
        Initialize a chart. Will always create an initial state (ROOT->.S, [0, 0])
        '''
        initial_state = State('ROOT', ['S'], 0, 0, 0)
        initial_state.fwd_prob = 1.0
        initial_state.in_prob = 1.0
        self.__chart = []
        self.enqueue(initial_state, 0)

    def enqueue(self, state_to_add: State, idx: int):
        '''
        Add a state to the chart

        Args:
            state_to_add (State): The state to add.
            idx (int): The index to insert at.
        '''
        states = []
        if idx < len(self.__chart):
            states = self.__chart[idx]
            for state in states:
                if state == state_to_add:
                    return
        else:
            self.__chart.append(states)
        state_to_add.uid = '{}/{}'.format(idx, len(states))
        states.append(state_to_add)

    def __getitem__(self, key):
        return self.__chart[key]

    def __len__(self):
        return len(self.__chart)

class Earley():
    '''
    The Earley Parser
    '''
    def __init__(self, pcfg: PCFG, sentence: str):
        '''
        Initialize an Earley parser

        Args:
            pcfg (PCFG): The pcfg grammar.
            sentence (str): The sentence to parser
        '''
        self.chart = Chart()
        self.pcfg = pcfg
        self.sentence = sentence

    def parse(self):
        '''
        Parse the setence inside.
        '''
        for i in range(len(self.sentence) + 1):
            word = ''
            inside_i = 0
            if i < len(self.sentence):
                norm, word = self.sentence[i]
            if i >= len(self.chart):
                raise ParseError('Unable to parse sentence: {}'.format(self.sentence))
            while inside_i < len(self.chart[i]):
                state = self.chart[i][inside_i]
                if state.is_completed():
                    self.completer(state)
                else:
                    next_symbol = state.next_cat()
                    if self.pcfg.unary_rules[next_symbol]:
                        self.scanner(state, norm, word)
                    else:
                        self.predictor(state)
                inside_i += 1

        last_state = State()
        for state in self.chart[len(self.sentence)]:
            if state.is_completed() and \
                state.lhs == 'ROOT' and \
                state.in_prob > last_state.in_prob:
                last_state = state

        if last_state and last_state.backpointers:
            return self.backtrace(last_state.backpointers[0])
        return ['']

    def backtrace(self, backpointer: str):
        '''
        Backtrace the parsed tree.
        '''
        state_set, state_idx = backpointer.split('/')
        state = self.chart[int(state_set)][int(state_idx)]
        if len(state.rhs) == 1:
            return [state.lhs, state.word]
        else:
            result = [state.lhs]
            for bp in state.backpointers:
                result.append(self.backtrace(bp))
            return result

    def predictor(self, state: State):
        '''
        The predictor

        Args:
            state (State): The state to expand
        '''
        next_symbol = state.next_cat()
        j = state.end_idx
        states_to_add = []
        for rhs in self.pcfg.binary_rules[next_symbol]:
            candidate = State(next_symbol, list(rhs), j, j, 0)
            rule_prob = self.pcfg.q2[(next_symbol, *rhs)]
            candidate.fwd_prob = state.fwd_prob * rule_prob
            candidate.in_prob = rule_prob
            states_to_add.append(candidate)

        states_to_add.sort(key=lambda x: x.fwd_prob, reverse=True)
        # Prune the tree to the top 10 list
        for candidate in states_to_add[:15]:
            self.chart.enqueue(candidate, j)

    def scanner(self, state: State, norm: str, word: str):
        '''
        The scanner

        Args:
            state (State): The state to be scanned.
            norm (str): The normalized form of the word. It can be the word itself, or "_RARE_".
            word (str): The word to be scanned.
        '''
        next_symbol = state.next_cat()
        if self.pcfg.q1[next_symbol, norm] > 0:
            j = state.end_idx
            state_to_add = State(next_symbol, [norm], j, j + 1, 1)
            state_to_add.word = word
            rule_prob = self.pcfg.q1[next_symbol, norm]
            state_to_add.fwd_prob = rule_prob
            state_to_add.in_prob = rule_prob
            self.chart.enqueue(state_to_add, j + 1)

    def completer(self, state: State):
        '''
        The predictor

        Args:
            state (State): The state to be completed
        '''
        j = state.start_idx
        k = state.end_idx
        for state_in_chart in self.chart[j]:
            if state_in_chart.next_cat() == state.lhs:
                i = state_in_chart.start_idx
                state_to_add = State(state_in_chart.lhs,
                                     state_in_chart.rhs,
                                     i,
                                     k,
                                     state_in_chart.dot_idx + 1)
                state_to_add.backpointers = list(state_in_chart.backpointers)
                state_to_add.backpointers.append(state.uid)
                state_to_add.fwd_prob = state_in_chart.fwd_prob * state.in_prob
                state_to_add.in_prob = state_in_chart.in_prob * state.in_prob
                self.chart.enqueue(state_to_add, k)
