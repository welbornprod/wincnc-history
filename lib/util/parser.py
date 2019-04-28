#!/usr/bin/env python3
""" WinCNC-History - Libraries - Parser
    CSV parser and classes to hold information about the WinCNC history file.
    -Christopher Welborn 04-25-2019
"""
import csv
from collections import UserList
from datetime import (
    datetime,
    timedelta,
)

from colr import Colr as C


def parse_datetime(s):
    """ Parse a datetime in the form 'm-d-y h:m:s'. """
    return datetime.strptime(s, '%m-%d-%y %H:%M:%S')


def time_str(dt, human=False, time_only=False):
    """ Use strftime to format a datetime. """
    timestr = datetime.strftime(dt, '%I:%M:%S%p').lower()
    if time_only:
        return timestr
    if human:
        fmt = '%a, %b %e'
    else:
        fmt = '%m-%d-%y'
    datestr = datetime.strftime(dt, fmt)
    return f'{datestr} {timestr}'


def timedelta_from_str(durstr):
    """ Convert a string like '01:29' (1 minute and 29 seconds)
        into a datetime.timedelta`.
    """
    mins, secs = (int(s) for s in durstr.split(':'))
    return timedelta(minutes=mins, seconds=secs)


def timedelta_str(delta, short=False):
    """ Convert a timedelta into a human-readable string. """
    hours, rem = divmod(delta.seconds, 3600)
    hours += delta.days * 24
    mins, secs = divmod(rem, 60)

    plurals = 'second' if secs == 1 else 'seconds'
    pluralm = 'minute' if mins == 1 else 'minutes'
    if hours:
        if short:
            return f'{hours:>02}h:{mins:>02}m:{secs:>02}s'
        pluralh = 'hour' if hours == 1 else 'hours'
        return f'{hours} {pluralh}, {mins} {pluralm}, {secs} {plurals}'
    if mins:
        if short:
            return f'{mins:>02}m:{secs:>02}s'
        return f'{mins} {pluralm}, {secs} {plurals}'
    if short:
        return f'{secs:>02}s'
    return f'{secs} {plurals}'


class History(UserList):
    """ A collection of SessionHistorys. """
    def __bool__(self):
        return bool(self.data)

    def __colr__(self):
        return C('\n').join(C(ses) for ses in self)

    @classmethod
    def from_file(cls, filepath):
        """ Parse a WinCNC.csv file and return an initialized History
            instance.
        """
        sessions = []
        session = None
        with open(filepath, 'r') as f:
            for line in f:
                if line.lower().startswith('file name'):
                    # Skip headers.
                    continue
                if line.lower().startswith('starting'):
                    _, timestr, datestr = line.split(', ')

                    session = SessionHistory(
                        [],
                        start_time=' '.join((
                            datestr.strip(),
                            timestr.strip(),
                        ))
                    )
                    continue
                elif line.lower().startswith('exiting'):
                    _, timestr, datestr = line.split(', ')
                    session.end_time = parse_datetime(' '.join((
                        datestr.strip(),
                        timestr.strip(),
                    )))
                    session.recalculate_duration()
                    sessions.append(session)
                    session = None
                    continue
                if session is not None:
                    session.append(HistoryLine.from_line(line))
        # Pick up any non-exits.
        if session is not None:
            session.recalculate_duration()
            sessions.append(session)
        return cls(sessions)

    def get_line(self, hsh):
        """ Retrieve a HistoryLine from this History by hash. """
        for session in self:
            hl = session.get_line(hsh)
            if hl is not None:
                return hl
        raise ValueError(f'No HistoryLine with that hash {hsh}')


