#!/usr/bin/env python3

import json
from src.blockparser import BlockParser
import src.util as util
from dataclasses import dataclass


@dataclass
class Block:
    code: str = ''
    id: str = ''
    name: str = ''


class Parser:

    """ Parse everything """

    def __init__(self, f1, f2):
        self.fn_script = f1
        self.fn_spec = f2
        self.blocks = {}

        # read spec
        with open(f2, 'rb') as f:
            self.spec = json.load(f)

    def _throw(self, msg):
        util.print_fail(msg)
        exit(1)

    def _throw_parse_error(self, msg):
        prefix = 'In parsing file "{}":\n\t'.format(self.fn_script)
        self._throw(prefix + msg)

    def _add_block(self, block):
        # ignore empty block
        if block.id == '' and block.code == '':
            return

        # handle unnamed block
        if block.id == '':
            block.id = '_start' if len(self.blocks) == 0 else '_end'

        # check if id exists
        if block.id in self.blocks:
            err = 'Duplicated code block ID "{}"'.format(block.id)
            self._throw_parse_error(err)
        self.blocks[block.id] = block

    def _parse_blocks(self):
        bl = Block()

        with open(self.fn_script, 'r') as f:
            for line in f:
                if BlockParser.can_parse(line):
                    # end of the last block
                    self._add_block(bl)

                    # parse the metadata
                    res = BlockParser(line).parse()
                    if not res['success']:
                        self._throw_parse_error(res['err'])

                    # create a new block
                    bl = Block('', res['id'], res['name'])
                else:
                    bl.code += line

            # add the last block
            self._add_block(bl)
