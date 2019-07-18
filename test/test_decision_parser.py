#!/usr/bin/env python3

# Ugly hack to allow import from the root folder
import sys
import os
sys.path.insert(0, os.path.abspath('..'))

import unittest
from src.decisionparser import DecisionParser


class TestDecisionParser(unittest.TestCase):

    def test_read(self):
        # TODO
        pass


if __name__ == '__main__':
    unittest.main()
