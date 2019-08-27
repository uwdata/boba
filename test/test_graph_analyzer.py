#!/usr/bin/env python3

# Ugly hack to allow import from the root folder
import sys
import os
sys.path.insert(0, os.path.abspath('..'))

import unittest
from boba.graphparser import GraphParser
from boba.graphanalyzer import GraphAnalyzer, InvalidGraphError


class TestGraphAnalyzer(unittest.TestCase):

    def cp_helper(self, spec, expected):
        nodes, edges = GraphParser(spec).parse()
        ga = GraphAnalyzer(nodes, edges)
        ga._construct_paths()
        expected = set([','.join(p) for p in expected])
        actual = set([','.join(p) for p in ga.paths])
        self.assertSetEqual(actual, expected)

    def test_construct_paths(self):
        # normal
        spec = ['a->b->c', 'b->d']
        expected = [['a', 'b', 'c'], ['a', 'b', 'd']]
        self.cp_helper(spec, expected)

        # single node
        spec = ['a']
        expected = [['a']]
        self.cp_helper(spec, expected)

        # multiple sources and targets
        spec = ['a->b->c', 'a2->b->c2']
        expected = [['a', 'b', 'c'], ['a2', 'b', 'c2'], ['a', 'b', 'c2'],
                    ['a2', 'b', 'c']]
        self.cp_helper(spec, expected)

        # disconnected
        spec = ['a->b->c', 'e->f']
        expected = [['a', 'b', 'c'], ['e', 'f']]
        self.cp_helper(spec, expected)

        # cyclic
        spec = ['a->b->c->a']
        nodes, edges = GraphParser(spec).parse()
        ga = GraphAnalyzer(nodes, edges)
        with self.assertRaises(InvalidGraphError):
            ga._construct_paths()

    def source_helper(self, spec, exp_source, exp_target):
        nodes, edges = GraphParser(spec).parse()
        ga = GraphAnalyzer(nodes, edges)
        self.assertSetEqual(ga._get_source(), exp_source)
        self.assertSetEqual(ga._get_target(), exp_target)

    def test_get_source_and_target(self):
        # normal
        spec = ['a->b->d', 'a->b->c']
        source = {'a'}
        target = {'d', 'c'}
        self.source_helper(spec, source, target)

        # disconnected
        spec = ['a->b->d', 'c->e']
        source = {'a', 'c'}
        target = {'d', 'e'}
        self.source_helper(spec, source, target)

        # a single node
        spec = ['a']
        source = {'a'}
        target = {'a'}
        self.source_helper(spec, source, target)

        # cyclic
        spec = ['a->b->c->d->a']
        source = set()
        target = set()
        self.source_helper(spec, source, target)

        # complex
        spec = ['a->b->d', 'a->c->b->d', 'c->a->d']
        source = set()
        target = {'d'}
        self.source_helper(spec, source, target)

    def path_helper(self, spec, s, t, expected):
        nodes, edges = GraphParser(spec).parse()
        ga = GraphAnalyzer(nodes, edges)
        ga._all_paths(s, t)
        expected = set([','.join(p) for p in expected])
        actual = set([','.join(p) for p in ga.paths])
        self.assertSetEqual(actual, expected)

    def test_get_path(self):
        """ test if the program correctly gets all paths from s to t"""

        spec = ['a->b->c', 'b->d', 'e']
        start = 'a'
        stop = 'e'
        expected = []
        self.path_helper(spec, start, stop, expected)

        spec = ['a->b->c', 'b->d', 'e']
        start = 'a'
        stop = 'c'
        expected = [['a', 'b', 'c']]
        self.path_helper(spec, start, stop, expected)

        spec = ['a->b->c', 'b->d', 'e']
        start = 'b'
        stop = 'd'
        expected = [['b', 'd']]
        self.path_helper(spec, start, stop, expected)

        # a single node
        spec = ['a']
        start = 'a'
        stop = 'a'
        expected = [['a']]
        self.path_helper(spec, start, stop, expected)

        # graph with a merged branch
        spec = ['a->b->c', 'b->d', 'c->e d->e']
        start = 'a'
        stop = 'e'
        expected = [['a', 'b', 'c', 'e'], ['a', 'b', 'd', 'e']]
        self.path_helper(spec, start, stop, expected)

        # graph with a cycle
        spec = ['a->b->c->b', 'b->d', 'e']
        start = 'a'
        stop = 'c'
        expected = [['a', 'b', 'c']]
        self.path_helper(spec, start, stop, expected)

        # a complicated graph
        spec = ['a->b->d', 'a->c->b->d', 'c->a->d']
        start = 'c'
        stop = 'd'
        expected = [['c', 'b', 'd'], ['c', 'a', 'd'], ['c', 'a', 'b', 'd']]
        self.path_helper(spec, start, stop, expected)


if __name__ == '__main__':
    unittest.main()
