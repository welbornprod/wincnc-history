#!/usr/bin/env python3

""" WinCNC-History - GUI - Main
    Main GUI for WinCNC-History
    -Christopher Welborn 04-27-2019
"""

from .common import (
    WinTkBase,
)
from ..util.config import (
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

        self.style = ttk.Style()

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
        self.tree_session.configure(columns=('session', ), show='tree headings')
        self.tree_session.heading(
            'session',
            anchor=tk.W,
            text='',
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
        self.tree_session.column('#0', stretch=False, anchor=tk.E)
        self.tree_session.column(0, stretch=True)

        # Build info frame.
        self.frm_bottom = ttk.Frame(self.frm_main)
        self.frm_bottom.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)

        info_sections = (
            ('basic', ('status', 'rapid', 'feed', 'laser')),
            ('axis', ('axis1', 'axis2', 'axis3', 'axis4', 'axis5', 'axis6')),
            ('output', ('output_c1', 'output_c2', 'output_c3')),
            ('input', tuple(f'input_c{x}' for x in range(1, 14))),
            ('atc', tuple(f'atc1_t{x}' for x in range(11)))
        )
        self.frm_section = ttk.Frame(self.frm_bottom)
        self.frm_section.pack(anchor=tk.W, fill=None, expand=False)
        assigned_frms = {
            'basic': {
                'side': tk.LEFT,
                'frame': self.frm_section,
            },
            'axis': {
                'side': tk.TOP,
            },
            'output': {
                'side': tk.RIGHT,
                'frame': self.frm_section,
            },
            'input': {
                'side': tk.TOP,
            },
        }
        for section, section_attrs in info_sections:
            frmname = f'frm_{section}'
            sectioninfo = assigned_frms.get(section, {})
            parent = sectioninfo.get('frame', self.frm_bottom)
            side = sectioninfo.get('side', tk.LEFT)
            frm = ttk.LabelFrame(
                parent,
                padding='2 2 2 2',
                text=f'{section.title()}:'
            )
            setattr(self, frmname, frm)
            frm.pack(side=side, anchor=tk.W, fill=None, padx=5, pady=5)
            for i, attr in enumerate(section_attrs):
                subfrmname = f'frm_{attr}'
                varname = f'var_{attr}'
                lblname = f'lbl_{attr}'
                entryname = f'entry_{attr}'
                subfrm = ttk.Frame(frm)
                setattr(self, subfrmname, subfrm)

                subfrm.pack(side=tk.LEFT, anchor=tk.W, expand=True, padx=5)
                lbltext = attr.split('_')[-1]
                if lbltext.startswith(section):
                    lbltext = lbltext.lstrip(section)
                lbl = ttk.Label(subfrm, text=f'{lbltext}:')
                setattr(self, lblname, lbl)
                lbl.pack(side=tk.LEFT, anchor=tk.W, expand=False)
                var = tk.StringVar(subfrm)
                setattr(self, varname, var)
                entrywidth = 5
                if section == 'axis':
                    entrywidth = 9
                elif attr == 'status':
                    entrywidth = 24
                entry = ttk.Entry(
                    subfrm,
                    width=entrywidth,
                    state='readonly',
                    textvariable=var,
                )
                setattr(self, entryname, entry)
                entry.pack(side=tk.RIGHT, anchor=tk.E, expand=False)

        # Bind events.
        self.tree_session.bind(
            '<<TreeviewSelect>>',
            self.event_tree_session_select,
        )
        self.refresh()

    def clear_entry(self, entry):
        entry.delete(0, tk.END)

    def clear_entries(self):
        """ Clear all the entries. """
        entrynames = [s for s in dir(self) if s.startswith('var_')]
        for name in entrynames:
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
            sessionid = self.tree_session.insert(
                '',
                tk.END,
                values=(f'Status: {session.last_status()}', ),
                text=session.time_str(human=True),
                tags=session.treeview_tags(),
            )
            for hl in session:
                self.tree_session.insert(
                    sessionid,
                    tk.END,
                    values=(hl.filename, ),
                    text=hl.status,
                    tags=hl.treeview_tags(),
                )

        children = self.tree_session.get_children()
        if children:
            self.tree_session.selection_set(children[-1])

    def set_entries(self, hl):
        """ Set all entry values from a HistoryLine. """
        for name in [s for s in dir(self) if s.startswith('var_')]:
            var = getattr(self, name)
            var.set(getattr(hl, name[4:]))
