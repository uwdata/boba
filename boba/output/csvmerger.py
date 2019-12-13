# -*- coding: utf-8 -*-

import os
import re
import pandas as pd
import boba.util as util

STR_MAX = 1024


class CSVMerger:
    def __init__(self, pattern, base, out, delimiter=','):
        self.pattern = pattern
        self.base = base
        self.out = out
        self.delimiter = delimiter

    def _fn_func(self, i):
        return self.pattern.format(i)

    def _to_regex(self):
        """ Convert the string pattern to regex. """
        i = self.pattern.find('{}')
        if i < 0:
            util.print_fail('Invalid pattern: {}'.format(self.pattern))
            exit(1)

        rg = re.compile('^' + re.escape(self.pattern[:i]) + '(\d+)' +
                        re.escape(self.pattern[i+2:]))
        return rg

    def get_files(self):
        """ Get a list of universe indices in the folder that matches given
        pattern. The indices are sorted."""
        idx = []
        for f in os.listdir(self.base):
            m = re.match(self._to_regex(), f)
            if m:
                idx.append(int(m.group(1)))
        idx.sort()
        return idx

    def merge(self):
        """ Merge the CSV files into one file """
        result = pd.DataFrame()
        for i in self.get_files():
            # read the file
            df = pd.read_csv(os.path.join(self.base, self._fn_func(i)),
                             delimiter=self.delimiter,
                             converters={i: str for i in range(0, STR_MAX)})
            n = len(list(df.columns))

            # augment
            df['uid'] = i

            # rearrange columns
            cols = list(df.columns)
            cols = cols[n:] + cols[:n]
            df = df[cols]

            # merge with previous results
            result = pd.concat([result, df], axis=0, sort=False)

        return result

    def main(self):
        res = self.merge()
        res.to_csv(self.out, index=False)
