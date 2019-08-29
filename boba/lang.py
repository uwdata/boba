# -*- coding: utf-8 -*-
import os

PY = 'python'
R = 'r'


class LangError(NameError):
    pass


class Lang:
    def __init__(self, lang, script):
        self.lang = self._infer_lang(lang, script)

    def _is_valid_lang(self, lang):
        return lang == PY or lang == R

    def _ext_to_lang(self, ext):
        ext = ext.lower()[1:]
        if ext == 'py':
            return PY
        if ext == 'r' or ext == 'rmd':
            return R
        return ''

    def _infer_lang(self, lang, script):
        lang = lang.strip().lower()

        if self._is_valid_lang(lang):
            return lang

        if lang == '':
            _, ext = os.path.splitext(script)
            lang = self._ext_to_lang(ext)
            if self._is_valid_lang(lang):
                return lang
            else:
                raise LangError('Error: cannot infer language from file ' +
                                'extension {}'.format(ext))
        else:
            raise LangError('Error: language "{}" is not supported'.format(lang))

    def get_ext(self):
        if self.lang == R:
            return '.R'
        if self.lang == PY:
            return '.py'

    def get_cmd(self):
        if self.lang == R:
            return 'Rscript'
        if self.lang == PY:
            return 'python'

    def is_r(self):
        return self.lang == R

    def is_python(self):
        return self.lang == PY
