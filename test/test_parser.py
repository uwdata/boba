#!/usr/bin/env python3

# Ugly hack to allow import from the root folder
import sys
import os
sys.path.insert(0, os.path.abspath('..'))

import unittest
import pandas
from unittest.mock import patch
import io
from boba.parser import Parser

FIRST_SCRIPT = 'multiverse/code/universe_1.py'


def _print_code(ps):
    for b in ps.blocks:
        bl = ps.blocks[b]
        print('-' * 10, '  ({}) {}  '.format(bl.id, bl.name), '-' * 10)
        for c in bl.chunks:
            print(c[1], end='')


def abs_path(rel_path):
    return os.path.join(os.path.dirname(__file__), rel_path)


def verify_summary_csv(summary, expected_values):
    data = pandas.read_csv(summary)
    for key, val in expected_values.items():
        if key not in data:
            return False

        values = data[key].to_list()
        if not all(elem == val for elem in values):
            return False

    return True


class FilterTestCase:
    def __init__(self, folder, script):
        self.folder = folder
        self.script = script
        self.cases = []

    def add_case(self, filt, expected=None):
        if expected is None:
            self.cases.append((filt, filt))
        else:
            self.cases.append((filt, expected))


class TestParser(unittest.TestCase):

    # --- code gen ---
    # a simple synthetic example
    def test_code_gen(self):
        base = abs_path('../example/simple/')
        ps = Parser(base+'template.py', base)
        ps.main(verbose=False)
        self.assertEqual(ps.wrangler.counter, 6)

    # a complex example
    def test_codegen_reading(self):
        base = abs_path('../example/reading/python/')
        Parser(base+'template.py', base).main(verbose=False)

    # another complex example
    def test_codegen_fertility(self):
        base = abs_path('../example/fertility/')
        ps = Parser(base+'template.py', base)
        ps.main(verbose=False)
        self.assertEqual(ps.wrangler.counter, 120)

    # an example written in R
    def test_r(self):
        base = abs_path('../example/fertility_r/')
        ps = Parser(base+'template.R', base)
        ps.main(verbose=False)
        self.assertEqual(ps.wrangler.counter, 120)

    # the spec has one decision and no graphs; should work
    def test_codegen_decision_only(self):
        base = abs_path('./specs/')
        sc = 'script-no-graph.py'
        ps = Parser(base+sc, base)
        ps.main(verbose=False)

        # compare file content
        with open(base+FIRST_SCRIPT, 'r') as f:
            actual = f.read()
        with open(base+sc, 'r') as f:
            lines = f.readlines()[7:]
            expected = ''.join(lines).replace('{{a}}', '1')
        self.assertEqual(actual, expected)

    # the spec has a graph and no decisions; should work
    def test_codegen_graph_only(self):
        base = abs_path('./specs/')
        ps = Parser(base + 'script1-good.py', base)
        ps.main(verbose=False)

        # compare file content
        with open(os.path.join(base, FIRST_SCRIPT), 'r') as f:
            actual = f.read()
        with open(base+'script1.py', 'r') as f:
            lines = f.read().split('\n')
            expected = ''
            for l in lines:
                if not l.strip().startswith('# --- '):
                    expected += l + '\n'
        self.assertEqual(actual.strip(), expected.strip())

    # the template contains decisions, but spec does not have corresponding def
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_codegen_missing_decision(self, stdout):
        base = abs_path('./specs/')
        sc = 'script-no-graph-empty.py'
        with self.assertRaises(SystemExit):
            Parser(base+sc, base)
        self.assertRegex(stdout.getvalue(), 'Cannot find matching variable')

    # --- parse blocks ---
    def test_parse_blocks(self):
        base = abs_path('../example/simple/')
        ps = Parser(base+'template.py')
        self.assertSetEqual(set(ps.code_parser.blocks.keys()), {'_start', 'A:std', 'A:iqr', 'B'})
        self.assertListEqual(['_start', 'A', 'B'], ps.code_parser.order)

    def test_script_2(self):
        ps = Parser(abs_path('./specs/')+'script2.py')
        self.assertListEqual([*ps.code_parser.blocks], ['_start', 'A', 'B', 'C'])

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_script_3(self, stdout):
        with self.assertRaises(SystemExit):
            Parser(abs_path('./specs/') + 'script2-syntax.py')
        self.assertRegex(stdout.getvalue(), r'Cannot find "\("')

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_script_4(self, stdout):
        with self.assertRaises(SystemExit):
            Parser(abs_path('./specs/')+'script2-dup.py')
        self.assertRegex(stdout.getvalue(), '(?i)duplicated')

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_script_5(self, stdout):
        with self.assertRaises(SystemExit):
            Parser(abs_path('./specs/')+'script2-dup-var.py')
        self.assertRegex(stdout.getvalue(), '(?i)name')

    def test_script_6(self):
        base = abs_path('./specs/')
        ps = Parser(base+'script2-block-param.py', base)
        ps.main(verbose=False)
        self.assertEqual(ps.wrangler.counter, 9)

    # --- constraints ---
    def test_constraint_1(self):
        """ Block options depend on block parameter """
        base = abs_path('./specs/')
        ps = Parser(base+'script3-1.py', base)
        ps.main(verbose=False)
        self.assertEqual(ps.wrangler.counter, 6)

    def test_constraint_2(self):
        """ Block parameter depends on block parameter """
        base = abs_path('./specs/')
        ps = Parser(base+'script3-2.py', base)
        ps.main(verbose=False)
        self.assertEqual(ps.wrangler.counter, 3)

    def test_constraint_3(self):
        """ Normal block depends on block parameter """
        base = abs_path('./specs/')
        ps = Parser(base+'script3-3.py', base)
        ps.main(verbose=False)
        self.assertEqual(ps.wrangler.counter, 8)

    def test_constraint_4(self):
        """ Variable depends on variable """
        base = abs_path('./specs/')
        ps = Parser(base + 'script3-4.py', base)
        ps.main(verbose=False)
        self.assertEqual(ps.wrangler.counter, 4)

        # then, test index
        ps = Parser(base + 'script3-4.py', base)
        ps.spec['constraints'] = [
            {"variable": "b", "index": 1, "condition": "a.index == 0"},
            {"variable": "b", "index": 0, "condition": "a == else"}]
        ps._parse_constraints()
        ps.main(verbose=False)
        self.assertEqual(ps.wrangler.counter, 4)

    def test_constraint_5(self):
        """ Skip a block """
        # first, skip a normal block
        base = abs_path('./specs/')
        ps = Parser(base+'script3-5.py', base)
        ps.main(verbose=False)
        self.assertEqual(ps.wrangler.counter, 8)

        # then, skip a decision block
        ps = Parser(base+'script3-5.py', base)
        ps.spec['constraints'] = [{"block": "B", "skippable": True, "condition": "a == if"}]
        ps._parse_constraints()
        ps.main(verbose=False)
        self.assertEqual(ps.wrangler.counter, 6)

    def test_constraint_7(self):
        """ Linked decisions """
        base = abs_path('./specs/')
        ps = Parser(base+'script3-7.py', base)
        ps.main(verbose=False)
        self.assertEqual(ps.wrangler.counter, 10)

    def test_constraint_inline(self):
        """ Inline constraints """
        base = abs_path('./specs/')
        ps = Parser(base+'script-inline-constraints.py', base)
        ps.main(verbose=False)
        self.assertEqual(ps.wrangler.counter, 2)

    # --- adg ---
    @staticmethod
    def _edge_to_set(edges):
        res = {}
        for k in edges:
            res[k] = set(edges[k])
        return res

    def test_adg(self):
        base = abs_path('./specs/')
        ps = Parser(base+'script4-1.py', base)
        ps.adg.create(ps.code_parser.blocks)
        self.assertSetEqual(ps.adg.nodes, {'b', 'C', 'B', 'A'})
        expected = {'B': {'b', 'C'}, 'A': {'B'}}
        self.assertDictEqual(self._edge_to_set(ps.adg.edges), expected)

    def test_adg_code_graph(self):
        base = abs_path('./specs/')
        ps = Parser(base+'script4-2.py', base)
        ps.adg.create(ps.code_parser.blocks)
        self.assertSetEqual(ps.adg.nodes, {'C', 'B', 'a', 'A', 'b', 'D'})
        expected = {'b': {'D', 'C'}, 'B': {'D', 'b', 'C'}, 'a': {'B'}, 'A': {'a'}}
        self.assertDictEqual(self._edge_to_set(ps.adg.edges), expected)
        expected ={'b': {'D', 'C'}, 'B': {'D', 'b', 'C'}}
        self.assertDictEqual(self._edge_to_set(ps.adg.proc_edges), expected)

    def test_adg_link(self):
        base = abs_path('./specs/')
        ps = Parser(base+'script4-3.py', base)
        ps.adg.create(ps.code_parser.blocks)
        self.assertSetEqual(ps.adg.nodes, {'a', 'B'})
        self.assertDictEqual(ps.adg.edges, {'a': ['B']})

    # --- parse graph ---
    def test_spec_good(self):
        base = abs_path('../example/simple/')
        ps = Parser(base+'template.py')
        expected = [['_start', 'A:std', 'B'], ['_start', 'A:iqr', 'B']]
        expected = set([','.join(p) for p in expected])
        self.assertSetEqual(set([','.join(p) for p in ps.paths]), expected)

    def test_spec_empty(self):
        base = abs_path('./specs/')
        ps = Parser(base+'script1.py')
        self.assertListEqual(ps.paths, [['A', 'B', 'C']])

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_spec_bad_graph(self, stdout):
        base = abs_path('./specs/')
        with self.assertRaises(SystemExit):
            Parser(base+'script1-bad-graph.py')
        self.assertRegex(stdout.getvalue(), 'Cannot find a target node')

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_spec_cyclic_graph(self, stdout):
        base = abs_path('./specs/')
        with self.assertRaises(SystemExit):
            Parser(base + 'script1-cyclic-graph.py')
        self.assertRegex(stdout.getvalue(), 'Cannot find any starting node')

    def test_decision_filter(self):
        base = abs_path('../example')

        filts = []

        filt = FilterTestCase('simple', 'template.py')
        filt.add_case({'path_filter' : {'A' : 'iqr'}}, {'A' : 'iqr'})
        filt.add_case({'cutoff' : 2.5})
        filt.add_case({'cutoff' : 3})
        filt.add_case({'path_filter' : {'A' : 'std'}, 'cutoff' : 2}, {'A' : 'std', 'cutoff' : 2})
        filts.append(filt)

        filt = FilterTestCase('simple_cont', 'template.py')
        filt.add_case({'path_filter' : {'A' : 'iqr'}}, {'A' : 'iqr'})
        filt.add_case({'cutoff' : 1.0})
        filt.add_case({'cutoff' : 1.5})
        filt.add_case({'cutoff' : 2.0})
        filt.add_case({'cutoff' : 2.5})
        filt.add_case({'cutoff' : 3.0})
        filt.add_case({'path_filter' : {'A' : 'std'}, 'cutoff' : 2.25}, {'A' : 'std', 'cutoff' : 2.25})
        filt.add_case({'path_filter' : {'A' : 'iqr'}, 'cutoff' : 1.0}, {'A' : 'iqr', 'cutoff' : 1.0})
        filt.add_case({'path_filter' : {'A' : 'iqr'}, 'cutoff' : 3.0}, {'A' : 'iqr', 'cutoff' : 3.0})
        filts.append(filt)

        for filt in filts:
            ps = Parser(base + '/' + filt.folder + '/' + filt.script, base + '/' + filt.folder)
            for i in range(0, len(filt.cases)):
                f = filt.cases[i]
                ps.main(f[0], verbose=False)
                csv = base + '/' + filt.folder + '/multiverse/summary.csv'
                if not verify_summary_csv(csv, f[1]):
                    msg = 'failed on test case ' + str(i) + ' of ' + filt.folder + '\n'
                    msg += 'filter was: ' + str(f[0]) + ', expected ' + str(f[1]) + '\n'
                    self.fail(msg)

    def test_decision_filter_err(self):
        base = abs_path('../example')

        filts = []

        filt = FilterTestCase('simple', 'template.py')
        filt.add_case({'path_filter' : {'C' : 'iqr'}}, ValueError)
        filt.add_case({'path_filter' : {'A' : 'bad'}}, ValueError)
        filt.add_case({'cutoff' : 'bad data'}, ValueError)
        filt.add_case({'cutoff' : 1}, ValueError)
        filts.append(filt)

        filt = FilterTestCase('simple_cont', 'template.py')
        filt.add_case({'path_filter' : {'C' : 'iqr'}}, ValueError)
        filt.add_case({'path_filter' : {'A' : 'bad'}}, ValueError)
        filt.add_case({'cutoff' : 'bad data'}, ValueError)
        filt.add_case({'cutoff' : 5.0}, ValueError)
        filts.append(filt)

        for filt in filts:
            ps = Parser(base + '/' + filt.folder + '/' + filt.script, base + '/' + filt.folder)
            for i in range(0, len(filt.cases)):
                f = filt.cases[i]
                thrown = False
                msg = 'failed on test case ' + str(i) + ' of ' + filt.folder + '\n'
                try:
                    ps.main(f[0], verbose=False)
                except Exception as e:
                    msg += 'filter was: ' + str(f[0]) + ', expected ' + str(f[1]) + ', recieved ' + str(e) + '\n'
                    if not isinstance(e, f[1]):
                        self.fail(msg)

                    thrown = True
                
                if not thrown:
                    msg += 'no exception was thrown'
                    self.fail(msg)


if __name__ == '__main__':
    unittest.main()
