#!/usr/bin/env python3

# Ugly hack to allow import from the root folder
import sys
import os
sys.path.insert(0, os.path.abspath('..'))

import unittest
from boba.blockparser import BlockParser, ParseError


class TestBlockParser(unittest.TestCase):

    def test_steps(self):
        line = '# --- (A) remove_outlier'
        self.assertTrue(BlockParser.can_parse(line))
        bp = BlockParser(line)
        self.assertEqual(bp.i, 0)
        bp._read_next()
        self.assertEqual(bp.i, 5)
        bp._read_next()
        self.assertEqual(bp.i, 9)
        bp._read_next()
        self.assertEqual(bp.i, len(line))
        bp._read_next()
        self.assertEqual(bp.i, len(line))

    def test_can_parse(self):
        self.assertTrue(BlockParser.can_parse('   # --- comment'))
        self.assertTrue(BlockParser.can_parse('   # ---comment   '))
        self.assertFalse(BlockParser.can_parse('#--- comment'))
        self.assertFalse(BlockParser.can_parse('# --'))

    def test_syntax(self):
        line = '# --- (A) remove_outlier'
        self.assertTrue(BlockParser.can_parse(line))
        bid, par, opt = BlockParser(line).parse()
        self.assertEqual(bid, 'A:remove_outlier')
        self.assertEqual(par, 'A')
        self.assertEqual(opt, 'remove_outlier')

        line = '# --- (A) remove outlier'
        with self.assertRaises(ParseError):
            BlockParser(line).parse()

        line = '# --- ((A)) name'
        with self.assertRaises(ParseError):
            BlockParser(line).parse()

        line = '# --- ( A)'
        bid, par, opt = BlockParser(line).parse()
        self.assertEqual(bid, 'A')
        self.assertEqual(par, '')
        self.assertEqual(opt, '')

    def test_whitespace(self):
        line = '\t\t# --- (A) name'
        bid, par, opt = BlockParser(line).parse()
        self.assertEqual(par, 'A')
        self.assertEqual(opt, 'name')

        line = '    # --- (A) name    \t'
        bid, par, opt = BlockParser(line).parse()
        self.assertEqual(par, 'A')
        self.assertEqual(opt, 'name')

        line = '# ---(A)socrowded'
        bid, par, opt = BlockParser(line).parse()
        self.assertEqual(par, 'A')
        self.assertEqual(opt, 'socrowded')

    def test_id_syntax(self):
        line = '# --- (C1)'
        bid, par, opt = BlockParser(line).parse()
        self.assertEqual(bid, 'C1')

        line = '# --- (aXa) '
        bid, par, opt = BlockParser(line).parse()
        self.assertEqual(bid, 'aXa')

        line = '# --- (my_variable) \t'
        bid, par, opt = BlockParser(line).parse()
        self.assertEqual(bid, 'my_variable')

        # ID must start with a letter
        line = '# --- (12)'
        with self.assertRaisesRegex(ParseError, '(?i)invalid identifier'):
            BlockParser(line).parse()

        line = '# --- (_start)'
        with self.assertRaisesRegex(ParseError, '(?i)invalid identifier'):
            BlockParser(line).parse()


if __name__ == '__main__':
    unittest.main()
