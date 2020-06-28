import subprocess
import os
from .lang import Lang
from .wrangler import DIR_SCRIPT, DIR_LOG, get_universe_id_from_script, get_universe_log, get_universe_error_log, get_universe_name
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

    universe_id = get_universe_id_from_script(script)
    universe_name_fmt = "[" + get_universe_name(universe_id) + "]"
    log_dir = os.path.join(folder, DIR_LOG)
    with open(os.path.join(log_dir, get_universe_log(universe_id)), 'w') as log:
        while True:
            # blocks here until next line is availible.
            output = out.stdout.readline().decode('utf-8')
            if output == '' and out.poll() is not None:
                break
            if output:
                print(universe_name_fmt + " " + output, end='')
                log.write(output)
            rc = out.poll()

    err = out.communicate()[1]
    err_decoded = err.decode('utf-8')
    if err_decoded is not "":
        with open(os.path.join(log_dir, get_universe_error_log(universe_id)), 'w') as err_log:
            err_log.write(err_decoded)
        
        print(universe_name_fmt + " error:\n" + err_decoded, end='')

    return get_universe_name(universe_id), out.returncode


def run_commands_in_folder(folder, file_with_commands):
    """ Run command """
    cwd = os.getcwd()
    os.chdir(folder)
    with open(file_with_commands) as f:
        for line in f.readlines():
            os.system(line)
    os.chdir(cwd)
