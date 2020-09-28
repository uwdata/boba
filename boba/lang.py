# -*- coding: utf-8 -*-
import os

PY = 'python'
R = 'r'

script = '{{script_name}}'
compiled = '{{universe_name}}'

DEFAULT_LANGS = {
    'python' : {
        'ext' : ['py'],
        'run' : ['python', script]
    },
    'r' : {
        'ext' : ['R', 'r'],
        'run' : ['Rscript', script]
    }
}

class LangError(NameError):
    pass


class Lang:
    def __init__(self, script, lang=None, supported_langs=None):
        self.supported_langs = DEFAULT_LANGS
        if supported_langs:
            for l in supported_langs:
                self.supported_langs[l] = supported_langs[l]
            
        self.script = script
        self.name, self.ext = os.path.splitext(script)
        self.lang = self._infer_lang(lang)

    def _infer_lang(self, lang):
        if lang:
            lang = lang.strip().lower()
            if not lang in self.supported_langs:
                raise LangError('Error: language "{}" is not supported'.format(lang))

            return lang, self.supported_langs[lang]
        else:
            for lang, lang_properties in self.supported_langs.items():
                if self.ext[1:] in lang_properties['ext']:
                    return lang, lang_properties

            raise LangError('Error: cannot infer language from file extension ' + self.ext)

    def _format_cmd(self, cmd):
        return cmd.strip().replace(script, self.script).replace(compiled, self.name)
    
    def get_ext(self):
        return self.ext

    def get_cmd(self):
        cmd = []
        if 'compile' in self.lang[1]:
            cmd.append([self._format_cmd(x) for x in self.lang[1]['compile']])
            
        cmd.append([self._format_cmd(x) for x in self.lang[1]['run']])
        return cmd

    def is_r(self):
        return self.lang[0] == R

    def is_python(self):
        return self.lang[0] == PY
