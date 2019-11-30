# -*- coding: utf-8 -*-
from .baseparser import BaseParser, ParseError
from dataclasses import dataclass
from enum import Enum


class TokenType(Enum):
    var = 1
    index_var = 2
    number = 3


@dataclass
class ParsedToken:
    value: str
    type: TokenType


class ConditionParser(BaseParser):
    """ A class for parsing the condition string """
    def __init__(self, line):
        super(ConditionParser, self).__init__(line)
        self.parsed_code = ''
        self.parsed_decs = []

    def parse(self):
        while not self._is_end():
            self._read_next()
        return self.parsed_code, self.parsed_decs

    @staticmethod
    def _is_keyword(w):
        return w == 'and' or w == 'or'

    @staticmethod
    def _is_operator(ch):
        return ch in ['=', '(', ')', '!', '>', '<']

    def _throw(self, msg):
        msg = 'At character {} of "{}":\n\t{}'.format(self.i + 1, self.line, msg)
        raise ParseError(msg)

    def _maybe_read_index(self):
        # we only want to parse the LHS of ==
        if len(self.parsed_decs) % 2 == 1:
            return False

        if not self._is_end() and self._peek_char() == '.':
            # try to parse .index
            self._next_char()
            v = self._read_while(self._is_id)
            if v == 'index':
                return True
            else:
                msg = 'Expected ".index", got ".{}"'.format(v)
                self._throw(msg)

        return False

    def _read_next(self):
        self.parsed_code += self._read_while(BaseParser._is_whitespace)
        if self._is_end():
            return

        ch = self._peek_char()
        if self._is_id_start(ch):
            w = self._read_while(self._is_id)
            if ConditionParser._is_keyword(w):
                self.parsed_code += w
                return

            tk = ParsedToken(w, TokenType.var)
            if self._maybe_read_index():
                tk.type = TokenType.index_var

            self.parsed_decs.append(tk)
            self.parsed_code += '{}'
        elif self._is_digit(ch):
            w = self._read_while(self._is_digit)
            if not self._is_end() and self._peek_char() == '.':  # read decimal
                w += self._next_char() + self._read_while(self._is_digit)

            self.parsed_decs.append(ParsedToken(w, TokenType.number))
            self.parsed_code += '{}'
        elif self._is_operator(ch):
            w = self._read_while(ConditionParser._is_operator)
            self.parsed_code += w
        else:
            msg = 'Cannot handle character "{}".'.format(ch)
            self._throw(msg)
