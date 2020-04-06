# -*- coding: utf-8 -*-

from dataclasses import dataclass
from .baseparser import BaseParser, Token, ParseError


@dataclass(frozen=True)
class Edge:
    start: str
    end: str


class GraphParser(BaseParser):
    def __init__(self, graph_spec):
        line = '\n'.join(graph_spec)
        super(GraphParser, self).__init__(line)

        self.spec = graph_spec
        self.nodes = set()
        self.edges = set()

    def _prep_err(self, msg):
        return 'At character {} of "{}":\n\t{}'.format(self.col+1, self.spec[self.row], msg)

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
            raise ParseError(self._prep_err('Cannot handle character "{}"'.format(ch)))

    def _read_edge(self):
        val = self._next_char()
        ch = self._peek_char()
        if ch != '>':
            raise ParseError(self._prep_err('Expected "->", got "-{}"'.format(ch)))
        val += self._next_char()
        return Token('edge', val)

    def _read_node(self):
        nd = self._read_while(GraphParser._is_id)
        return Token('node', nd)

    def parse(self):
        prev_node = None

        while True:
            tk = self._next()

            if tk.type == 'node':
                self.nodes.add(tk.value)
                prev_node = tk.value
            if tk.type == 'edge':
                if not prev_node:
                    raise ParseError(self._prep_err('Cannot find a source node'))
                nx = self._peek()
                if nx.type != 'node':
                    raise ParseError(self._prep_err('Cannot find a target node'))
                self.edges.add(Edge(prev_node, nx.value))
            if tk.type == 'eof':
                break

        return self.nodes, self.edges

    def replace_graph(self, decs):
        """ Replace the block-level decision nodes in the graph with option nodes."""
        # replace nodes
        nds = []
        for nd in self.nodes:
            tmp = decs[nd] if nd in decs else [nd]
            nds.extend(tmp)

        # replace edges
        egs = []
        for eg in self.edges:
            ss = decs[eg.start] if eg.start in decs else [eg.start]
            es = decs[eg.end] if eg.end in decs else [eg.end]
            egs.extend([Edge(s, e) for s in ss for e in es])

        self.nodes = set(nds)
        self.edges = set(egs)
        return self.nodes, self.edges

    def create_default_graph(self, nodes):
        """
        Create the default graph, which is a linear flow of blocks, with the
        same order as they appear in the template script.
        :param nodes: A list of unique blocks.
        :return: nodes and edges
        """
        self.nodes = set(nodes)
        self.edges = set()
        for i in range(len(nodes) - 1):
            self.edges.add(Edge(nodes[i], nodes[i + 1]))
        return self.nodes, self.edges
