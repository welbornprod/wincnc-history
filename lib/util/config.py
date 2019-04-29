#!/usr/bin/env python3

""" WinCNC-History - Libraries - Config
    Configuration for WinCNC-History.
    -Christopher Welborn 04-27-2019
"""

import json
import os
import sys
import tkinter as tk
from tkinter import ttk


from colr import (
    Colr as C,
    auto_disable as colr_auto_disable,
    docopt,
)
from easysettings import load_json_settings
from printdebug import DebugColrPrinter


# Explicitly exported by this module:
__all__ = (
    'C',
    'NAME',
    'NotSet',
    'SCRIPT',
    'SCRIPTDIR',
    'VERSION',
    'VERSIONSTR',
    'colr_auto_disable',
    'config',
    'debug',
    'debug_err',
    'debug_exc',
    'debugprinter',
    'docopt',
    'tk',
    'ttk',
)

debugprinter = DebugColrPrinter()
debugprinter.disable()
debug = debugprinter.debug
debug_err = debugprinter.debug_err
debug_exc = debugprinter.debug_exc

colr_auto_disable()

NAME = 'WinCNC-History'
VERSION = '0.0.2'
VERSIONSTR = '{} v. {}'.format(NAME, VERSION)
SCRIPT = os.path.split(os.path.abspath(sys.argv[0]))[1]
SCRIPTDIR = os.path.abspath(sys.path[0])

CONFIGFILE = os.path.join(SCRIPTDIR, 'wincnc-history.json')
ICONFILE = os.path.join(
    SCRIPTDIR,
    'resources',
    'wincnc-history.png'
)
# Global config settings.
config = load_json_settings(
    CONFIGFILE,
    default={
        'theme': 'clam',
    }
)

example_file = os.path.join(SCRIPTDIR, 'example_data/WINCNC.CSV')
win_file = 'C:/WinCNC/WINCNC.CSV'
config_file = config.get('wincnc_file', None)
if config_file and os.path.exists(config_file):
    WINCNC_FILE = config_file
elif os.path.exists(win_file):
    WINCNC_FILE = win_file
elif os.path.exists(example_file):
    WINCNC_FILE = example_file
else:
    print(C('WinCNC.csv file not found!', 'red'), file=sys.stderr)
    sys.exit(1)


def debug_obj(o, msg=None, is_error=False, parent=None, level=0):
    """ Pretty print an object, using JSON. """
    alignfirst = False
    debugfunc = debug_err if is_error else debug
    if msg:
        debugfunc(msg, parent=parent, level=level + 1)
        alignfirst = True

    try:
        # Try sorting first.
        lines = json.dumps(o, indent=4, sort_keys=True).split('\n')
    except (TypeError, ValueError):
        try:
            lines = json.dumps(o, indent=4).split('\n')
        except (TypeError, ValueError) as ex:
            # Not serializable, just use repr.
            debug_err('Can\'t serialize object: ({}) {!r}'.format(
                type(o).__name__,
                o,
            ))
            debug_err('Error was: {}'.format(ex))
            lines = []
            for a in [s for s in dir(o) if not s.startswith('_')]:
                val = getattr(o, a)
                lines.append(f'{a!r}: {val!r}')

    for i, s in enumerate(lines):
        debugfunc(
            s,
            parent=parent,
            level=level + 1,
            align=(i > 0) or alignfirst,
        )


def print_err(*args, **kwargs):
    """ A wrapper for print() that uses stderr by default. """
    if kwargs.get('file', None) is None:
        kwargs['file'] = sys.stderr

    # Use color if asked, but only if the file is a tty.
    if kwargs['file'].isatty():
        # Keep any Colr args passed, convert strs into Colrs.
        msg = kwargs.get('sep', ' ').join(
            str(a) if isinstance(a, C) else str(C(a, 'red'))
            for a in args
        )
    else:
        # The file is not a tty anyway, no escape codes.
        msg = kwargs.get('sep', ' ').join(
            str(a.stripped() if isinstance(a, C) else a)
            for a in args
        )
    print(msg, **kwargs)


class _NotSet(object):
    def __bool__(self):
        return False

    def __colr__(self):
        return C('Not Set', 'red').join('<', '>', fore='dimgrey')

    def __str__(self):
        return '<Not Set>'


# Singleton instance for a None value that is not None.
NotSet = _NotSet()
