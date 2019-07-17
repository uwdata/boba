#!/usr/bin/env python3

# Ugly hack to allow import from the root folder
import sys
import os
sys.path.insert(0, os.path.abspath('..'))

import unittest
from src.graphparser import GraphParser, Edge


class TestParser(unittest.TestCase):
    def test_good_specs(self):
        spec = ['A -> B -> C1', 'B->C2']
        res = GraphParser(spec).parse()
        self.assertTrue(res['success'])
        self.assertSetEqual(res['nodes'], {'A', 'B', 'C1', 'C2'})
        edges = {Edge('A', 'B'), Edge('B', 'C1'), Edge('B', 'C2')}
        self.assertSetEqual(res['edges'], edges)

    def test_weird_specs(self):
        spec = ['a->a->a->a  b ']
        res = GraphParser(spec).parse()
        self.assertTrue(res['success'])
        self.assertSetEqual(res['nodes'], {'a', 'b'})
        self.assertSetEqual(res['edges'], {Edge('a', 'a')})

        spec = ['a  b', 'c']
        res = GraphParser(spec).parse()
        self.assertTrue(res['success'])
        self.assertSetEqual(res['nodes'], {'a', 'b', 'c'})
        self.assertSetEqual(res['edges'], set())

        spec = ['a->b c->b']
        res = GraphParser(spec).parse()
        self.assertTrue(res['success'])
        self.assertSetEqual(res['nodes'], {'a', 'b', 'c'})
        self.assertSetEqual(res['edges'], {Edge('a', 'b'), Edge('c', 'b')})

    def test_syntax_error(self):
        spec = ['my_first_node -> my_second_node']
        res = GraphParser(spec).parse()
        self.assertFalse(res['success'])
        self.assertRegex(res['err'], '(?i)cannot handle character')

        spec = ['-> B']
        res = GraphParser(spec).parse()
        self.assertFalse(res['success'])
        self.assertRegex(res['err'], '(?i)source node')

        spec = ['A -> B ->']
        res = GraphParser(spec).parse()
        self.assertFalse(res['success'])
        self.assertRegex(res['err'], '(?i)target node')

        spec = ['A - B']
        res = GraphParser(spec).parse()
        self.assertFalse(res['success'])

        spec = ['A->B->C, B->D']
        res = GraphParser(spec).parse()
        self.assertFalse(res['success'])


if __name__ == '__main__':
    unittest.main()
