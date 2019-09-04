#!/usr/bin/env python3

# Ugly hack to allow import from the root folder
import sys
import os
sys.path.insert(0, os.path.abspath('..'))

import unittest
import json
from boba.decisionparser import DecisionParser


def abs_path(rel_path):
    return os.path.join(os.path.dirname(__file__), rel_path)


class TestDecisionParser(unittest.TestCase):

    def test_id_syntax(self):
        # valid identifiers
        self.assertTrue(DecisionParser._is_id_token('my_var'))
        self.assertTrue(DecisionParser._is_id_token('A1'))
        self.assertTrue(DecisionParser._is_id_token('a1b'))

        # invalid identifiers
        self.assertFalse(DecisionParser._is_id_token('_start'))
        self.assertFalse(DecisionParser._is_id_token('1b'))
        self.assertFalse(DecisionParser._is_id_token(' A'))

    def test_read_json(self):
        with open(abs_path('./specs/spec-good.json'), 'rb') as f:
            spec = json.load(f)
        dp = DecisionParser(spec)
        ds = dp.read_decisions()
        self.assertListEqual(list(ds.keys()), ['a', 'b'])
        self.assertEqual(ds['a'].desc, 'outlier')
        self.assertEqual(ds['b'].desc, 'Decision b')

    def test_parse_code(self):
        with open(abs_path('./specs/spec-good.json'), 'rb') as f:
            spec = json.load(f)
        dp = DecisionParser(spec)
        dp.read_decisions()

        line = ''
        vs, codes = dp.parse_code(line)
        self.assertListEqual(vs, [])
        self.assertListEqual(codes, [line])

        # valid pattern, no variable
        line = '{{}}'
        vs, codes = dp.parse_code(line)
        self.assertListEqual(vs, [])
        self.assertListEqual(codes, [line])

        # valid pattern {{a}}
        line = "\t this is {{a}} v{{a}}riable"
        vs, codes = dp.parse_code(line)
        self.assertListEqual(vs, ['a', 'a'])
        self.assertListEqual(codes, ["\t this is {{a}}", " v{{a}}", 'riable'])

        # invalid id start {{_a}}
        line = '{{_a}}'
        vs, codes = dp.parse_code(line)
        self.assertListEqual(vs, [])

        # valid pattern, back to back
        line = '{{a}}{{b}}'
        vs, codes = dp.parse_code(line)
        self.assertListEqual(vs, ['a', 'b'])
        self.assertListEqual(codes, ['{{a}}', '{{b}}', ''])

        # back to back, too few separators
        line = '{{a}}{a}}'
        vs, codes = dp.parse_code(line)
        self.assertListEqual(vs, ['a'])
        self.assertListEqual(codes, ['{{a}}', '{a}}'])

        # back to back, extra separators
        line = '{{a}}{{{b}}'
        vs, codes = dp.parse_code(line)
        self.assertListEqual(vs, ['a', 'b'])
        self.assertListEqual(codes, ['{{a}}', '{{{b}}', ''])

        # back to back, extra separators
        line = '{{a}}}{{b}}'
        vs, codes = dp.parse_code(line)
        self.assertListEqual(vs, ['a', 'b'])
        self.assertListEqual(codes, ['{{a}}', '}{{b}}', ''])

        # broken + valid
        line = '{{a}{{a}}'
        vs, codes = dp.parse_code(line)
        self.assertListEqual(vs, ['a'])
        self.assertListEqual(codes, [line, ''])

        # broken + valid
        line = '{{{{a}}'
        vs, codes = dp.parse_code(line)
        self.assertListEqual(vs, ['a'])
        self.assertListEqual(codes, [line, ''])

        # no pattern
        line = "'In parsing file \"{}\":\n'.format(self.fn_script)"
        vs, codes = dp.parse_code(line)
        self.assertListEqual(vs, [])
        self.assertListEqual(codes, [line])

        # missing closing syntax
        line = '{{a}'
        vs, codes = dp.parse_code(line)
        self.assertListEqual(vs, [])
        self.assertListEqual(codes, [line])

        # missing closing syntax
        line = '{{a'
        vs, codes = dp.parse_code(line)
        self.assertListEqual(vs, [])
        self.assertListEqual(codes, [line])


if __name__ == '__main__':
    unittest.main()
