#!/usr/bin/env python3

""" WinCNC-History - GUI - Main
    Main GUI for WinCNC-History
    -Christopher Welborn 04-27-2019
"""

from .common import (
    WinTkBase,
    WinToolTipBase,
)
from ..util.config import (
    ICONFILE,
    NAME,
    VERSION,
    config,
    debug,
    debug_err,
    print_err,
    tk,
    ttk,
)

from ..util.parser import (
    History,
    time_str,
    timedelta_str,
)


def load_gui(filepath=None):
    """ Load WinMain and run the event loop. """
    win = WinMain(filepath=filepath)  # noqa
    try:
        tk.mainloop()
    except Exception as ex:
        print_err('Main loop error: ({})\n{}'.format(
            type(ex).__name__,
            ex,
        ))
        return 1
    return 0


class WinToolTipCommand(WinToolTipBase):
    """ A tooltip window for Commands. """
    def __init__(
            self, master=None, x=None, y=None, delay=1000, command=None,
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

        end_time = time_str(command.end_time, time_only=True)
        self.text = f'End Time: {end_time}'
        self.frm_main = ttk.Frame(
            self,
            relief=tk.GROOVE,
            borderwidth=1,
            padding='2 2 2 2',
            style='ToolTip.TFrame',
        )
        self.frm_main.pack(fill=tk.BOTH, expand=True)

        self.lbl = ttk.Label(
            self.frm_main,
            text=self.text,
            anchor=tk.CENTER,
            justify=tk.CENTER,
            width=len(self.text) + 1,
            style='ToolTip.TLabel',
        )
        self.lbl.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # MUST call this before calling the winfo_* methods!
        self.update_idletasks()
        self.set_geometry(
            x=x,
            y=y,
            width=self.frm_main.winfo_reqwidth(),
            height=self.frm_main.winfo_reqheight(),
        )


class WinToolTipSession(WinToolTipBase):
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
            ('actual_duration', 'Run Time:'),
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
            style='ToolTip.TLabel',
        )
        lblval.pack(
            side=tk.RIGHT,
            fill=tk.X,
            expand=True,
            anchor=tk.E,
        )
        setattr(self, f'lbl_{attr}_val', lblval)


