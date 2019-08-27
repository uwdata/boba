#!/usr/bin/env python3

# Ugly hack to allow import from the root folder
import sys
import os
sys.path.insert(0, os.path.abspath('..'))

import unittest
from boba.graphparser import GraphParser, Edge, ParseError


class TestParser(unittest.TestCase):
    def test_good_specs(self):
        spec = ['A -> B -> C1', 'B->C2']
        nodes, edges = GraphParser(spec).parse()
        self.assertSetEqual(nodes, {'A', 'B', 'C1', 'C2'})
        exp_edges = {Edge('A', 'B'), Edge('B', 'C1'), Edge('B', 'C2')}
        self.assertSetEqual(edges, exp_edges)

    def test_weird_specs(self):
        spec = ['a->a->a->a  b ']
        nds, eds = GraphParser(spec).parse()
        self.assertSetEqual(nds, {'a', 'b'})
        self.assertSetEqual(eds, {Edge('a', 'a')})

        spec = ['a  b', 'c']
        nds, eds = GraphParser(spec).parse()
        self.assertSetEqual(nds, {'a', 'b', 'c'})
        self.assertSetEqual(eds, set())

        spec = ['a->b c->b']
        nds, eds = GraphParser(spec).parse()
        self.assertSetEqual(nds, {'a', 'b', 'c'})
        self.assertSetEqual(eds, {Edge('a', 'b'), Edge('c', 'b')})

    def test_syntax_error(self):
        spec = ['my_first_node -> my_second_node']
        nds, eds = GraphParser(spec).parse()
        self.assertSetEqual(nds, {'my_first_node', 'my_second_node'})
        self.assertSetEqual(eds, {Edge('my_first_node', 'my_second_node')})

        spec = ['_start -> _end']
        with self.assertRaisesRegex(ParseError, '(?i)cannot handle character'):
            GraphParser(spec).parse()

        spec = ['-> B']
        with self.assertRaisesRegex(ParseError, '(?i)source node'):
            GraphParser(spec).parse()

        spec = ['A -> B ->']
        with self.assertRaisesRegex(ParseError, '(?i)target node'):
            GraphParser(spec).parse()

        spec = ['A - B']
        with self.assertRaises(ParseError):
            GraphParser(spec).parse()

        spec = ['A->B->C, B->D']
        with self.assertRaises(ParseError):
            GraphParser(spec).parse()


if __name__ == '__main__':
    unittest.main()