class SessionHistory(UserList):
    """ A collection of HistoryLines. """
    def __init__(self, iterable, start_time=None, end_time=None):
        super().__init__(iterable)
        self.start_time = start_time
        if isinstance(start_time, str):
            self.start_time = parse_datetime(start_time)

        self.end_time = end_time
        if isinstance(end_time, str):
            self.end_time = parse_datetime(end_time)

        # Cannot calculate duration on an empty list.
        self.duration_delta = timedelta()
        self.duration = '0s'
        self.recalculate_duration()

    def __bool__(self):
        return bool(self.data)

    def __colr__(self):
        pcs = [
            self.time_fmt(self.start_time, time_args={'fore': 'blue'}),
            C('  {}'.format(
                C('\n  ').join(C(l) for l in self)
            ))
        ]
        if self.end_time:
            pcs.append(self.time_fmt(self.end_time, time_args={'fore': 'red'}))
        return C('\n').join(pcs)

    def __hash__(self):
        return hash(self.time_str())

    def calc_duration(self):
        """ Calculate a timedelta (duration) for all lines in this session.
        """
        # sum() does not work for timedeltas.
        delta = timedelta()
        for line in self:
            delta = delta + line.duration_delta
        return delta

    def get_line(self, hsh):
        """ Retrieve a HistoryLine from this SessionHistory by hash.
        """
        hsh = str(hsh)
        for line in self:
            if hsh == str(hash(line)):
                return line
        return None

    def has_error(self):
        """ Returns True if any lines in this session had an error. """
        return any(hl.is_error() for hl in self)

    def last_status(self):
        """ Return the status of the last command/file in the history. """
        return self[-1].status if self else '<no commands>'

    def recalculate_duration(self):
        """ Set `self.duration_delta` and `self.duration` based on current
            HistoryLines.
        """
        self.duration_delta = self.calc_duration()
        self.duration = timedelta_str(self.duration_delta, short=True)

    def time_fmt(self, dt=None, time_args=None, date_args=None):
        """ Return a color formatted version of a datetime (self.start_time
            by default).
        """
        if dt is None:
            dt = self.start_time
        if not time_args:
            time_args = {'fore': 'blue'}
        if not date_args:
            date_args = time_args

        return datetime.strftime(
            dt,
            str(
                C(' ').join(
                    C('-').join(
                        C('%m', **time_args),
                        C('%d', **time_args),
                        C('%y', **time_args),
                    ),
                    C(':').join(
                        C('%I', **date_args),
                        C('%M', **date_args),
                        C('%S', **date_args),
                    ),
                )
            )
        )

    def time_str(self, dt=None, human=False, time_only=False):
        """ Return a stringified version of a datetime (self.start_time is
            the default).
        """
        if dt is None:
            dt = self.start_time
        return time_str(dt, human=human, time_only=time_only)

    def treeview_tags(self):
        """ Return a tuple of Treeview tag names for this SessionHistory. """
        tags = [hash(self), 'session']
        if self.has_error():
            tags.append('error')
        return tuple(tags)


