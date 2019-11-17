# -*- coding: utf-8 -*-

from .baseparser import BaseParser, ParseError

kw = '# ---'


class BlockSyntaxParser(BaseParser):
    """
    Parse the metadata of a code block, which must have the structure:
        # --- (ID) option
    option is optional, but including it will mark the block as a parameter.
    """

    def __init__(self, line):
        super(BlockSyntaxParser, self).__init__(line)

        self.state = 0
        self.parsed_id = ''
        self.parsed_parameter = ''
        self.parsed_option = ''

    @staticmethod
    def can_parse(line):
        return line.lstrip().startswith(kw)

    def parse(self):
        while not self._is_end():
            self._read_next()
        return self.parsed_id, self.parsed_parameter, self.parsed_option

    def _read_next(self):
        self._read_while(BlockSyntaxParser._is_whitespace)
        if self._is_end():
            return

        if self.state == 0:
            self._read_kw()
        elif self.state == 1:
            self._read_id()
        else:
            self._read_option()

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
        """ Read the thing inside the parenthesis. """
        # open paren
        if self._peek_char() != '(':
            self._throw('Cannot find "("')
        self._next_char()
        self._read_while(self._is_whitespace)

        # read the actual identifier
        ch = self._peek_char()
        if not self._is_id_start(ch):
            self._throw('Invalid identifier start character {}'.format(ch))

        self.parsed_id = self._read_while(self._is_id)
        self._read_while(self._is_whitespace)

        # close paren
        if self._peek_char() != ')':
            self._throw('Cannot find ")"')
        self._next_char()
        self.state += 1

    def _read_option(self):
        """ Read whatever remains after the parenthesis. """
        s = self._remaining().strip()  # for error message

        self._read_while(self._is_whitespace)
        # option follows the same naming convention as ID
        # but we didn't check the starting character, so option can start with
        # a number or the underscore
        opt = self._read_while(self._is_id)
        if opt != '':
            self.parsed_parameter = self.parsed_id
            self.parsed_option = opt
            self.parsed_id += ':' + self.parsed_option

        self._read_while(self._is_whitespace)
        # throw an error for anything we can't handle
        if not self._is_end():
            self._throw('Invalid option syntax "{}"'.format(s))
