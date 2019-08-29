# -*- coding: utf-8 -*-

from .baseparser import BaseParser, ParseError

kw = '# ---'


class BlockParser(BaseParser):
    """
    Parse the metadata of a code block, which must have the structure:
        # --- (ID) name of the block
    """

    def __init__(self, line):
        super(BlockParser, self).__init__(line)

        self.state = 0
        self.parsed_id = ''
        self.parsed_name = ''

    @staticmethod
    def can_parse(line):
        return line.lstrip().startswith(kw)

    def parse(self):
        while not self._is_end():
            self._read_next()
        return self.parsed_id, self.parsed_name

    def _read_next(self):
        self._read_while(BlockParser._is_whitespace)
        if self._is_end():
            return

        if self.state == 0:
            self._read_kw()
        elif self.state == 1:
            self._read_id()
        else:
            self._read_name()

    def _end(self):
        self.i = len(self.line)  # stop parsing

    def _throw(self, msg):
        err = 'At character {} of "{}":\n\t{}'.format(self.i+1, self.line, msg)
        raise ParseError(err)

    def _remaining(self):
        return self.line[self.i:]

    def _read_kw(self):
        if self._remaining().startswith(kw):
            self.i += len(kw)
            self.state += 1
        else:
            self._throw('expected {}'.format(kw))

    def _read_id(self):
        # open paren
        if self._peek_char() != '(':
            self._throw('Cannot find "("')
        self._next_char()

        # read the actual identifier
        ch = self._peek_char()
        if not self._is_id_start(ch):
            self._throw('Invalid identifier start character {}'.format(ch))

        self.parsed_id = self._read_while(self._is_id)

        # close paren
        if self._peek_char() != ')':
            self._throw('Cannot find ")"')
        self._next_char()
        self.state += 1

    def _read_name(self):
        self.parsed_name = self._remaining().strip()
        self._end()
