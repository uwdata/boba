#!/usr/bin/env python3

import re

kw = '# ---'


class BlockParser:
    """
    Parse the metadata of a code block, which must have the structure:
        # --- (ID) name of the block
    """

    def __init__(self, line):
        self.i = 0
        self.state = 0
        self.line = line
        self.result = {'id': '', 'name': '', 'success': False, 'err': ''}

    @staticmethod
    def can_parse(line):
        return line.lstrip().startswith(kw)

    def parse(self):
        while not self._is_end():
            self._read_next()
        return self.result

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
        self.result['err'] = err
        self._end()

    def _next_char(self):
        self.i += 1
        return self.line[self.i - 1]

    def _peek_char(self):
        return self.line[self.i]

    def _is_end(self):
        return self.i >= len(self.line)

    @staticmethod
    def _is_whitespace(char):
        return any(c == char for c in ' \t\n')

    def _read_while(self, fun):
        s = ''
        while not self._is_end() and fun(self._peek_char()):
            s += self._next_char()
        return s

    def _remaining(self):
        return self.line[self.i:]

    def _read_kw(self):
        if self._remaining().startswith(kw):
            self.i += len(kw)
            self.state += 1
        else:
            self._throw('expected {}'.format(kw))

    def _read_id(self):
        pattern = r'^\([a-zA-Z][a-zA-Z0-9]*\)'
        m = re.match(pattern, self._remaining())
        if m:
            g = m.group(0)
            self.result['id'] = g.strip('()')
            self.i += len(g)
            self.state += 1

            # since name clause is optional
            self.result['success'] = True
        else:
            self._throw('expected an ID with syntax "(ID)"')

    def _read_name(self):
        self.result['name'] = self._remaining().strip()
        self._end()
