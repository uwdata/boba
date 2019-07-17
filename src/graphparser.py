#!/usr/bin/env python3

from dataclasses import dataclass
import re


@dataclass(frozen=True)
class Edge:
    start: str
    end: str


@dataclass
class Token:
    type: str
    value: str


class GraphSyntaxError(SyntaxError):
    pass


class GraphParser:
    def __init__(self, graph_spec):
        self.spec = graph_spec
        self.line = '\n'.join(graph_spec)
        self.i = 0
        self.row = 0
        self.col = 0
        self.current = None
        self.nodes = set()
        self.edges = set()

    def _prep_err(self, msg):
        return 'At character {} of "{}":\n\t{}'.format(self.col+1, self.spec[self.row], msg)

    def _prep_res(self, success, err):
        return {'success': success, 'err': err}

    @staticmethod
    def _is_whitespace(char):
        return any(c == char for c in ' \t\n')

    @staticmethod
    def _is_id_start(ch):
        return bool(re.match('[a-zA-Z]', ch))

    @staticmethod
    def _is_id(ch):
        return bool(re.match('[a-zA-Z0-9]', ch))

    def _next_char(self):
        ch = self.line[self.i]
        self.i += 1
        if ch == '\n':
            self.row += 1
            self.col = 0
        else:
            self.col += 1
        return ch

    def _peek_char(self):
        return self.line[self.i]

    def _is_end(self):
        return self.i >= len(self.line)

    def _read_while(self, fun):
        s = ''
        while not self._is_end() and fun(self._peek_char()):
            s += self._next_char()
        return s

    def _read_next(self):
        self._read_while(GraphParser._is_whitespace)
        if self._is_end():
            return Token('eof', '')

        ch = self._peek_char()
        if ch == '-':
            return self._read_edge()
        elif GraphParser._is_id_start(ch):
            return self._read_node()
        else:
            raise GraphSyntaxError(self._prep_err('Cannot handle character "{}"'.format(ch)))

    def _read_edge(self):
        val = self._next_char()
        ch = self._peek_char()
        if ch != '>':
            raise GraphSyntaxError(self._prep_err('Expected "->", got "-{}"'.format(ch)))
        val += self._next_char()
        return Token('edge', val)

    def _read_node(self):
        nd = self._read_while(GraphParser._is_id)
        return Token('node', nd)

    def _peek(self):
        if not self.current:
            self.current = self._read_next()
        return self.current

    def _next(self):
        tmp = self.current
        self.current = None
        return tmp or self._read_next()

    def parse(self):
        prev_node = None

        while True:
            try:
                tk = self._next()

                if tk.type == 'node':
                    self.nodes.add(tk.value)
                    prev_node = tk.value
                if tk.type == 'edge':
                    if not prev_node:
                        return self._prep_res(False, self._prep_err('Cannot find a source node'))
                    nx = self._peek()
                    if nx.type != 'node':
                        return self._prep_res(False, self._prep_err('Cannot find a target node'))
                    self.edges.add(Edge(prev_node, nx.value))
                if tk.type == 'eof':
                    break

            except GraphSyntaxError as e:
                return self._prep_res(False, e.args[0])

        res = self._prep_res(True, '')
        res['nodes'] = self.nodes
        res['edges'] = self.edges
        return res
