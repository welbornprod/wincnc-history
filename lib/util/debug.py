#!/usr/bin/env python3

""" WinCNC-History - Libraries - Debug
    Debug utilities for WinCNC-History.
    -Christopher Welborn 05-05-2019
"""

import json
import sys

from colr import (
    __version__ as colr_version,
    Colr as C,
    auto_disable as colr_auto_disable,
)

from printdebug import (
    __version__ as printdebug_version,
    DebugColrPrinter,
)

__all__ = [
    'C',
    'colr_auto_disable',
    'colr_version',
    'debugprinter',
    'debug',
    'debug_err',
    'debug_exc',
    'printdebug_version',
]

colr_auto_disable()

debugprinter = DebugColrPrinter()
debugprinter.enable(('-D' in sys.argv) or ('--debug' in sys.argv))
debug = debugprinter.debug
debug_err = debugprinter.debug_err
debug_exc = debugprinter.debug_exc


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
            # Not serializable, just use attrs from `dir()`.
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
