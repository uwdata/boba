#!/usr/bin/env python3

# Ugly hack to allow import from the root folder
import sys
import os
sys.path.insert(0, os.path.abspath('..'))

import unittest
import json
from src.decisionparser import DecisionParser


class TestDecisionParser(unittest.TestCase):

    def test_id_syntax(self):
        # valid identifiers
        self.assertTrue(DecisionParser._is_id('my_var'))
        self.assertTrue(DecisionParser._is_id('A1'))
        self.assertTrue(DecisionParser._is_id('a1b'))

        # invalid identifiers
        self.assertFalse(DecisionParser._is_id('_start'))
        self.assertFalse(DecisionParser._is_id('1b'))
        self.assertFalse(DecisionParser._is_id(' A'))

    def test_read_json(self):
        with open('./specs/spec-good.json', 'rb') as f:
            spec = json.load(f)
        dp = DecisionParser(spec)
        ds = dp.read_decisions()
        self.assertListEqual(list(ds.keys()), ['a', 'b'])
        self.assertEqual(ds['a'].desc, 'outlier')
        self.assertEqual(ds['b'].desc, 'Decision b')

    def test_parse_code(self):
        with open('./specs/spec-good.json', 'rb') as f:
            spec = json.load(f)
        dp = DecisionParser(spec)
        dp.read_decisions()

        line = ''
        vs, codes = dp.parse_code(line)
        self.assertListEqual(vs, [])
        self.assertListEqual(codes, [line])

        line = '    my fav'
        vs, codes = dp.parse_code(line)
        self.assertListEqual(vs, [])
        self.assertListEqual(codes, [line])

        line = "\t this is '{{a}}' v'{{a}}'riable"
        vs, codes = dp.parse_code(line)
        self.assertListEqual(vs, ['a', 'a'])
        self.assertListEqual(codes, ["\t this is '{{a}}'", " v'{{a}}'", 'riable'])


if __name__ == '__main__':
    unittest.main()
