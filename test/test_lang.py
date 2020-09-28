#!/usr/bin/env python3

# Ugly hack to allow import from the root folder
import click
import sys
import os
sys.path.insert(0, os.path.abspath('..'))

import unittest
from unittest.mock import patch
import io
from boba.cli import compile, run

from io import StringIO 
import sys

def run_click(fn, args):
    """ run a click function """

    stdout = sys.stdout
    null = open(os.devnull, 'w')
    sys.stdout = null

    try:
        fn(args)
    except SystemExit as e:
        if e.code != 0:
            raise RuntimeError('nonzero exit code: ' + str(e))

    sys.stdout = stdout
    null.close()

class TestLang(unittest.TestCase):
    def test_c(self):
        folder = 'test_c/'
        script = folder + 'template.c'
        out = folder

        run_click(compile, ['-s', script, '--out', folder])

        file_base = out + 'multiverse/code/universe_'
        ext = '.c'
        for i in range(1, 4):
            if not os.path.isfile(file_base + str(i) + ext):
                self.fail('did not generate universe ' + str(i))

        run_click(run, ['--dir', folder + 'multiverse/', '--all'])
        
        file_base = out + 'multiverse/boba_logs/log_'
        ext = '.txt'
        for i in range(1, 4):
            fn = file_base + str(i) + ext
            if not os.path.isfile(fn):
                self.fail('did not generate log ' + str(i))

            with open(fn) as f:
                read = f.read()
                if read != 'hello from universe ' + str(i) + '\n':
                    self.fail('universe generated unexpected output "' + read + '"')
