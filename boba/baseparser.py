# -*- coding: utf-8 -*-

import re
import sys
from dataclasses import dataclass


@dataclass
class Token:
    type: str
    value: str


class ParseError(SyntaxError):
    pass


class BaseParser:

    def __init__(self, line):
        self.line = line
        self.i = 0
        self.row = 0
        self.col = 0
        self.current = None

    @staticmethod
    def _is_whitespace(char):
        return any(c == char for c in ' \t\n')

    @staticmethod
    def _is_id_start(ch):
        return bool(re.match('[a-zA-Z]', ch))

    @staticmethod
    def _is_id(ch):
        return bool(re.match('[_a-zA-Z0-9]', ch))

    def _next_char(self):
        ch = self.line[self.i]
        self.i += 1
        if ch == '\n':
            self.row += 1
            self.col = 0
        else:
            self.col += 1
        return ch

    def _peek_char(self):
        return self.line[self.i]

    def _is_end(self):
        return self.i >= len(self.line)

    def _read_while(self, fun, max_len=sys.maxsize):
        s = ''
        while not self._is_end() and fun(self._peek_char()) and len(s) < max_len:
            s += self._next_char()
        return s

    def _peek(self):
        if not self.current:
            self.current = self._read_next()
        return self.current

    def _next(self):
        tmp = self.current
        self.current = None
        return tmp or self._read_next()

    def _read_next(self):
        pass
