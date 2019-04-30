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
    'AUTHOR',
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
VERSION = '0.0.3'
VERSIONSTR = '{} v. {}'.format(NAME, VERSION)
AUTHOR = 'Christopher Welborn'
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


def get_wincnc_file():
    paths = [
        config.get('wincnc_file', None),
        'C:/WinCNC/WINCNC.CSV',
        os.path.join(SCRIPTDIR, 'example_data/WINCNC.CSV'),
    ]
    for filepath in paths:
        if filepath and os.path.exists(filepath):
            return filepath

    # Not found, build a decent error message.
    if paths[0] is None:
        paths.pop(0)
        paths.append('\n`wincnc_file` was not set in config.')
    else:
        configpath = paths[0]
        paths.pop(0)
        paths.append(f'\nFile set in config was not found:\n  {configpath}')

    trypaths = '\n  '.join(
        s.replace(SCRIPTDIR, '..')
        for s in paths
    )
    msg = '\n'.join((
        'Cannot find WinCNC.csv file.',
        'Tried to look in:',
        f'  {trypaths}',
    ))
    raise FileNotFoundError(msg)


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
