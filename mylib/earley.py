'''
A module that implements the Earley Algorithm
'''

from mylib.pcfg import PCFG

class State():
    '''
    A State is something records the current grammar rule, the dot position and the span
    '''
    def __init__(self, lhs: str, rhs: list, start_idx: int, dot_idx_s: int, dot_idx_r: int):
        '''
        Initialize a state.

        Args:
            lhs (string): The left-hand symbol.
            rhs (list): The right-hand symbols in a list.
            start_idx: The start index of the state in the sentence.
            dot_idx_s: The dot index in the scope of the whole sentence.
            dot_idx_r: The dot index in the scope of current state.
        '''
        self.uid = 0
        self.lhs = lhs
        self.rhs = rhs
        self.start_idx = start_idx
        self.dot_idx_s = dot_idx_s
        self.dot_idx_r = dot_idx_r
        self.backpointers = []

    def __eq__(self, other):
        if not isinstance(other, State):
            return False
        return self.lhs == other.lhs and self.rhs == other.rhs

    def next_cat(self) -> str:
        '''
        Get the next right-hand symbol from the constituents predicted by this rule.

        Returns:
            string: The next right-hand symbol, or None if it's already completed.
        '''
        if self.is_completed():
            return None
        return self.rhs[self.dot_idx_r]

    def is_completed(self) -> bool:
        '''
        Check if the state is completed, which means the dot is already to the\\
        right of all its constituents.

        Returns:
            bool: True if it's completed, otherwise False.
        '''
        return self.dot_idx_r >= len(self.rhs)

class Chart():
    '''
    A Chart keeps tracks of all of the states during parsing
    '''
    def __init__(self):
        '''
        Initialize a chart. Will always create an initial state (ROOT->.S, [0, 0])
        '''
        initial_state = State('ROOT', ['S'], 0, 0, 0)
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
        last_state = None
        for i in range(len(self.sentence) + 1):
            word = ''
            inside_i = 0
            if i < len(self.sentence):
                (_, word) = self.sentence[i]
            while inside_i < len(self.chart[i]):
                state = self.chart[i][inside_i]
                if state.is_completed():
                    self.completer(state)
                else:
                    next_symbol = state.next_cat()
                    if next_symbol in self.pcfg.POS:
                        self.scanner(state, word)
                    else:
                        self.predictor(state)
                inside_i += 1

                if state.is_completed() and state.lhs == 'ROOT':
                    last_state = state

        return self.backtrace(last_state.backpointers[0])

    def backtrace(self, backpointer: str):
        '''
        Backtrace the parsed tree.
        '''
        chart_row, chart_col = backpointer.split('/')
        state = self.chart[int(chart_row)][int(chart_col)]
        if len(state.rhs) == 1:
            return [state.lhs, state.rhs[0]]
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
        j = state.dot_idx_s
        for rhs in self.pcfg.binary_rules[next_symbol]:
            state_to_add = State(next_symbol, list(rhs), j, j, 0)
            self.chart.enqueue(state_to_add, j)

    def scanner(self, state: State, word: str):
        '''
        The scanner

        Args:
            state (State): The state to be scanned.
            word (str): The word to be scanned.
        '''
        next_symbol = state.next_cat()
        if self.pcfg.q1[next_symbol, word] > 0:
            j = state.dot_idx_s
            state_to_add = State(next_symbol, [word], j, j + 1, 1)
            self.chart.enqueue(state_to_add, j + 1)

    def completer(self, state: State):
        '''
        The predictor

        Args:
            state (State): The state to be completed
        '''
        j = state.start_idx
        k = state.dot_idx_s
        for state_in_chart in self.chart[j]:
            if state_in_chart.next_cat() == state.lhs:
                i = state_in_chart.start_idx
                state_to_add = State(state_in_chart.lhs,
                                     state_in_chart.rhs,
                                     i,
                                     k,
                                     state_in_chart.dot_idx_r + 1)
                state_to_add.backpointers = list(state_in_chart.backpointers)
                state_to_add.backpointers.append(state.uid)
                self.chart.enqueue(state_to_add, k)
