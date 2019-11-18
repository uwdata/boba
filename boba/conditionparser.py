# -*- coding: utf-8 -*-
from .baseparser import BaseParser, ParseError


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
        return ch in ['=', '(', ')']

    def _read_next(self):
        self.parsed_code += self._read_while(BaseParser._is_whitespace)
        if self._is_end():
            return

        ch = self._peek_char()
        if self._is_id_start(ch):
            w = self._read_while(self._is_id)
            if ConditionParser._is_keyword(w):
                self.parsed_code += w
            else:
                self.parsed_decs.append(w)
                self.parsed_code += '{}'
        elif self._is_operator(ch):
            w = self._read_while(ConditionParser._is_operator)
            self.parsed_code += w
        else:
            msg = 'Cannot handle character "{}".'.format(ch)
            msg = 'At character {} of "{}":\n\t{}'.format(self.i+1, self.line, msg)
            raise ParseError(msg)
