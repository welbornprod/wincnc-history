#!/usr/bin/env python3
# -*- coding: utf-8 -*-

""" WinCNC-History
    View history from WinCNC, because the actual History dialog in WinCNC is
    way too small and doesn't have a lot of features.
    -Christopher Welborn 04-25-2019
"""

import sys

from lib.gui.main import load_gui
from lib.util.config import (
    C,
    SCRIPT,
    VERSIONSTR,
    WINCNC_FILE,
    debug,
    debugprinter,
    docopt,
    print_err,
)
from lib.util.parser import History

USAGESTR = """{versionstr}
    Usage:
        {script} -h | -v
        {script} [-D] [-c]

    Options:
        -c,--console  : Run in console-mode.
        -D,--debug    : Show some debug info while running.
        -h,--help     : Show this help message.
        -v,--version  : Show version.
""".format(script=SCRIPT, versionstr=VERSIONSTR)


def main(argd):
    """ Main entry point, expects docopt arg dict as argd. """
    debugprinter.enable(argd['--debug'])
    if argd['--console']:
        debug('Using file: {}'.format(WINCNC_FILE))
        return list_history()
    return load_gui()


def list_history():
    history = History.from_file(WINCNC_FILE)
    for session in history:
        print(C(session))
    return 0 if history else 1


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
