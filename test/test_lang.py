#!/usr/bin/env python3

# Ugly hack to allow import from the root folder
import shutil
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
        print('here')
        fn(args)
    except SystemExit as e:
        if e.code != 0:
            raise RuntimeError('nonzero exit code: ' + str(e))

    sys.stdout = stdout
    null.close()

class TestLang(unittest.TestCase):
    def test_c(self):
        folder = 'test/test_c'
        script = os.path.join(folder, 'template.c')
        out = folder
        multiverse = os.path.join(folder, 'multiverse')

        run_click(compile, ['-s', script, '--out', folder])

        file_base = os.path.join(out, 'multiverse/code/universe_')
        ext = '.c'
        for i in range(1, 4):
            f = file_base + str(i) + ext
            if not os.path.isfile(file_base + str(i) + ext):
                self.fail('did not generate universe ' + f)

        run_click(run, ['--dir', multiverse, '-a'])
        
        file_base = os.path.join(out, 'multiverse/boba_logs/log_')
        ext = '.txt'
        for i in range(1, 4):
            fn = file_base + str(i) + ext
            if not os.path.isfile(fn):
                self.fail('did not generate log ' + str(i))

            with open(fn) as f:
                read = f.read()
                if read != 'hello from universe ' + str(i) + '\n':
                    self.fail('universe generated unexpected output "' + read + '"')

        shutil.rmtree(multiverse)
