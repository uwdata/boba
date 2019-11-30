# Ugly hack to allow import from the root folder
import sys
import os
sys.path.insert(0, os.path.abspath('..'))

import unittest
from boba.constraintparser import ConstraintParser, ParseError
from boba.conditionparser import ConditionParser, TokenType
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

    def test_condition_parser(self):
        cond = ''
        ConditionParser(cond).parse()

        cond = 'a == b'
        _, decs = ConditionParser(cond).parse()
        self.assertListEqual(['a', 'b'], [d.value for d in decs])

        cond = 'a.index == 1'
        _, decs = ConditionParser(cond).parse()
        self.assertListEqual(['a', '1'], [d.value for d in decs])
        self.assertListEqual([TokenType.index_var, TokenType.number],
                             [d.type for d in decs])

        cond = 'a = 2.5'
        _, decs = ConditionParser(cond).parse()
        self.assertListEqual(['a', '2.5'], [d.value for d in decs])
        self.assertListEqual([TokenType.var, TokenType.number],
                             [d.type for d in decs])

        cond = 'a.index == b.index'  # .index not allowed on RHS, should fail
        with self.assertRaises(ParseError):
            ConditionParser(cond).parse()

        cond = '1 2 a b 4'  # we did not check other semantics ...
        ConditionParser(cond).parse()

    def test_condition_syntax(self):
        """ Does the condition code contain python syntax error? """

        base = abs_path('./specs/')
        ps = Parser(base+'script6.py', base+'spec-constraint-1.json')
        ps._parse_blocks()

        spec = {'constraints': [{'block': 'A', 'condition': 'B=b1'}]}
        with self.assertRaises(ParseError):
            read_wrapper(spec, ps)

        spec = {'constraints': [{'block': 'A', 'condition': 'B b1'}]}
        with self.assertRaises(ParseError):
            read_wrapper(spec, ps)

        spec = {'constraints': [{'block': 'A', 'condition': 'B == 2.5'}]}
        read_wrapper(spec, ps)

    def test_json_syntax(self):
        """ Test various possibilities to specify constraints in JSON """

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
        spec = {'constraints': [{'block': 'A', 'condition': 'B==b1'}]}
        read_wrapper(spec, ps)

        # block and option - should parse
        spec = {'constraints': [{'block': 'A', 'option': 'a1', 'condition': 'B==b1'}]}
        read_wrapper(spec, ps)

        # variable and option - should parse
        spec = {'constraints': [{'variable': 'a', 'option': '2.5', 'condition': 'B==b1'}]}
        read_wrapper(spec, ps)

        # weird option - should parse
        # fixme: {'option': '[1,2]'} will fail
        spec = {'constraints': [{'variable': 'c', 'option': '[1, 2]', 'condition': 'B==b1'}]}
        read_wrapper(spec, ps)

        # variables in condition do not match - should fail
        spec = {'constraints': [{'block': 'A', 'condition': 'H==b1'}]}
        with self.assertRaises(ParseError):
            read_wrapper(spec, ps)

        # variables in condition do not match - should fail
        spec = {'constraints': [{'block': 'A', 'condition': 'H.index==1'}]}
        with self.assertRaises(ParseError):
            read_wrapper(spec, ps)


if __name__ == '__main__':
    unittest.main()
