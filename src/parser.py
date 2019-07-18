#!/usr/bin/env python3

import json
from dataclasses import dataclass, field
from typing import List

from src.blockparser import BlockParser
from src.graphparser import GraphParser
from src.graphanalyzer import GraphAnalyzer, InvalidGraphError
from src.decisionparser import DecisionParser, InvalidSyntaxError
import src.util as util


@dataclass
class Block:
    code: str = ''
    id: str = ''
    name: str = ''
    decisions: List = field(default_factory=lambda: [])


class Parser:

    """ Parse everything """

    def __init__(self, f1, f2):
        self.fn_script = f1
        self.fn_spec = f2
        self.blocks = {}
        self.decisions = {}
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
        dp = DecisionParser(self.spec)
        try:
            self.decisions = dp.read_decisions()
        except InvalidSyntaxError as e:
            self._throw_spec_error(e.args[0])

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
                    bl = Block('', res['id'], res['name'], [])
                else:
                    # match any decision variables
                    try:
                        bl.decisions.extend(dp.parse_code(line))
                    except InvalidSyntaxError as e:
                        msg = 'At line "{}"\n\t{}'.format(line, e.args[0])
                        self._throw_parse_error(msg)

                    # add to the current block
                    bl.code += line

            # add the last block
            self._add_block(bl)

    def _match_nodes(self, nodes):
        # nodes in spec and script should match
        for nd in nodes:
            if nd not in self.blocks:
                self._throw_spec_error('Cannot find matching node "{}" in script'.format(nd))

        for nd in self.blocks:
            # ignore special nodes inserted by us
            if not nd.startswith('_') and nd not in nodes:
                util.print_warn('Cannot find matching node "{}" in graph spec'.format(nd))

    def _parse_graph(self):
        if 'graph' not in self.spec:
            self._throw_spec_error('Cannot find "graph" in json')

        res = GraphParser(self.spec['graph']).parse()

        if not res['success']:
            self._throw_spec_error(res['err'])

        self._match_nodes(res['nodes'])
        try:
            self.paths = GraphAnalyzer(res['nodes'], res['edges']).analyze()
        except InvalidGraphError as e:
            self._throw_spec_error(e.args[0])

    def _code_gen(self):
        # TODO: remember to prepend _start to every output script!
        pass

    def _main(self):
        self._parse_blocks()
        self._parse_graph()
        self._code_gen()
