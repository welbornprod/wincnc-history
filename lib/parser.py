#!/usr/bin/env python3
""" WinCNC-History - Libraries - Parser
    CSV parser and classes to hold information about the WinCNC history file.
    -Christopher Welborn 04-25-2019
"""
import csv
import datetime
from collections import UserList

from colr import Colr as C


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
                    session.end_time = session.parse_datetime(' '.join((
                        datestr.strip(),
                        timestr.strip(),
                    )))
                    sessions.append(session)
                    session = None
                    continue
                if session is not None:
                    session.append(HistoryLine.from_line(line))
        # Pick up any non-exits.
        if session is not None:
            sessions.append(session)
        return cls(sessions)


class SessionHistory(UserList):
    """ A collection of HistoryLines. """
    def __init__(self, iterable, start_time=None, end_time=None):
        super().__init__(iterable)
        self.start_time = start_time
        if isinstance(start_time, str):
            self.start_time = self.parse_datetime(start_time)

        self.end_time = end_time
        if isinstance(end_time, str):
            self.end_time = self.parse_datetime(end_time)

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

    @staticmethod
    def parse_datetime(s):
        """ Parse a datetime in the form 'm-d-y h:m:s'. """
        return datetime.datetime.strptime(s, '%m-%d-%y %H:%M:%S')

    @staticmethod
    def time_fmt(dt, time_args=None, date_args=None):
        """ Return a color formatted version of a datetime. """
        if not time_args:
            time_args = {'fore': 'blue'}
        if not date_args:
            date_args = time_args

        return datetime.datetime.strftime(
            dt,
            str(
                C(' ').join(
                    C('-').join(
                        C('%m', **time_args),
                        C('%d', **time_args),
                        C('%y', **time_args),
                    ),
                    C(':').join(
                        C('%H', **date_args),
                        C('%M', **date_args),
                        C('%S', **date_args),
                    ),
                )
            )
        )

    @staticmethod
    def time_str(dt):
        """ Return a stringified version of a datetime. """
        return datetime.strftime(dt, '%m-%d-%y %H:%M:%S')


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
        self.filename = filename
        self.minutes = minutes
        self.seconds = seconds
        self.time = time
        self.date = date
        self.status = status
        self.rapid = rapid
        self.feed = feed
        self.laser = laser
        self.axis1 = axis1
        self.axis2 = axis2
        self.axis3 = axis3
        self.axis4 = axis4
        self.axis5 = axis5
        self.axis6 = axis6
        self.output_c1 = output_c1
        self.output_c2 = output_c2
        self.output_c3 = output_c3
        self.input_c1 = input_c1
        self.input_c2 = input_c2
        self.input_c3 = input_c3
        self.input_c4 = input_c4
        self.input_c5 = input_c5
        self.input_c6 = input_c6
        self.input_c7 = input_c7
        self.input_c8 = input_c8
        self.input_c9 = input_c9
        self.input_c10 = input_c10
        self.input_c11 = input_c11
        self.input_c12 = input_c12
        self.input_c13 = input_c13
        self.atc1_t0 = atc1_t0
        self.atc1_t1 = atc1_t1
        self.atc1_t2 = atc1_t2
        self.atc1_t3 = atc1_t3
        self.atc1_t4 = atc1_t4
        self.atc1_t5 = atc1_t5
        self.atc1_t6 = atc1_t6
        self.atc1_t7 = atc1_t7
        self.atc1_t8 = atc1_t8
        self.atc1_t9 = atc1_t9
        self.atc1_t10 = atc1_t10

    def __colr__(self):
        return C(' ').join(
            self.filename_fmt(),
            self.status_fmt(),
        )

    def __str__(self):
        return ', '.join(
            str(getattr(self, s, None))
            for s in self.header
        )

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

    def status_fmt(self):
        """ Return a colorized version of the status value. """
        args = self.colors['status']
        if self.status != 'OK':
            args = self.colors['status_err']
        return C(self.status, **args)