class HistoryLine(object):
    colors = {
        'command': {'fore': 'dimgrey'},
        'command_file': {'fore': 'lightblue'},
        'filename': {'fore': 'blue', 'style': 'bright'},
        'minutes': {'fore': 'cyan'},
        'seconds': {'fore': 'cyan'},
        'time': {'fore': 'blue'},
        'date': {'fore': 'blue'},
        'status': {'fore': 'green'},
        'status_err': {'fore': 'red'},
        'rapid': {'fore': 'white'},
        'feed': {'fore': 'yellow'},
        'laser': {'fore': 'cyan'},
        'axis1': {'fore': 'blue'},
        'axis2': {'fore': 'blue'},
        'axis3': {'fore': 'blue'},
        'axis4': {'fore': 'blue'},
        'axis5': {'fore': 'blue'},
        'axis6': {'fore': 'blue'},
        'output_c1': {'fore': 'magenta'},
        'output_c2': {'fore': 'magenta'},
        'output_c3': {'fore': 'magenta'},
        'input_c1': {'fore': 'lightblue'},
        'input_c2': {'fore': 'lightblue'},
        'input_c3': {'fore': 'lightblue'},
        'input_c4': {'fore': 'lightblue'},
        'input_c5': {'fore': 'lightblue'},
        'input_c6': {'fore': 'lightblue'},
        'input_c7': {'fore': 'lightblue'},
        'input_c8': {'fore': 'lightblue'},
        'input_c9': {'fore': 'lightblue'},
        'input_c10': {'fore': 'lightblue'},
        'input_c11': {'fore': 'lightblue'},
        'input_c12': {'fore': 'lightblue'},
        'input_c13': {'fore': 'lightblue'},
        'atc1_t0': {'fore': 'white'},
        'atc1_t1': {'fore': 'white'},
        'atc1_t2': {'fore': 'white'},
        'atc1_t3': {'fore': 'white'},
        'atc1_t4': {'fore': 'white'},
        'atc1_t5': {'fore': 'white'},
        'atc1_t6': {'fore': 'white'},
        'atc1_t7': {'fore': 'white'},
        'atc1_t8': {'fore': 'white'},
        'atc1_t9': {'fore': 'white'},
        'atc1_t10': {'fore': 'white'},
    }
    header = (
        'filename', 'minutes', 'seconds', 'time', 'date',
        'status', 'rapid', 'feed', 'laser',
        'axis1', 'axis2', 'axis3', 'axis4', 'axis5', 'axis6',
        'output_c1', 'output_c2', 'output_c3',
        'input_c1', 'input_c2', 'input_c3', 'input_c4', 'input_c5',
        'input_c6', 'input_c7', 'input_c8', 'input_c9', 'input_c10',
        'input_c11', 'input_c12', 'input_c13',
        'atc1_t0', 'atc1_t1', 'atc1_t2', 'atc1_t3', 'atc1_t4', 'atc1_t5',
        'atc1_t6', 'atc1_t7', 'atc1_t8', 'atc1_t9', 'atc1_t10'
    )
    row_len = len(header)

    def __init__(
            self, filename, minutes, seconds, time, date,
            status, rapid, feed, laser,
            axis1, axis2, axis3, axis4, axis5, axis6,
            output_c1, output_c2, output_c3,
            input_c1, input_c2, input_c3, input_c4, input_c5, input_c6,
            input_c7, input_c8, input_c9, input_c10, input_c11, input_c12,
            input_c13,
            atc1_t0, atc1_t1, atc1_t2, atc1_t3, atc1_t4, atc1_t5, atc1_t6,
            atc1_t7, atc1_t8, atc1_t9, atc1_t10):
        self.filename = filename.strip().lower()
        self.minutes = minutes.strip()
        self.seconds = seconds.strip()
        self.time = time.strip()
        self.date = date.strip()
        self.status = status.strip()
        self.rapid = rapid.strip()
        self.feed = feed.strip()
        self.laser = laser.strip()
        self.axis1 = axis1.strip()
        self.axis2 = axis2.strip()
        self.axis3 = axis3.strip()
        self.axis4 = axis4.strip()
        self.axis5 = axis5.strip()
        self.axis6 = axis6.strip()
        self.output_c1 = output_c1.strip()
        self.output_c2 = output_c2.strip()
        self.output_c3 = output_c3.strip()
        self.input_c1 = input_c1.strip()
        self.input_c2 = input_c2.strip()
        self.input_c3 = input_c3.strip()
        self.input_c4 = input_c4.strip()
        self.input_c5 = input_c5.strip()
        self.input_c6 = input_c6.strip()
        self.input_c7 = input_c7.strip()
        self.input_c8 = input_c8.strip()
        self.input_c9 = input_c9.strip()
        self.input_c10 = input_c10.strip()
        self.input_c11 = input_c11.strip()
        self.input_c12 = input_c12.strip()
        self.input_c13 = input_c13.strip()
        self.atc1_t0 = atc1_t0.strip()
        self.atc1_t1 = atc1_t1.strip()
        self.atc1_t2 = atc1_t2.strip()
        self.atc1_t3 = atc1_t3.strip()
        self.atc1_t4 = atc1_t4.strip()
        self.atc1_t5 = atc1_t5.strip()
        self.atc1_t6 = atc1_t6.strip()
        self.atc1_t7 = atc1_t7.strip()
        self.atc1_t8 = atc1_t8.strip()
        self.atc1_t9 = atc1_t9.strip()
        self.atc1_t10 = atc1_t10.strip()

        # Non-csv-file attributes:
        self.duration_delta = self.calc_duration()
        self.duration = timedelta_str(self.duration_delta)
        self.end_time = parse_datetime(f'{self.date} {self.time}')
        self.start_time = self.end_time - self.duration_delta

    def __colr__(self):
        return C(' ').join(
            self.filename_fmt(),
            self.status_fmt(),
        )

    def __repr__(self):
        attrs = '  {}'.format(',\n  '.join(
            '{:>9}={!r}'.format(s, str(getattr(self, s, None)))
            for s in self.header
        ))
        return f'{type(self).__name__}(\n{attrs}\n)'

    def calc_duration(self):
        """ Return a timedelta representing the total run time for this
            command/file.
        """
        return (
            timedelta_from_str(self.rapid) +
            timedelta_from_str(self.feed) +
            timedelta_from_str(self.laser)
        )

    def command_type(self):
        """ Return the type of command as a string. """
        if self.is_user_file():
            return 'user file'
        if self.is_command_file():
            return 'command file'
        return 'command'

    def filename_fmt(self):
        """ Return a colorized version of the filename value. """
        if self.filename.lower().startswith('c:\\wincnc'):
            # A command file.
            args = self.colors['command_file']
        elif not self.filename.lower().startswith('c:\\'):
            # A command.
            args = self.colors['command']
        else:
            args = self.colors['filename']
        return C(self.filename, **args)

    @classmethod
    def from_line(cls, line):
        for row in csv.reader([line]):
            hl = cls(*row)
            return hl
        raise ValueError(f'No line to parse: {line!r}')

    def is_command(self):
        return not self.is_file()

    def is_command_file(self):
        return self.filename.lower().startswith('c:\\wincnc')

    def is_error(self):
        return 'ok' not in self.status.lower()

    def is_file(self):
        return self.filename.lower().startswith('c:\\')

    def is_user_file(self):
        return self.is_file() and (not self.is_command_file())

    def status_fmt(self):
        """ Return a colorized version of the status value. """
        args = self.colors['status']
        if self.is_error():
            args = self.colors['status_err']
        return C(self.status, **args)

    def time_str(self, dt=None, human=False, time_only=False):
        if dt is None:
            dt = self.start_time
        return time_str(dt, human=human, time_only=time_only)

    def treeview_tags(self):
        """ Return a tuple of ttk.Treeview tag names for this HistoryLine.
        """
        tags = [hash(self)]
        if self.is_error():
            tags.append('error')

        if self.is_user_file():
            tags.append('file')
        elif self.is_command_file():
            tags.append('file_command')
        else:
            tags.append('command')
        return tuple(tags)
