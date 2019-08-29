# -*- coding: utf-8 -*-


class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def print_fail(msg):
    print(Colors.FAIL + msg + Colors.ENDC)

def print_warn(msg):
    print(Colors.WARNING + msg + Colors.ENDC)
