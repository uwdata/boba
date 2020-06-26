import subprocess
import os
from .lang import Lang
from .wrangler import DIR_SCRIPT
from subprocess import PIPE


def run_batch_of_universes(folder, universes):
    """ Run a batch of universes """
    batch = []
    for universe in universes:
        batch.append(run_universe(folder, universe))

    return batch


def run_universe(folder, script):
    """ Run one universe """
    cmd = Lang('', script).get_cmd()
    out = subprocess.Popen([cmd, script], cwd=os.path.join(folder, DIR_SCRIPT),
                           stdout=PIPE, stderr=PIPE)
    # it's ok to block here because this function will be running as a separate process
    output, err = out.communicate()
    print(err.decode('utf-8'), end='')
    print(script + '\n' + output.decode('utf-8'), end='')
    return script.split('.')[0], out.returncode


def run_commands_in_folder(folder, file_with_commands):
    """ Run command """
    cwd = os.getcwd()
    os.chdir(folder)
    with open(file_with_commands) as f:
        for line in f.readlines():
            os.system(line)
    os.chdir(cwd)
