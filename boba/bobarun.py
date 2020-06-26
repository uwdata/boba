import subprocess
import os
from .lang import Lang
from subprocess import PIPE

def run_batch_of_universes(folder, universes):
    batch = []
    for universe in universes:
        batch.append(run_universe(folder, universe))

    return batch


def run_universe(folder, script):
    cmd = Lang("", script).get_cmd()
    out = subprocess.Popen([cmd, script], cwd=folder + "/code/", stdout = PIPE, stderr = PIPE)
    # it's ok to block here because this function will be running as a seperate process
    output, err = out.communicate()
    print(err.decode("utf-8"), end = '')
    print(script + "\n" + output.decode("utf-8"), end='')
    return (script.split('.')[0], out.returncode)


def run_commands_in_folder(folder, file_with_commands):
    cwd = os.getcwd()
    os.chdir(folder)
    with open(file_with_commands) as f:
        for line in f.readlines():
            os.system(line)
    os.chdir(cwd)


def get_universe_script(universe_id, lang_extension):
    return "universe_" + str(universe_id) + lang_extension
