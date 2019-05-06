#!/usr/bin/env python3
# -*- coding: utf-8 -*-

""" WinCNC-History
    View history from WinCNC, because the actual History dialog in WinCNC is
    way too small and doesn't have a lot of features.
    -Christopher Welborn 04-25-2019
"""

import sys

from lib.gui.main import load_gui
from lib.gui.dialogs import show_error
from lib.util.config import (
    SCRIPT,
    VERSIONSTR,
    docopt,
    get_wincnc_file,
)
from lib.util.debug import (
    C,
    debug,
    debugprinter,
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
    try:
        wincnc_file = get_wincnc_file()
    except FileNotFoundError as ex:
        show_error(ex)
        return 1

    if argd['--console']:
        debug('Using file: {}'.format(wincnc_file))
        return list_history(wincnc_file)
    return load_gui(filepath=wincnc_file)


def list_history(filepath):
    history = History.from_file(filepath)
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
