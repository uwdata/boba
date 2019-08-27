#!/usr/bin/env python3

# Ugly hack to allow import from the root folder
import sys
import os
sys.path.insert(0, os.path.abspath('..'))

import unittest
from boba.blockparser import BlockParser, ParseError


class TestBlockParser(unittest.TestCase):

    def test_steps(self):
        line = '# --- (A) remove outlier'
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
        line = '# --- (A) remove outlier'
        self.assertTrue(BlockParser.can_parse(line))
        bid, bname = BlockParser(line).parse()
        self.assertEqual(bid, 'A')
        self.assertEqual(bname, 'remove outlier')

        line = '# --- ((A)) name'
        with self.assertRaises(ParseError):
            BlockParser(line).parse()

        line = '# --- (A)'
        bid, bname = BlockParser(line).parse()
        self.assertEqual(bid, 'A')
        self.assertEqual(bname, '')

    def test_whitespace(self):
        line = '\t\t# --- (A) name'
        bid, bname = BlockParser(line).parse()
        self.assertEqual(bid, 'A')
        self.assertEqual(bname, 'name')

        line = '    # --- (A) name    \t'
        bid, bname = BlockParser(line).parse()
        self.assertEqual(bid, 'A')
        self.assertEqual(bname, 'name')

        line = '# ---(A)socrowded'
        bid, bname = BlockParser(line).parse()
        self.assertEqual(bid, 'A')
        self.assertEqual(bname, 'socrowded')

    def test_id_syntax(self):
        line = '# --- (C1) name'
        bid, bname = BlockParser(line).parse()
        self.assertEqual(bid, 'C1')

        line = '# --- (aXa) name'
        bid, bname = BlockParser(line).parse()
        self.assertEqual(bid, 'aXa')

        line = '# --- (my_variable) name'
        bid, bname = BlockParser(line).parse()
        self.assertEqual(bid, 'my_variable')

        # ID must start with a letter
        line = '# --- (12) name'
        with self.assertRaisesRegex(ParseError, '(?i)invalid identifier'):
            BlockParser(line).parse()

        line = '# --- (_start) name'
        with self.assertRaisesRegex(ParseError, '(?i)invalid identifier'):
            BlockParser(line).parse()


if __name__ == '__main__':
    unittest.main()
