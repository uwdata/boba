#!/usr/bin/env python3

# Ugly hack to allow import from the root folder
import sys
import os
import shutil
sys.path.insert(0, os.path.abspath('..'))

import unittest
from unittest.mock import patch
import io
from boba.parser import Parser

FIRST_SCRIPT = 'multiverse/code/universe_1.py'


def _print_code(ps):
    for b in ps.blocks:
        bl = ps.blocks[b]
        print('-' * 10, '  ({}) {}  '.format(bl.id, bl.name), '-' * 10)
        print(bl.code)


def abs_path(rel_path):
    return os.path.join(os.path.dirname(__file__), rel_path)


class TestParser(unittest.TestCase):

    # --- code gen ---
    # a simple synthetic example
    def test_code_gen(self):
        base = abs_path('../example/simple/')
        ps = Parser(base+'script_annotated.py', base+'spec.json', base)
        ps.main(verbose=False)
        self.assertEqual(ps.wrangler.counter, 6)

    # a complex example
    def test_codegen_reading(self):
        base = abs_path('../example/reading/python/')
        Parser(base+'script_annotated.py', base+'spec.json', base).main(verbose=False)

    # another complex example
    def test_codegen_fertility(self):
        base = abs_path('../example/fertility/')
        ps = Parser(base+'script_annotated.py', base+'spec.json', base)
        ps.main(verbose=False)
        self.assertEqual(ps.wrangler.counter, 120)

    # an example written in R
    def test_r(self):
        base = abs_path('../example/fertility_r/')
        ps = Parser(base+'template.R', base+'spec.json', base)
        ps.main(verbose=False)
        self.assertEqual(ps.wrangler.counter, 120)

    # the spec has one decision and no graphs; should work
    def test_codegen_decision_only(self):
        base = abs_path('./specs/')
        sc = 'script_no_graph.py'
        ps = Parser(base+sc, base+'spec-no-graph.json', base)
        ps.main(verbose=False)

        # compare file content
        with open(base+FIRST_SCRIPT, 'r') as f:
            actual = f.read()
        with open(base+sc, 'r') as f:
            expected = f.read().replace('{{a}}', '1')
        self.assertEqual(actual, expected)

        # clean up
        shutil.rmtree(base+'multiverse/')

    # the spec has a graph and no decisions; should work
    def test_codegen_graph_only(self):
        base = abs_path('./specs/')
        sc = 'script1.py'
        pout = abs_path('./output_no_dec')
        ps = Parser(base+sc, base+'spec-good.json', pout)
        ps.main(verbose=False)

        # compare file content
        with open(os.path.join(pout, FIRST_SCRIPT), 'r') as f:
            actual = f.read()
        with open(base+sc, 'r') as f:
            lines = f.read().split('\n')
            expected = ''
            for l in lines:
                if not l.strip().startswith('# --- '):
                    expected += l + '\n'
        self.assertEqual(actual.strip(), expected.strip())

        # clean up
        shutil.rmtree(pout)

    # the template contains decisions, but spec does not have corresponding def
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_codegen_missing_decision(self, stdout):
        base = abs_path('./specs/')
        sc = 'script_no_graph.py'
        ps = Parser(base+sc, base+'spec-empty.json', base)
        with self.assertRaises(SystemExit):
            ps.main(verbose=False)
        self.assertRegex(stdout.getvalue(), 'Cannot find the matching variable')

    # --- parse blocks ---
    def test_parse_blocks(self):
        base = abs_path('../example/simple/')
        ps = Parser(base+'script_annotated.py', base+'spec.json')
        ps._parse_blocks()
        self.assertListEqual([*ps.blocks], ['_start', 'A1', 'A2', 'B'])

    def test_script_1(self):
        base = abs_path('./specs/')
        ps = Parser(base+'script1.py', base+'spec-good.json')
        ps._parse_blocks()
        self.assertListEqual([*ps.blocks], ['a', 'b', 'c'])

    def test_script_2(self):
        base = abs_path('./specs/')
        ps = Parser(base+'script2.py', base+'spec-good.json')
        ps._parse_blocks()
        self.assertListEqual([*ps.blocks], ['_start', 'a', 'b', 'c'])

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_script_3(self, stdout):
        base = abs_path('./specs/')
        ps = Parser(base+'script3.py', base+'spec-good.json')
        with self.assertRaises(SystemExit):
            ps._parse_blocks()
        self.assertRegex(stdout.getvalue(), r'Cannot find "\("')

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_script_4(self, stdout):
        base = abs_path('./specs/')
        ps = Parser(base+'script4.py', base+'spec-good.json')
        with self.assertRaises(SystemExit):
            ps._parse_blocks()
        self.assertRegex(stdout.getvalue(), '(?i)duplicated')

    # --- parse graph ---
    def test_spec_good(self):
        base = abs_path('../example/simple/')
        ps = Parser(base+'script_annotated.py', base+'spec.json')
        ps._parse_blocks()
        ps._parse_graph()
        expected = [['_start', 'A1', 'B'], ['_start', 'A2', 'B']]
        expected = set([','.join(p) for p in expected])
        self.assertSetEqual(set([','.join(p) for p in ps.paths]), expected)

    def test_spec_empty(self):
        base = abs_path('./specs/')
        ps = Parser(base+'script1.py', base+'spec-empty.json')
        ps._parse_graph()
        self.assertListEqual(ps.paths, [])

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_spec_bad_graph(self, stdout):
        base = abs_path('./specs/')
        ps = Parser(base+'script1.py', base+'spec-bad-graph.json')
        with self.assertRaises(SystemExit):
            ps._parse_graph()
        self.assertRegex(stdout.getvalue(), 'Cannot find a target node')

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_spec_cyclic_graph(self, stdout):
        base = abs_path('./specs/')
        ps = Parser(base + 'script1.py', base + 'spec-cyclic-graph.json')
        with self.assertRaises(SystemExit):
            ps._parse_blocks()
            ps._parse_graph()
        self.assertRegex(stdout.getvalue(), 'Cannot find any starting node')


if __name__ == '__main__':
    unittest.main()
