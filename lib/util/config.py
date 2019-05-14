#!/usr/bin/env python3

""" WinCNC-History - Libraries - Config
    Configuration for WinCNC-History.
    -Christopher Welborn 04-27-2019
"""

import json
import os
import sys

from colr import (
    docopt,
)

from ..gui.dialogs import show_error

from .config_json import (
    easysettings_version,
    load_settings,
)
from .debug import (
    C,
    colr_version,
    printdebug_version,
)
# Explicitly exported by this module:
__all__ = (
    'AUTHOR',
    'NAME',
    'NotSet',
    'SCRIPT',
    'SCRIPTDIR',
    'VERSION',
    'VERSIONSTR',
    'config',
    'docopt',
)

NAME = 'WinCNC-History'
VERSION = '0.0.6'
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


try:
    config = load_settings(CONFIGFILE)
except json.decoder.JSONDecodeError as ex:
    show_error('\n'.join((
        f'Can\'t decode config file.',
        '\nMessage:',
        f'  {ex}',
    )))
    sys.exit(1)


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


class _NotSet(object):
    def __bool__(self):
        return False

    def __colr__(self):
        return C('Not Set', 'red').join('<', '>', fore='dimgrey')

    def __str__(self):
        return '<Not Set>'


# Singleton instance for a None value that is not None.
NotSet = _NotSet()


# Some version info, available to the GUI.
config['versions'] = {
    'Colr': colr_version,
    'EasySettings': easysettings_version,
    'PrintDebug': printdebug_version,
    'Python': sys.version.split()[0],
}
