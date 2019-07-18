#!/usr/bin/env python3

import json
from dataclasses import dataclass
from src.blockparser import BlockParser
from src.graphparser import GraphParser
from src.graphanalyzer import GraphAnalyzer, InvalidGraphError
import src.util as util


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
        self.paths = []

        # read spec
        with open(f2, 'rb') as f:
            self.spec = json.load(f)

    def _throw(self, msg):
        util.print_fail(msg)
        exit(1)

    def _indent(self, msg):
        return '\n'.join(['\t' + l for l in msg.split('\n')])

    def _throw_parse_error(self, msg):
        prefix = 'In parsing file "{}":\n'.format(self.fn_script)
        self._throw(prefix + self._indent(msg))

    def _throw_spec_error(self, msg):
        prefix = 'In parsing file "{}":\n'.format(self.fn_spec)
        self._throw(prefix + self._indent(msg))

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

    def _check_nodes(self, nodes):
        # nodes in spec and script should match
        for nd in nodes:
            if nd not in self.blocks:
                self._throw_spec_error('Cannot find matching node "{}" in script'.format(nd))

        for nd in self.blocks:
            if nd not in nodes:
                util.print_warn('Cannot find matching node "{}" in graph spec'.format(nd))

    def _parse_graph(self):
        if 'graph' not in self.spec:
            self._throw_spec_error('Cannot find a graph specification')

        res = GraphParser(self.spec['graph']).parse()

        if not res['success']:
            self._throw_spec_error(res['err'])

        # TODO: how to deal with '_start'??
        self._check_nodes(res['nodes'])
        try:
            self.paths = GraphAnalyzer(res['nodes'], res['edges']).analyze()
        except InvalidGraphError as e:
            self._throw_spec_error(e.args[0])

    def parse(self):
        self._parse_blocks()
        self._parse_graph()
