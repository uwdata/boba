#!/usr/bin/env python3

# Ugly hack to allow import from the root folder
import sys
import os
sys.path.insert(0, os.path.abspath('..'))

import unittest
from src.parser import Parser


class TestParser(unittest.TestCase):

    def test_parse_blocks(self):
        base = '../example/simple/'
        ps = Parser(base+'script_annotated.py', base+'spec.json')
        ps._parse_blocks()
        self.assertEqual(len(ps.blocks), 5)
        for b in ps.blocks:
            bl = ps.blocks[b]
            self.assertNotEqual(bl.code, '')
            print('-'*10, '  ({}) {}  '.format(bl.id, bl.name), '-'*10)
            print(bl.code)


if __name__ == '__main__':
    unittest.main()
