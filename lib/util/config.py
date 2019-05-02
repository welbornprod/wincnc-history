#!/usr/bin/env python3

""" WinCNC-History - Libraries - Config
    Configuration for WinCNC-History.
    -Christopher Welborn 04-27-2019
"""

import json
import os
import platform
import re
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

from ..gui.dialogs import show_error

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
VERSION = '0.0.4'
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

OS = platform.system().lower()

# Global config settings.
config_defaults = {
    'change_hours': 0,
    'theme': 'winnative' if OS == 'windows' else 'clam',
    'geometry': '1111x612+110+22',
    'bg_entry': '#F4F4F4',
    'bg_focus': '#DEDEDE',
    'bg_treeview': '#F4F4F4',
    'fg_command': '#002050',
    'fg_error': '#5B0000',
    'fg_file': '#004C13',
    'fg_file_command': '#0C4A46',
    'fg_label': '#4C4C4C',
    'fg_session': '#002050',
    'font_dialog': ['Arial', 10],
    'font_entry': ['Consolas', 9] if OS == 'windows' else ['Monospace', 9],
    'font_treeview': ['Consolas', 9] if OS == 'windows' else ['Monospace', 9],
    'font_treeview_heading': ['Arial', 12],
}
config_keys = set(config_defaults)
config_keys.add('wincnc_file')

try:
    config = load_json_settings(
        CONFIGFILE,
        default=config_defaults,
    )
except json.decoder.JSONDecodeError as ex:
    show_error('\n'.join((
        f'Can\'t decode config file.',
        '\nMessage:',
        f'  {ex}',
    )))
    sys.exit(1)


def bad_config_type(k):
    """ Generate an error message if config[k] is the wrong type. """
    v = config[k]
    vtype = type(v).__name__

    if v in (None, ''):
        return f'Empty or null values are not allowed.'

    # Special case for wincnc_file.
    if k == 'wincnc_file':
        if not isinstance(v, str):
            return f'Expecting a filepath (str), Got: ({vtype}) {v!r}.'
        if not os.path.exists(v):
            return f'File path in config was not found: {v}'
        return None

    expected = type(config_defaults[k])
    if not isinstance(v, expected):
        return f'Expecting {expected.__name__}, Got: ({vtype}) {v!r}.'

    if k == 'geometry':
        if re.match(r'\d{1,5}x\d{1,5}\+\d{1,5}\+\d{1,5}', v) is None:
            example = '[width]x[height]+[x_pos]+[y_pos]'
            return '\n'.join((
                f'Expected tkinter size/position:',
                '  {example},',
                '\nGot: {v!r}.',
            ))

    if k.startswith('font_'):
        ln = len(v)
        if (ln not in (1, 2, 3)):
            # Ensure fonts have the right length.
            return f'Expecting 1-3 items [name, size, weight], Got: {ln}.'
        # Ensure fonts have the right types.
        example = '\n'.join((
            '  [(str) name],',
            '  [(str) name, (int) size],',
            '  [(str) name, (int) size, (str) weight],',
        ))
        got = '[{}]'.format(
            ', '.join(
                f'({type(x).__name__}) {x!r}'
                for x in v
            )
        )
        valid = ([str], [str, int], [str, int, str])
        if list(type(x) for x in v) not in valid:
            return f'Expected\n{example}\n\nGot: {got}.'

    if k.startswith('fg_') or k.startswith('bg_'):
        if re.match('#[0-9A-F]{6}', v) is None:
            example = '#000000-#FFFFFF'
            return f'Expected hex color (str) {example!r},\nGot: {v!r}.'

    return None


# Check config types against default config values.
for k, v in config.items():
    # Ensure config keys are not misspelled.
    if k not in config_keys:
        show_error(f'Not a valid config key: {k!r} (value: {v!r})')
        sys.exit(1)

    # Ensure config values are always the right type.
    badmsg = bad_config_type(k)
    if badmsg:
        show_error('\n'.join((
            f'Bad config value for: {k!r}',
            badmsg,
        )))
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