class WinMain(WinTkBase):
    """ Main window for WinCNC History. """
    default_geometry = '903x418+257+116'
    default_theme = 'clam'

    def __init__(self, filepath=None):
        super().__init__()
        self.filepath = filepath or config.get('wincnc_file', None)

        # History instance set in `self.refresh()`.
        self.history = History()
        # Style for theme.
        self.style = ttk.Style()
        # Last "focused" row.
        self.last_focus = None
        # Delay for tooltips, in ms.
        self.tooltip_delay = 1250
        self.tooltip_kill_delay = 750

        # Callback id for cancelling tooltip.
        self.tooltip_cb_id = None
        # Tooltip window.
        self.win_tooltip = None

        # Set icon for main window and all children.
        try:
            self.main_icon = tk.PhotoImage(master=self, file=ICONFILE)
            self.iconphoto(True, self.main_icon)
        except Exception as ex:
            debug_err('Failed to set icon: {}\n{}'.format(ICONFILE, ex))
            self.main_icon = None
        # knownstyles = ('clam', 'alt', 'default', 'classic')
        self.known_themes = sorted(self.style.theme_names())
        usetheme = (
            config.get('theme', self.default_theme) or self.default_theme
        ).lower()
        if usetheme not in self.known_themes:
            debug_err(f'Invalid theme name: {usetheme}')
            debug_err(f'Using {self.default_theme!r}')
            themes = ', '.join(self.known_themes)
            debug(f'Known themes: {themes}')
            usetheme = self.default_theme
        self.theme = usetheme
        self.style.theme_use(self.theme)
        # Entry font is set in `_build_entry()`.
        self.style.configure(
            'TEntry',
            background=config.get('bg_entry', None) or '#F4F4F4',
        )
        self.style.configure(
            'TLabel',
            foreground=config.get('fg_label', None) or '#4C4C4C',
        )
        self.style.configure(
            'TLabelframe.Label',
            foreground=config.get('fg_label', None) or '#4C4C4C',
        )
        self.style.configure(
            'Treeview',
            background=config.get('bg_treeview', None) or '#F4F4F4',
            font=config.get('font_treeview', None) or ('Monospace', 9),
            indent=10
        )
        self.style.configure(
            'Treeview.Heading',
            foreground=config.get('fg_label', None) or '#4C4C4C',
            font=config.get('font_treeview_heading', None) or ('Arial', 12),
        )
        # Title
        self.title(f'{NAME} ({VERSION})')
        # Size
        self.geometry(
            config.get('geometry', None) or
            self.default_geometry
        )
        # Fix message boxes.
        self.option_add(
            '*Dialog.msg.font',
            config.get('font_dialog', None) or ('Arial', 10)
        )

        # Main frame.
        self.frm_main = ttk.Frame(self, padding='2 2 2 2')
        self.frm_main.pack(fill=tk.BOTH, expand=True)

        # Top frame.
        self.frm_top = ttk.Frame(self.frm_main)
        self.frm_top.pack(side=tk.TOP, fill=tk.X, expand=True)

        tree_height = 15
        # Build sessions frame
        self.frm_session = ttk.Frame(self.frm_top, padding='0 0 0 10')
        self.frm_session.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.tree_session = ttk.Treeview(
            self.frm_session,
            selectmode='browse',
            height=tree_height,
        )
        self.tree_session.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.tree_session.configure(
            columns=('duration', 'command'),
            show='tree headings',
        )
        self.tree_session.heading(
            '#0',
            anchor=tk.CENTER,
            text='Start Time:',
        )
        self.tree_session.heading(
            'duration',
            anchor=tk.CENTER,
            text='Duration:',
        )
        self.tree_session.heading(
            'command',
            anchor=tk.CENTER,
            text='Command:',
        )
        self.scroll_session = ttk.Scrollbar(
            self.frm_session,
            orient='vertical',
            command=self.tree_session.yview,
        )
        self.tree_session.configure(
            yscrollcommand=self.scroll_session.set
        )
        self.scroll_session.pack(side=tk.RIGHT, fill=tk.Y, expand=False)
        # Session tags
        self.tree_session.tag_configure(
            'error',
            foreground=config.get('fg_error', None) or '#5B0000'
        )
        self.tree_session.tag_configure(
            'session',
            foreground=config.get('fg_session', None) or '#002050'
        )
        self.tree_session.tag_configure(
            'command',
            foreground=config.get('fg_command', None) or '#002050'
        )
        self.tree_session.tag_configure(
            'file',
            foreground=config.get('fg_file', None) or '#004C13'
        )
        self.tree_session.tag_configure(
            'file_command',
            foreground=config.get('fg_file_command', None) or '#0C4A46'
        )
        self.tree_session.tag_configure(
            'focused',
            background=config.get('bg_focus', None) or '#DEDEDE'
        )

        # Heading 0 should not stretch.
        self.tree_session.column('#0', stretch=False, width=175, anchor=tk.E)
        self.tree_session.column(0, stretch=False, width=100, anchor=tk.E)
        self.tree_session.column(1, stretch=True, anchor=tk.W)
        self.tree_session.columnconfigure(0, weight=0)
        self.tree_session.columnconfigure(1, weight=10)

        # self.bal_session.set_silent('This is a ballong mang.')
        # Build info frame.
        self.frm_bottom = ttk.Frame(self.frm_main)
        self.frm_bottom.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)
        # Collection of StringVar names to update the info.
        # These are set in _build_entry(), and made immutable after init.
        self.var_names = []
        # Top section (basic and output)
        self.frm_section = ttk.Frame(self.frm_bottom)
        self.frm_section.pack(anchor=tk.W, fill=None, expand=False)
        # Basic
        self._build_frame(
            self.frm_section,
            'basic',
            side=tk.LEFT,
            text='Status and Movement Types (min:sec):',
        )
        for attr in ('status', 'rapid', 'feed', 'laser'):
            self._build_entry(
                self.frm_basic,
                attr,
                entrywidth=24 if attr == 'status' else 5,
            )
        # Output
        self._build_frame(self.frm_section, 'output', side=tk.RIGHT)
        for attr in ('output_c1', 'output_c2', 'output_c3'):
            self._build_entry(
                self.frm_output,
                attr,
                lbltext=attr.split('_')[-1].title(),
            )
        # Other sections
        # Axis
        self._build_frame(
            self.frm_bottom,
            'axis',
            text='Axis (inches):',
        )
        for attr in (f'axis{x}' for x in range(1, 7)):
            self._build_entry(
                self.frm_axis,
                attr,
                lbltext=attr[4:],
                entrywidth=9,
            )
        # Input
        self._build_frame(self.frm_bottom, 'input')
        for attr in tuple(f'input_c{x}' for x in range(1, 14)):
            self._build_entry(
                self.frm_input,
                attr,
                lbltext=attr.split('_')[-1].title(),
            )
        # ATC1
        self._build_frame(self.frm_bottom, 'atc1', text='ATC1 (min:sec):')
        for attr in tuple(f'atc1_t{x}' for x in range(11)):
            self._build_entry(
                self.frm_atc1,
                attr,
                lbltext=attr.split('_')[-1].title(),
            )

        # Make var_names immutable.
        self.var_names = tuple(self.var_names)
        # Bind events.
        self.tree_session.bind(
            '<<TreeviewSelect>>',
            self.event_tree_session_select,
        )
        self.tree_session.bind(
            '<Button-3>',
            self.event_tree_session_button3,
        )
        self.tree_session.bind(
            '<Motion>',
            self.event_tree_session_motion,
        )
        if self.filepath is None:
            self.show_error('No WinCNC.csv file to use.', fatal=True)
        else:
            # Load file.
            self.refresh()

    def _build_entry(self, parent, attr, lbltext=None, entrywidth=5):
        """ Build a single Label/Entry pair wrapped in a frame. """
        subfrmname = f'frm_{attr}'
        varname = f'var_{attr}'
        lblname = f'lbl_{attr}'
        entryname = f'entry_{attr}'

        subfrm = ttk.Frame(parent, relief=None)
        setattr(self, subfrmname, subfrm)
        subfrm.pack(side=tk.LEFT, anchor=tk.W, expand=True, padx=5)
        if not lbltext:
            lbltext = attr.title()
        lbl = ttk.Label(subfrm, text=f'{lbltext}:')
        setattr(self, lblname, lbl)
        lbl.pack(side=tk.LEFT, anchor=tk.W, expand=False)
        var = tk.StringVar(subfrm)
        setattr(self, varname, var)
        entry = ttk.Entry(
            subfrm,
            width=entrywidth,
            state='readonly',
            textvariable=var,
            style='TEntry',
            font=config.get('font_entry', None) or ('Monospace', 9),
        )
        setattr(self, entryname, entry)
        entry.pack(side=tk.RIGHT, anchor=tk.E, expand=False)
        self.var_names.append(varname)

    def _build_frame(self, parent, attr, text=None, side=None):
        """ Build a section frame for the info entries. """
        frm = ttk.LabelFrame(
            parent,
            padding='2 5 2 5',
            text=f'{attr.title()} (min:sec):' if text is None else text,
            labelanchor=tk.NW,
            relief=tk.GROOVE,
        )
        setattr(self, f'frm_{attr}', frm)
        frm.pack(
            side=tk.TOP if side is None else side,
            anchor=tk.W,
            fill=None,
            padx=5,
            pady=5,
        )

    def clear_entry(self, entry):
        entry.delete(0, tk.END)

    def clear_entries(self):
        """ Clear all the entries. """
        for name in self.var_names:
            var = getattr(self, name)
            var.set('')

    def clear_treeview(self, treeview):
        treeview.delete(*treeview.get_children())

    def destroy(self, save_config=True):
        if save_config:
            config['geometry'] = self.geometry()
            config.save()
        super().destroy()

    def event_tooltip(self, itemid):
        """ Fires after `self.tooltip_delay` milliseconds when hovering over
            an item in `self.tree_session`.
        """
        self.tooltip_cb_id = None
        selected = self.tree_session.item(itemid)
        hsh = selected['tags'][0]
        if 'session' not in selected['tags']:
            # Single line item.
            return self.show_tooltip_command(hsh)

        return self.show_tooltip_session(hsh)

    def event_tree_session_button3(self, event):
        """ Handle r-click. """
        itemid = self.tree_session.identify_row(event.y)
        self.event_tooltip(itemid)

    def event_tree_session_motion(self, event):
        """ Highlights the row underneath the mouse. """
        itemid = self.tree_session.identify_row(event.y)
        if itemid != self.last_focus:
            self.focus_remove()
            # Focus the new item.
            self.focus_set(itemid)
        # Kill tooltip on this motion.
        if self.win_tooltip is not None:
            self.win_tooltip.start_destroy()

    def event_tree_session_select(self, event):
        """ Populates all the entries for the selected item. """
        index = self.tree_session.selection()
        selected = self.tree_session.item(index)
        if 'session' in selected['tags']:
            # Session line selected.
            self.clear_entries()
            return

        hsh = selected['tags'][0]
        hl = self.history.get_command(hsh)
        self.set_entries(hl)

    def focus_remove(self):
        if not self.last_focus:
            return

        # Un-focus last focused item.
        self.tag_remove(self.last_focus, 'focused')

        # Cancel tooltip callback if it has not fired.
        if self.tooltip_cb_id is not None:
            self.after_cancel(self.tooltip_cb_id)

    def focus_set(self, itemid):
        """ Set focus to a row, by item id. """
        if itemid == self.last_focus:
            return
        self.tag_add(itemid, 'focused')
        self.last_focus = itemid

    def refresh(self):
        """ Read the WinCNC file and build the session/command trees. """
        self.clear_treeview(self.tree_session)

        self.history = History.from_file(self.filepath)
        if not self.history:
            self.show_error(f'No lines from history file: {self.filepath}')
            return

        for session in self.history:
            sessiontext = f'Status: {session.last_status()}'
            if session.duration_delta:
                sessionduration = session.duration
            else:
                sessionduration = ''
            sessionid = self.tree_session.insert(
                '',
                tk.END,
                values=(sessionduration, sessiontext, ),
                text=session.time_str(human=True),
                tags=session.treeview_tags(),
            )
            for hl in session:
                itemduration = timedelta_str(hl.duration_delta, short=True)
                statustext = hl.status.split()[0]
                timetext = hl.time_str(time_only=True)

                self.tree_session.insert(
                    sessionid,
                    tk.END,
                    values=(itemduration, hl.filename, ),
                    text=f'{timetext} - {statustext}',
                    tags=hl.treeview_tags(),
                )
        # Select last history item.
        children = self.tree_session.get_children()
        if children:
            lastsessionid = children[-1]
            self.tree_session.see(lastsessionid)
            lastlines = self.tree_session.get_children(item=lastsessionid)
            if lastlines:
                lastlineid = lastlines[-1]
                self.tree_session.see(lastlineid)
                self.tree_session.selection_set(lastlineid)

    def reset_win_tooltip(self):
        """ Set win_tooltip to None. This is a callback for WinToolTip*. """
        self.win_tooltip = None

    def set_entries(self, hl):
        """ Set all entry values from a Command. """
        for name in self.var_names:
            var = getattr(self, name)
            var.set(getattr(hl, name[4:]))

    def show_tooltip_command(self, hsh):
        if self.win_tooltip is not None:
            return
        try:
            command = self.history.get_command(hsh)
        except ValueError:
            # No real item was focused.
            return
        self.update_idletasks()
        self.win_tooltip = WinToolTipCommand(
            self,
            x=self.winfo_pointerx(),
            y=self.winfo_pointery(),
            delay=self.tooltip_kill_delay,
            command=command,
            destroy_cb=self.reset_win_tooltip,
        )

    def show_tooltip_session(self, hsh):
        if self.win_tooltip is not None:
            return
        try:
            session = self.history.get_session(hsh)
        except ValueError:
            # No real item was focused.
            return
        self.update_idletasks()
        self.win_tooltip = WinToolTipSession(
            self,
            x=self.winfo_pointerx(),
            y=self.winfo_pointery(),
            delay=self.tooltip_kill_delay,
            session=session,
            destroy_cb=self.reset_win_tooltip,
        )

    def tag_add(self, itemid, tag):
        """ Add a tag to a treeview item, by item id. """
        tags = self.tree_session.item(itemid)['tags']
        if not tags:
            # Sometimes tags is an empty str.
            self.tree_session.item(itemid, tags=[tag])
            return

        if tag not in tags:
            tags.append(tag)
        self.tree_session.item(itemid, tags=tags)

    def tag_remove(self, itemid, tag):
        """ Remove a tag from a treeview item, by item id. """
        item = self.tree_session.item(itemid)
        tags = item['tags']
        try:
            tags.remove(tag)
        except ValueError:
            pass
        else:
            self.tree_session.item(self.last_focus, tags=tags)
