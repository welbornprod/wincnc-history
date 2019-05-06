#!/usr/bin/env python3

""" WinCNC-History - Libraries - Config-JSON
    Default configuration for WinCNC-History and JSONSettings helpers.
    -Christopher Welborn 05-05-2019
"""

import os
import platform
import re
import sys

from datetime import datetime

from easysettings import (
    __version__ as easysettings_version,
    JSONSettings,
    load_json_settings,
)

from ..gui.dialogs import (
    show_error,
)

es_ver_pcs = easysettings_version.split('.')
es_ver_major = int(es_ver_pcs[0])
if es_ver_major < 3:
    show_error('\n'.join((
        'Need EasySettings >= 3.0.0.',
        f'Got EasySettings v. {easysettings_version}',
        '\nPlease upgrade easysettings with `pip`.',
    )))
    sys.exit(1)

OS = platform.system().lower()


# Global config settings.
config_defaults = {
    'change_hours': 0,
    'theme': 'winnative' if OS == 'windows' else 'clam',
    'geometry': '1111x612+110+22',
    'bg_entry': '#F4F4F4',
    'bg_focus': '#DEDEDE',
    'bg_treeview': '#F4F4F4',
    'break_lunch': None,
    'break_morning': None,
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


def bad_config_type(k, v):
    """ Generate an error message if config[k] is the wrong type. """
    vtype = type(v).__name__

    if (not k.startswith('break_')) and (v in (None, '')):
        # Break times can be empty.
        return f'Empty or null values are not allowed.'

    # Special case for wincnc_file.
    if k == 'wincnc_file':
        if not isinstance(v, str):
            return f'Expecting a filepath (str), Got: ({vtype}) {v!r}.'
        if not os.path.exists(v):
            return f'File path in config was not found: {v}'
        return None

    # Special case for break_*.
    if k.startswith('break_'):
        if not v:
            # Empty value is okay for break times.
            return None
        if not isinstance(v, str):
            return f'Expecting (str) \'hh:mm-hh:mm\', Got: ({vtype}) {v!r}.'
        try:
            parse_break_time(v)
        except ValueError as ex:
            return str(ex)
        return None

    # All other values should match the exact default type.
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
        # Ensure hex colors are valid.
        if re.match('#[0-9A-F]{6}', v) is None:
            example = '#000000-#FFFFFF'
            return f'Expected hex color (str) {example!r},\nGot: {v!r}.'

    return None


def load_settings(filename):
    return load_json_settings(
        filename,
        default=config_defaults,
        cls=WinCNCSettings,
    )


def parse_break_time(s):
    """ Parse a string like '11:00-11:30' into a start and end time. """
    errmsg = '\n'.join((
        f'Expecting (str) \'h:m-h:m\','
        '    [starttime-endtime]',
        '\nGot: {v!r}'
    ))
    try:
        startstr, endstr = s.split('-')
    except ValueError:
        raise ValueError(errmsg) from None
    try:
        start_time = datetime.strptime(startstr, '%H:%M')
    except ValueError as ex:
        raise ValueError('\n'.join((
            f'Bad start time: {startstr!r}\n',
            errmsg,
            f'Message: {ex}'
        ))) from None
    try:
        end_time = datetime.strptime(endstr, '%H:%M')
    except ValueError as ex:
        raise ValueError('\n'.join((
            f'Bad end time: {endstr!r}\n',
            errmsg,
            f'Message: {ex}'
        ))) from None
    return start_time, end_time


class WinCNCSettings(JSONSettings):
    def load_hook(self, data):
        """ Modify/check certain items during config load. """
        # Check config types against default config values.
        for k, v in data.items():
            # Ensure config keys are not misspelled.
            if k not in config_keys:
                show_error(f'Not a valid config key: {k!r} (value: {v!r})')
                sys.exit(1)

            # Ensure config values are always the right type.
            badmsg = bad_config_type(k, v)
            if badmsg:
                show_error('\n'.join((
                    f'Bad config value for: {k!r}',
                    badmsg,
                )))
                sys.exit(1)

            # Parse datetime types.
            if k.startswith('break_'):
                if v:
                    data[k] = parse_break_time(v)
                else:
                    data[k] = (None, None)
        return data

    def save_hook(self, data):
        """ Modify config before saving. """
        try:
            # Don't save versions to disk.
            data.pop('versions')
        except KeyError:
            pass
        return super().save_hook(data)

    def save_item_hook(self, key, value):
        """ Modify certain items before saving. """
        if not key.startswith('break_'):
            return key, value

        # Fix break times in config.
        if not all(value):
            return key, None

        return (
            key,
            '-'.join((
                datetime.strftime(value[0], '%H:%M'),
                datetime.strftime(value[1], '%H:%M'),
            ))
        )
