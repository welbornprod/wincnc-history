#!/usr/bin/env python3

""" WinCNC-History - GUI - Main
    Main GUI for WinCNC-History
    -Christopher Welborn 04-27-2019
"""

from .common import (
    WinTkBase,
)
from ..util.config import (
    ICONFILE,
    NAME,
    VERSION,
    WINCNC_FILE,
    config,
    debug,
    debug_err,
    print_err,
    tk,
    ttk,
)

from ..util.parser import (
    History,
    timedelta_str,
)


def load_gui():
    """ Load WinMain and run the event loop. """
    win = WinMain()  # noqa
    try:
        tk.mainloop()
    except Exception as ex:
        print_err('Main loop error: ({})\n{}'.format(
            type(ex).__name__,
            ex,
        ))
        return 1
    return 0


class WinMain(WinTkBase):
    """ Main window for WinCNC History. """
    default_geometry = '903x418+257+116'
    default_theme = 'clam'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.filepath = WINCNC_FILE
        # History instance set in `self.refresh()`.
        self.history = History()
        # Style for theme.
        self.style = ttk.Style()
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
        self.style.theme_use(usetheme)
        self.theme = usetheme
        self.style.configure('Treeview', font=('Monospace', 9), indent=10)
        self.style.configure('Treeview.Heading', font=('Arial', 12))
        self.title(f'{NAME} ({VERSION})')
        self.geometry(
            config.get('geometry', self.default_geometry) or
            self.default_geometry
        )
        # Fix message boxes.
        self.option_add('*Dialog.msg.font', 'Arial 10')

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
        self.tree_session.tag_configure('error', foreground='#680000')
        self.tree_session.tag_configure('session', foreground='#000068')
        self.tree_session.tag_configure('command', foreground='#000068')
        self.tree_session.tag_configure('file', foreground='#006800')
        self.tree_session.tag_configure('file_command', foreground='#006868')
        # Heading 0 should not stretch.
        self.tree_session.column('#0', stretch=False, width=175, anchor=tk.E)
        self.tree_session.column(0, stretch=False, width=100, anchor=tk.E)
        self.tree_session.column(1, stretch=True, anchor=tk.W)
        self.tree_session.columnconfigure(0, weight=0)
        self.tree_session.columnconfigure(1, weight=10)
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

    def destroy(self):
        config['geometry'] = self.geometry()
        config.save()
        super().destroy()

    def event_tree_session_select(self, event):
        index = self.tree_session.selection()
        selected = self.tree_session.item(index)
        if 'session' in selected['tags']:
            # Session line selected.
            self.clear_entries()
            return

        hsh = selected['tags'][0]
        hl = self.history.get_line(hsh)
        self.set_entries(hl)

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

    def set_entries(self, hl):
        """ Set all entry values from a HistoryLine. """
        for name in self.var_names:
            var = getattr(self, name)
            var.set(getattr(hl, name[4:]))
