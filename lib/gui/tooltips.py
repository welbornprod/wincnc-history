#!/usr/bin/env python3

""" WinCNC-History - GUI - ToolTips
    ToolTips for WinCNC-History
    -Christopher Welborn 04-29-2019
"""

from ..util.config import (
    config,
)
from ..util.parser import (
    time_str,
    timedelta_str,
)
from .common import (
    WinToolTipBase,
    tk,
    ttk,
)


font_key = config.get('font_tooltip_key', None) or ('Arial', 10)
font_val = config.get('font_tooltip_value', None) or ('Arial', 10, 'bold')


class WinToolTipCommon(WinToolTipBase):
    """ Common methods for all WinToolTips, that don't effect
        WinTopLevelBase.__init__.
    """
    def __init__(
            self, master=None, x=None, y=None, delay=1000, destroy_cb=None):
        super().__init__(
            master=master,
            x=x,
            y=y,
            delay=delay,
            destroy_cb=destroy_cb
        )
        self.max_label_len = 9
        self.max_value_len = 10

    def _build_item(self, attr, label, value):
        frm = ttk.Frame(
            self.frm_main,
            padding='2 2 2 2',
            style='ToolTip.TFrame',
        )
        frm.pack(fill=tk.X, expand=True)
        setattr(self, f'frm_{attr}', frm)

        lblkey = ttk.Label(
            frm,
            text=label,
            width=self.max_label_len,
            justify=tk.RIGHT,
            anchor=tk.E,
            font=font_key,
            style='ToolTip.TLabel',
        )
        lblkey.pack(
            side=tk.LEFT,
            fill=tk.X,
            expand=True,
            anchor=tk.W,
        )
        setattr(self, f'lbl_{attr}_key', lblkey)

        val = str(value)
        lblval = ttk.Label(
            frm,
            text=val,
            width=self.max_value_len,
            justify=tk.LEFT,
            font=font_val,
            style='ToolTip.TLabel',
        )
        lblval.pack(
            side=tk.RIGHT,
            fill=tk.X,
            expand=True,
            anchor=tk.E,
        )
        setattr(self, f'lbl_{attr}_val', lblval)


class WinToolTipCommand(WinToolTipCommon):
    """ A tooltip window for Commands. """
    def __init__(
            self, master=None, x=None, y=None, delay=1000,
            command=None, session=None, destroy_cb=None):
        if master is None:
            raise ValueError(f'No master provided, got: {master!r}')
        super().__init__(
            master=master,
            x=x,
            y=y,
            delay=delay,
            destroy_cb=destroy_cb,
        )

        self.frm_main = ttk.Frame(
            self,
            relief=tk.GROOVE,
            borderwidth=1,
            padding='2 2 2 2',
            style='ToolTip.TFrame',
        )
        self.frm_main.pack(fill=tk.BOTH, expand=True)

        time_before = timedelta_str(session.time_before(command), short=True)
        time_after = timedelta_str(session.time_after(command), short=True)

        end_time = time_str(command.end_time, time_only=True)
        self._build_item('end_time', 'End Time:', end_time)
        self._build_item('time_before', 'Before:', time_before)
        self._build_item('time_after', 'After:', time_after)

        # MUST call this before calling the winfo_* methods!
        self.update_idletasks()
        self.set_geometry(
            x=x,
            y=y,
            width=self.frm_main.winfo_reqwidth(),
            height=self.frm_main.winfo_reqheight(),
        )


class WinToolTipSession(WinToolTipCommon):
    """ A tooltip window for Sessions. """
    def __init__(
            self, master=None, x=None, y=None, delay=1000, session=None,
            destroy_cb=None):
        if master is None:
            raise ValueError(f'No master provided, got: {master!r}')
        super().__init__(
            master=master,
            x=x,
            y=y,
            delay=delay,
            destroy_cb=destroy_cb,
        )

        self.frm_main = ttk.Frame(
            self,
            relief=tk.GROOVE,
            borderwidth=1,
            padding='2 2 2 2',
            style='ToolTip.TFrame',
        )
        self.frm_main.pack(fill=tk.BOTH, expand=True)
        times = (
            ('start_time', 'Start Time:'),
            ('end_time', 'End Time:'),
        )
        time_vals = {
            attr: time_str(getattr(session, attr), human=True)
            for attr, _ in times
        }
        max_val_key = max(time_vals, key=lambda k: len(str(time_vals[k])))
        self.max_value_len = len(time_vals[max_val_key])
        info = (

            ('count', 'Commands:'),
            ('count_commands', 'System Commands:'),
            ('count_command_files', 'Command Files:'),
            ('count_files', 'User Files:'),
            ('actual_duration', 'Session Time:'),
            ('end_of_day_duration', 'End of Day:'),
            ('avg_duration', 'Average Run Time:'),
            ('between_duration', 'Time Between:'),
            ('avg_between_duration', 'Average Time Between:'),
        )
        self.max_label_len = len(max(info, key=lambda t: len(t[1]))[1])
        info_vals = {
            attr: getattr(session, attr)
            for attr, _ in info
        }
        for attr, label in times:
            self._build_item(attr, label, time_vals[attr])
        for attr, label in info:
            self._build_item(attr, label, info_vals[attr])

        # MUST call this before calling the winfo_* methods!
        self.update_idletasks()
        self.set_geometry(
            x=x,
            y=y,
            width=self.frm_main.winfo_reqwidth(),
            height=self.frm_main.winfo_reqheight(),
        )
