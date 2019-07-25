#!/usr/bin/env python3

# Ugly hack to allow import from the root folder
import sys
import os
sys.path.insert(0, os.path.abspath('..'))

import unittest
from unittest.mock import patch
import io
from src.parser import Parser


def _print_code(ps):
    for b in ps.blocks:
        bl = ps.blocks[b]
        print('-' * 10, '  ({}) {}  '.format(bl.id, bl.name), '-' * 10)
        print(bl.code)


class TestParser(unittest.TestCase):

    # --- code gen ---
    # TODO: more tests
    def test_code_gen(self):
        base = '../example/simple/'
        ps = Parser(base+'script_annotated.py', base+'spec.json', base)
        ps._parse_blocks()
        ps._parse_graph()
        ps._code_gen()
        ps._write_csv()
        self.assertEqual(ps.counter, 6)

    # --- parse blocks ---
    def test_parse_blocks(self):
        base = '../example/simple/'
        ps = Parser(base+'script_annotated.py', base+'spec.json')
        ps._parse_blocks()
        self.assertListEqual([*ps.blocks], ['_start', 'A', 'B', 'C1', 'C2'])

    def test_script_1(self):
        base = './specs/'
        ps = Parser(base+'script1.py', base+'spec-good.json')
        ps._parse_blocks()
        self.assertListEqual([*ps.blocks], ['a', 'b', 'c'])

    def test_script_2(self):
        base = './specs/'
        ps = Parser(base+'script2.py', base+'spec-good.json')
        ps._parse_blocks()
        self.assertListEqual([*ps.blocks], ['_start', 'a', 'b', 'c'])

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_script_3(self, stdout):
        base = './specs/'
        ps = Parser(base+'script3.py', base+'spec-good.json')
        with self.assertRaises(SystemExit):
            ps._parse_blocks()
        self.assertRegex(stdout.getvalue(), r'Cannot find "\("')

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_script_4(self, stdout):
        base = './specs/'
        ps = Parser(base+'script4.py', base+'spec-good.json')
        with self.assertRaises(SystemExit):
            ps._parse_blocks()
        self.assertRegex(stdout.getvalue(), '(?i)duplicated')

    # --- parse graph ---
    def test_spec_good(self):
        base = '../example/simple/'
        ps = Parser(base+'script_annotated.py', base+'spec.json')
        ps._parse_blocks()
        ps._parse_graph()

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_spec_empty(self, stdout):
        base = './specs/'
        ps = Parser(base+'script1.py', base+'spec-empty.json')
        with self.assertRaises(SystemExit):
            ps._parse_graph()
        self.assertRegex(stdout.getvalue(), 'Cannot find "graph" in json')

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_spec_bad_graph(self, stdout):
        base = './specs/'
        ps = Parser(base+'script1.py', base+'spec-bad-graph.json')
        with self.assertRaises(SystemExit):
            ps._parse_graph()
        self.assertRegex(stdout.getvalue(), 'Cannot find a target node')

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_spec_cyclic_graph(self, stdout):
        base = './specs/'
        ps = Parser(base + 'script1.py', base + 'spec-cyclic-graph.json')
        with self.assertRaises(SystemExit):
            ps._parse_blocks()
            ps._parse_graph()
        self.assertRegex(stdout.getvalue(), 'Cannot find any starting node')


if __name__ == '__main__':
    unittest.main()
