#!/usr/bin/env python3

# Ugly hack to allow import from the root folder
import sys
import os
sys.path.insert(0, os.path.abspath('..'))

import unittest
from src.blockparser import BlockParser


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
        bp = BlockParser(line)
        res = bp.parse()
        self.assertTrue(res['success'])
        self.assertEqual(res['id'], 'A')
        self.assertEqual(res['name'], 'remove outlier')

        line = '# --- ((A)) name'
        bp = BlockParser(line)
        res = bp.parse()
        self.assertFalse(res['success'])

        line = '# --- (A)'
        bp = BlockParser(line)
        res = bp.parse()
        self.assertTrue(res['success'])
        self.assertEqual(res['id'], 'A')
        self.assertEqual(res['name'], '')

    def test_whitespace(self):
        line = '\t\t# --- (A) name'
        bp = BlockParser(line)
        res = bp.parse()
        self.assertTrue(res['success'])
        self.assertEqual(res['id'], 'A')
        self.assertEqual(res['name'], 'name')

        line = '    # --- (A) name    \t'
        bp = BlockParser(line)
        res = bp.parse()
        self.assertTrue(res['success'])
        self.assertEqual(res['id'], 'A')
        self.assertEqual(res['name'], 'name')

        line = '# ---(A)socrowded'
        bp = BlockParser(line)
        res = bp.parse()
        self.assertTrue(res['success'])
        self.assertEqual(res['id'], 'A')
        self.assertEqual(res['name'], 'socrowded')

    def test_id_syntax(self):
        line = '# --- (C1) name'
        bp = BlockParser(line)
        res = bp.parse()
        self.assertTrue(res['success'])
        self.assertEqual(res['id'], 'C1')

        line = '# --- (aXa) name'
        bp = BlockParser(line)
        res = bp.parse()
        self.assertTrue(res['success'])
        self.assertEqual(res['id'], 'aXa')

        # underscore is not allowed
        line = '# --- (my_variable) name'
        bp = BlockParser(line)
        res = bp.parse()
        self.assertFalse(res['success'])

        # ID must start with a letter
        line = '# --- (12) name'
        bp = BlockParser(line)
        res = bp.parse()
        self.assertFalse(res['success'])


if __name__ == '__main__':
    unittest.main()
