#!/usr/bin/env python3
# -*- coding: utf-8 -*-

""" wincnc-history.py
    View history from WinCNC, because the actual History dialog in WinCNC is
    way too small.
    -Christopher Welborn 04-25-2019
"""

import os
import sys

from colr import (
    Colr as C,
    auto_disable as colr_auto_disable,
    docopt,
)
from printdebug import DebugColrPrinter

from lib.parser import History

debugprinter = DebugColrPrinter()
debugprinter.disable()
debug = debugprinter.debug

colr_auto_disable()

NAME = 'WinCNC-History'
VERSION = '0.0.1'
VERSIONSTR = '{} v. {}'.format(NAME, VERSION)
SCRIPT = os.path.split(os.path.abspath(sys.argv[0]))[1]
SCRIPTDIR = os.path.abspath(sys.path[0])

USAGESTR = """{versionstr}
    Usage:
        {script} -h | -v
        {script} [-D]

    Options:
        -D,--debug    : Show some debug info while running.
        -h,--help     : Show this help message.
        -v,--version  : Show version.
""".format(script=SCRIPT, versionstr=VERSIONSTR)

example_file = os.path.join(SCRIPTDIR, 'example_data/WINCNC.CSV')
win_file = 'C:/WinCNC/WINCNC.CSV'
if os.path.exists(example_file):
    WINCNC_FILE = example_file
elif os.path.exists(win_file):
    WINCNC_FILE = win_file
else:
    print(C('WinCNC.csv file not found!', 'red'), file=sys.stderr)
    sys.exit(1)


def main(argd):
    """ Main entry point, expects docopt arg dict as argd. """
    debugprinter.enable(argd['--debug'])

    history = History.from_file(WINCNC_FILE)
    for session in history:
        print(C(session))
    return 0 if history else 1


def print_err(*args, **kwargs):
    """ A wrapper for print() that uses stderr by default. """
    if kwargs.get('file', None) is None:
        kwargs['file'] = sys.stderr
    print(*args, **kwargs)


class InvalidArg(ValueError):
    """ Raised when the user has used an invalid argument. """
    def __init__(self, msg=None):
        self.msg = msg or ''

    def __str__(self):
        if self.msg:
            return 'Invalid argument, {}'.format(self.msg)
        return 'Invalid argument!'


if __name__ == '__main__':
    try:
        mainret = main(docopt(USAGESTR, version=VERSIONSTR, script=SCRIPT))
    except InvalidArg as ex:
        print_err(ex)
        mainret = 1
    except (EOFError, KeyboardInterrupt):
        print_err('\nUser cancelled.\n')
        mainret = 2
    except BrokenPipeError:
        print_err('\nBroken pipe, input/output was interrupted.\n')
        mainret = 3
    sys.exit(mainret)
