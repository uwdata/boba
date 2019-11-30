# -*- coding: utf-8 -*-

from dataclasses import dataclass, field
from typing import List

from .blocksyntaxparser import BlockSyntaxParser, ParseError


@dataclass
class Block:
    """
    A class for code blocks.

    id: unique identifier.
    parameter: parameter name, if the block is a decision.
    option: option name, if the block is a decision.
    chunks: code broken up at the boundaries of placeholder variables.
    """

    id: str = ''
    parameter: str = ''
    option: str = ''
    chunks: List = field(default_factory=lambda: [])


@dataclass
class Chunk:
    """A class for code chunks.
    A code chunk contains at most one placeholder variable.

    variable: the corresponding placeholder variable, if any.
    code: the code template proceeding the variable or the block boundary.
    """
    variable: str = ''
    code: str = ''


class CodeParser:
    def __init__(self):
        self.blocks = {}
        self.order = []

    @staticmethod
    def _get_block_name(block):
        """Get the ID of the block, ignoring options."""
        return block.id if block.parameter == '' else block.parameter

    def _add_block(self, block):
        """Add a block to our data structure."""
        # ignore empty block
        if block.id == '' and block.chunks[0].code == '':
            return

        # handle unnamed block
        if block.id == '':
            block.id = '_start' if len(self.blocks) == 0 else '_end'

        # check if id exists
        if block.id in self.blocks:
            err = 'Duplicated code block ID "{}"'.format(block.id)
            raise ParseError(err)

        # add to data structure
        self.blocks[block.id] = block
        bn = CodeParser._get_block_name(block)
        if bn not in self.order:
            self.order.append(bn)

    def get_block_names(self):
        """
        Get the ID of all blocks, ignoring options
        :return: a set of unique names
        """
        blocks = set()
        for b in self.blocks:
            bl = self.blocks[b]
            blocks.add(CodeParser._get_block_name(bl))
        return blocks

    def get_decisions(self):
        """
        Get a dict of all block-level decisions, where the key is the parameter
        and the value is a list of options.
        :return:
        """
        decs = {}
        for b in self.blocks:
            bl = self.blocks[b]
            if bl.parameter:
                p = bl.parameter
                if p in decs:
                    decs[p].append(bl.id)
                else:
                    decs[p] = [bl.id]
        return decs

    def parse(self, dec_parser, f):
        """ Make a pass over the template, parsing block declarations and
        placeholder variables inside the code."""
        code = ''
        bl = Block()

        for line in f:
            if BlockSyntaxParser.can_parse(line):
                # end of the previous block
                bl.chunks.append(Chunk('', code))
                code = ''
                self._add_block(bl)

                # parse the metadata and create a new block
                bp_id, par, opt = BlockSyntaxParser(line).parse()
                bl = Block(bp_id, par, opt, [])
            else:
                # match decision variables
                try:
                    vs, codes = dec_parser.parse_code(line)
                    if len(vs):
                        # chop into more chunks
                        # combine first chunk with previous code
                        bl.chunks.append(Chunk(vs[0], code + codes[0]))
                        for i in range(1, len(vs)):
                            bl.chunks.append(Chunk(vs[i], codes[i]))

                        # remaining code after the last matched variable
                        code = codes[-1]
                    else:
                        code += line
                except ParseError as e:
                    msg = 'At line "{}"\n\t{}'.format(line, e.args[0])
                    raise ParseError(msg)

        # add the last block
        bl.chunks.append(Chunk('', code))
        self._add_block(bl)
