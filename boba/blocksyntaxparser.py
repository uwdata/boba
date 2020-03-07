# -*- coding: utf-8 -*-

from .baseparser import BaseParser, ParseError

kw = '# ---'


class BlockSyntaxParser(BaseParser):
    """
    Parse the metadata of a code block, which must have the structure:
        # --- (ID) option @if condition
    option is optional, but including it will mark the block as a parameter.
    @if is optional and it creates a procedural dependency constraint on this
        block and this option (if any).
    """

    def __init__(self, line):
        super(BlockSyntaxParser, self).__init__(line)

        self.state = 0
        self.parsed_id = ''
        self.parsed_parameter = ''
        self.parsed_option = ''
        self.parsed_condition = ''

    @staticmethod
    def can_parse(line):
        return line.lstrip().startswith(kw)

    @staticmethod
    def _is_operator_start(ch):
        return ch == '@'

    @staticmethod
    def _is_condition(word):
        return word == 'if'

    def parse(self):
        while not self._is_end():
            self._read_next()
        return self.parsed_id, self.parsed_parameter, self.parsed_option,\
            self.parsed_condition

    def _read_next(self):
        self._read_while(BlockSyntaxParser._is_whitespace)
        if self._is_end():
            return

        if self.state == 0:
            self._read_kw()
        elif self.state == 1:
            self._read_id()
        elif self.state == 2:
            self._maybe_read_option()
        elif self.state == 3:
            self._read_condition()
        else:
            # we've read anything we can handle but haven't reached the end
            s = self._remaining().strip()
            self._throw('Cannot handle "{}"'.format(s))

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

    def _maybe_read_option(self):
        """ Read the option, if there is any. """
        self._read_while(self._is_whitespace)

        # check if the next word is maybe an option
        if not self._is_id_start(self._peek_char()):
            self.state += 1
            return

        # option follows the same naming convention as ID
        opt = self._read_while(self._is_id)
        if opt != '':
            self.parsed_parameter = self.parsed_id
            self.parsed_option = opt
            self.parsed_id += ':' + self.parsed_option

        self._read_while(self._is_whitespace)
        self.state += 1

    def _read_condition(self):
        """ Read condition. """
        self._read_while(self._is_whitespace)

        # check if the next char is indeed an operator
        if not BlockSyntaxParser._is_operator_start(self._peek_char()):
            self.state += 1
            return

        # read @if
        self._next_char()
        w = self._read_while(self._is_id)
        if not BlockSyntaxParser._is_condition(w):
            self._throw('Cannot handle @{}'.format(w))

        # read whatever remains as the condition
        s = self._remaining().strip()
        self._end()
        self.state += 1

        # construct the condition
        bl = self.parsed_parameter if self.parsed_option else self.parsed_id
        self.parsed_condition = {'block': bl, 'condition': s}
        if self.parsed_option:
            self.parsed_condition['option'] = self.parsed_option
