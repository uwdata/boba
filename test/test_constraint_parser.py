# Ugly hack to allow import from the root folder
import sys
import os
sys.path.insert(0, os.path.abspath('..'))

import unittest
from boba.constraintparser import ConstraintParser, ParseError
from boba.parser import Parser


def abs_path(rel_path):
    return os.path.join(os.path.dirname(__file__), rel_path)


def read_wrapper(spec, ps):
    ConstraintParser(spec).read_constraints(ps.code_parser, ps.dec_parser)


class TestConstraintParser(unittest.TestCase):

    def test_read_json(self):
        base = abs_path('./specs/')
        ps = Parser(base+'script6.py', base+'spec-constraint-1.json')
        ps._parse_blocks()
        cp = ConstraintParser(ps.spec)
        cs = cp.read_constraints(ps.code_parser, ps.dec_parser)
        self.assertEqual(len(cs), 2)

    def test_json_syntax(self):
        base = abs_path('./specs/')
        ps = Parser(base+'script6.py', base+'spec-constraint-1.json')
        ps._parse_blocks()

        # empty - should parse
        spec = {}
        read_wrapper(spec, ps)

        # empty array - should parse
        spec = {'constraints': []}
        read_wrapper(spec, ps)

        # empty element - should fail
        spec = {'constraints': [{}]}
        with self.assertRaises(ParseError):
            read_wrapper(spec, ps)

        # no matching block - should fail
        spec = {'constraints': [{'block': 'a'}]}
        with self.assertRaises(ParseError):
            read_wrapper(spec, ps)

        # no matching variable - should fail
        spec = {'constraints': [{'variable': 'c'}]}
        with self.assertRaises(ParseError):
            read_wrapper(spec, ps)

        # loner option - should fail
        spec = {'constraints': [{'option': 'a1'}]}
        with self.assertRaises(ParseError):
            read_wrapper(spec, ps)

        # loner block - should parse
        spec = {'constraints': [{'block': 'A', 'condition': 'B=b1'}]}
        read_wrapper(spec, ps)

        # block and option - should parse
        spec = {'constraints': [{'block': 'A', 'option': 'a1', 'condition': 'B=b1'}]}
        read_wrapper(spec, ps)

        # variable and option - should parse
        spec = {'constraints': [{'variable': 'a', 'option': '2.5', 'condition': 'B=b1'}]}
        read_wrapper(spec, ps)

        # weird option - should parse
        # fixme: {'option': '[1,2]'} will fail
        spec = {'constraints': [{'variable': 'c', 'option': '[1, 2]', 'condition': 'B=b1'}]}
        read_wrapper(spec, ps)

if __name__ == '__main__':
    unittest.main()
