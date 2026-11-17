"""
gui.py
------
One window for the whole project: pick a maze, a problem and an algorithm,
press Run, and watch the search. Every run is added to the results table, and
"Compare all" produces the table for the report (see the "Text log" tab).

    python gui.py

This file is only a convenience on top of runner.py. It is not part of the
submission and does not change any of the provided files.
"""

import tkinter as tk
from tkinter import ttk

import maze as mazeModule
import runner
from display import (COLORS, HEAT_EARLY, HEAT_LATE, RUNNER, TRAIL, KEY_COLOR,
                     _blend, pathPositions)

# What the dropdowns show -> the short names runner.py understands.
ALGORITHMS = [
    ('Depth-first search (Q1)', 'dfs'),
    ('Breadth-first search (Q2)', 'bfs'),
    ('Depth-limited search (Q3)', 'dls'),
    ('Iterative deepening search (Q4)', 'ids'),
    ('Uniform-cost search (Q5)', 'ucs'),
    ('Greedy best-first search (Q6)', 'gbfs'),
    ('A* search (Q7)', 'astar'),
    ('Always go right (example)', 'right'),
]
PROBLEMS = [
    ('Reach the exit', 'maze'),
    ('Collect all pieces, then exit (Q8-Q9)', 'keys'),
]
# A heuristic only makes sense for the problem it was written for.
HEURISTICS = {
    'maze': ['manhattan', 'euclidean', 'null'],
    'keys': ['keyhunt', 'null'],
}

# Colours of the window itself (the maze colours come from display.py).
WINDOW = '#161b18'
SIDEBAR = '#1f2622'
CARD = '#262f2a'
FIELD = '#2f3a34'
BORDER = '#3b4841'
TEXT = '#ecefe9'
DIM = '#98a59d'
ACCENT = '#e0a526'
GOOD = '#6fcf7f'
WARN = '#f0b849'
BAD = '#f0736a'

FONT = 'Segoe UI'
MONO = 'Consolas'

RESULT_COLUMNS = [
    # (id, heading, width, anchor)
    ('maze', 'Maze', 150, 'w'),
    ('algorithm', 'Algorithm', 250, 'w'),
    ('result', 'Result', 100, 'w'),
    ('cost', 'Path cost', 80, 'e'),
    ('steps', 'Steps', 70, 'e'),
    ('expanded', 'Expanded', 90, 'e'),
    ('time', 'Time (s)', 80, 'e'),
]


class MazeRunnerApp:
    def __init__(self, root):
        self.root = root
        root.title("Maze Runner - Escape The Maze")
        root.configure(bg=WINDOW)
        root.geometry('1240x720')
        root.minsize(980, 620)

        self.maze = None
        self.cells = {}          # (row, col) -> canvas rectangle
        self.keyItems = {}       # (row, col) -> canvas diamond
        self.runId = 0           # increases with every run, so old animations stop
        self.skip = False
        self.lastSearch = None   # (expanded cells, path) of the run on screen
        self.resizeJob = None

        self._setupStyles()
        root.columnconfigure(1, weight=1)
        root.rowconfigure(0, weight=1)
        self._buildSidebar()
        self._buildMain()

        root.bind('<space>', lambda event: self.skipAnimation())
        root.bind('<Return>', lambda event: self.run())
        self.onMazeChanged()

    # ------------------------------------------------------------------
    # Look of the widgets
    # ------------------------------------------------------------------
    def _setupStyles(self):
        style = ttk.Style(self.root)
        style.theme_use('clam')

        style.configure('TCombobox', fieldbackground=FIELD, background=FIELD,
                        foreground=TEXT, arrowcolor=TEXT, bordercolor=BORDER,
                        lightcolor=FIELD, darkcolor=FIELD, padding=5)
        style.map('TCombobox',
                  fieldbackground=[('disabled', SIDEBAR), ('readonly', FIELD)],
                  foreground=[('disabled', '#5f6b64'), ('readonly', TEXT)],
                  selectbackground=[('readonly', FIELD)],
                  selectforeground=[('readonly', TEXT)],
                  arrowcolor=[('disabled', '#5f6b64')])
        # The list that drops down from a combobox is a plain Tk listbox.
        self.root.option_add('*TCombobox*Listbox.background', FIELD)
        self.root.option_add('*TCombobox*Listbox.foreground', TEXT)
        self.root.option_add('*TCombobox*Listbox.selectBackground', ACCENT)
        self.root.option_add('*TCombobox*Listbox.selectForeground', '#1a1a1a')
        self.root.option_add('*TCombobox*Listbox.font', (FONT, 10))

        style.configure('TEntry', fieldbackground=FIELD, foreground=TEXT,
                        insertcolor=TEXT, bordercolor=BORDER, lightcolor=FIELD,
                        darkcolor=FIELD, padding=5)
        style.map('TEntry', fieldbackground=[('disabled', SIDEBAR)],
                  foreground=[('disabled', '#5f6b64')])

        style.configure('TButton', background=FIELD, foreground=TEXT,
                        bordercolor=BORDER, lightcolor=FIELD, darkcolor=FIELD,
                        font=(FONT, 10), padding=(10, 7))
        style.map('TButton', background=[('disabled', SIDEBAR), ('active', BORDER)],
                  foreground=[('disabled', '#5f6b64')])
        style.configure('Primary.TButton', background=ACCENT, foreground='#1a1a1a',
                        bordercolor=ACCENT, lightcolor=ACCENT, darkcolor=ACCENT,
                        font=(FONT, 11, 'bold'), padding=(10, 9))
        style.map('Primary.TButton',
                  background=[('disabled', '#6d5a2a'), ('active', '#f0b849')],
                  foreground=[('disabled', '#3a3a3a')])

        style.configure('TCheckbutton', background=SIDEBAR, foreground=TEXT,
                        font=(FONT, 10), indicatorcolor=FIELD)
        style.map('TCheckbutton', background=[('active', SIDEBAR)],
                  indicatorcolor=[('selected', ACCENT)])

        style.configure('Small.TButton', font=(FONT, 9), padding=(12, 3))

        style.configure('TNotebook', background=WINDOW, borderwidth=0, tabmargins=0,
                        bordercolor=WINDOW, lightcolor=WINDOW, darkcolor=WINDOW)
        style.configure('TNotebook.Tab', background=WINDOW, foreground=DIM,
                        font=(FONT, 10), padding=(14, 6), borderwidth=0,
                        bordercolor=WINDOW, lightcolor=WINDOW, darkcolor=WINDOW,
                        focuscolor=CARD)
        style.map('TNotebook.Tab', background=[('selected', CARD)],
                  foreground=[('selected', TEXT)],
                  lightcolor=[('selected', CARD)], bordercolor=[('selected', CARD)])

        style.configure('Treeview', background=CARD, fieldbackground=CARD,
                        foreground=TEXT, font=(FONT, 10), rowheight=24, borderwidth=0,
                        bordercolor=CARD, lightcolor=CARD, darkcolor=CARD)
        style.map('Treeview', background=[('selected', BORDER)],
                  foreground=[('selected', TEXT)])
        style.configure('Treeview.Heading', background=FIELD, foreground=DIM,
                        font=(FONT, 9, 'bold'), borderwidth=0, padding=(6, 4))
        style.map('Treeview.Heading', background=[('active', FIELD)])

        style.configure('Vertical.TScrollbar', background=FIELD, troughcolor=CARD,
                        bordercolor=CARD, arrowcolor=DIM, lightcolor=FIELD, darkcolor=FIELD)

    # ------------------------------------------------------------------
    # Left side: the controls
    # ------------------------------------------------------------------
    def _buildSidebar(self):
        side = tk.Frame(self.root, bg=SIDEBAR, padx=18, pady=16, width=310)
        side.grid(row=0, column=0, sticky='ns')
        side.pack_propagate(False)

        tk.Label(side, text="Escape The Maze", bg=SIDEBAR, fg=TEXT,
                 font=(FONT, 16, 'bold')).pack(anchor='w')
        tk.Label(side, text="Classical search, Q1 to Q9", bg=SIDEBAR, fg=DIM,
                 font=(FONT, 9)).pack(anchor='w')

        def label(text):
            tk.Label(side, text=text.upper(), bg=SIDEBAR, fg=DIM, anchor='w',
                     font=(FONT, 8, 'bold')).pack(fill='x', pady=(12, 3))

        def dropdown(values):
            box = ttk.Combobox(side, values=values, state='readonly', font=(FONT, 10))
            box.pack(fill='x')
            return box

        label("Maze")
        self.mazeBox = dropdown(mazeModule.availableMazes())
        self.mazeBox.set('maze_medium' if 'maze_medium' in self.mazeBox['values']
                         else self.mazeBox['values'][0])
        self.mazeBox.bind('<<ComboboxSelected>>', lambda event: self.onMazeChanged())

        label("Problem")
        self.problemBox = dropdown([])
        self.problemBox.bind('<<ComboboxSelected>>', lambda event: self.onProblemChanged())

        label("Algorithm")
        self.algorithmBox = dropdown([name for name, short in ALGORITHMS])
        self.algorithmBox.set(ALGORITHMS[1][0])
        self.algorithmBox.bind('<<ComboboxSelected>>', lambda event: self.onAlgorithmChanged())

        label("Heuristic  (Greedy and A* only)")
        self.heuristicBox = dropdown([])

        # Two small number fields side by side.
        numbers = tk.Frame(side, bg=SIDEBAR)
        numbers.pack(fill='x', pady=(12, 0))
        numbers.columnconfigure(0, weight=1, uniform='numbers')
        numbers.columnconfigure(1, weight=1, uniform='numbers')
        tk.Label(numbers, text="DEPTH LIMIT  (DLS)", bg=SIDEBAR, fg=DIM, anchor='w',
                 font=(FONT, 8, 'bold')).grid(row=0, column=0, sticky='w', pady=(0, 3))
        tk.Label(numbers, text="TIME LIMIT  (SEC)", bg=SIDEBAR, fg=DIM, anchor='w',
                 font=(FONT, 8, 'bold')).grid(row=0, column=1, sticky='w', padx=(8, 0), pady=(0, 3))
        self.depthEntry = ttk.Entry(numbers, font=(FONT, 10), width=8)
        self.depthEntry.insert(0, '60')
        self.depthEntry.grid(row=1, column=0, sticky='ew')
        self.timeoutEntry = ttk.Entry(numbers, font=(FONT, 10), width=8)
        self.timeoutEntry.insert(0, '10')
        self.timeoutEntry.grid(row=1, column=1, sticky='ew', padx=(8, 0))

        self.animateVar = tk.BooleanVar(value=True)
        ttk.Checkbutton(side, text="Animate the search",
                        variable=self.animateVar).pack(anchor='w', pady=(14, 0))

        self.runButton = ttk.Button(side, text="Run search", style='Primary.TButton',
                                    command=self.run)
        self.runButton.pack(fill='x', pady=(14, 6))
        self.compareButton = ttk.Button(side, text="Compare all algorithms",
                                        command=self.compareAll)
        self.compareButton.pack(fill='x')
        ttk.Button(side, text="Skip animation",
                   command=self.skipAnimation).pack(fill='x', pady=(6, 0))
        tk.Label(side, text="Enter: run      Space: skip animation", bg=SIDEBAR,
                 fg=DIM, font=(FONT, 8)).pack(anchor='w', pady=(6, 0))

    def _buildLegend(self, parent):
        """One line under the maze that says what the colours mean."""
        legend = tk.Frame(parent, bg=WINDOW)
        entries = [
            (HEAT_EARLY, "Expanded early"), (HEAT_LATE, "Expanded late"),
            (TRAIL, "Path"), (KEY_COLOR, "Code piece"),
            (COLORS[mazeModule.IVY], "Ivy (3)"), (COLORS[mazeModule.GRIEVER], "Griever (10)"),
        ]
        for color, text in entries:
            tk.Frame(legend, bg=color, width=11, height=11).pack(side='left', padx=(0, 5))
            tk.Label(legend, text=text, bg=WINDOW, fg=DIM,
                     font=(FONT, 9)).pack(side='left', padx=(0, 14))
        return legend

    # ------------------------------------------------------------------
    # Right side: title, numbers, maze, results
    # ------------------------------------------------------------------
    def _buildMain(self):
        main = tk.Frame(self.root, bg=WINDOW, padx=16, pady=14)
        main.grid(row=0, column=1, sticky='nsew')
        main.columnconfigure(0, weight=1)
        main.rowconfigure(2, weight=1)      # the maze takes the spare room

        # Title of the maze on screen
        self.titleLabel = tk.Label(main, bg=WINDOW, fg=TEXT, anchor='w', font=(FONT, 13, 'bold'))
        self.titleLabel.grid(row=0, column=0, sticky='ew')

        # A row of cards with the numbers of the last run
        cards = tk.Frame(main, bg=WINDOW)
        cards.grid(row=1, column=0, sticky='ew', pady=(10, 10))
        self.cards = {}
        names = [('result', "Result"), ('cost', "Path cost"), ('steps', "Steps"),
                 ('expanded', "Expanded"), ('time', "Search time")]
        for i, (key, title) in enumerate(names):
            cards.columnconfigure(i, weight=1, uniform='cards')
            card = tk.Frame(cards, bg=CARD, padx=12, pady=8)
            card.grid(row=0, column=i, sticky='ew', padx=(0 if i == 0 else 8, 0))
            tk.Label(card, text=title.upper(), bg=CARD, fg=DIM, anchor='w',
                     font=(FONT, 8, 'bold')).pack(fill='x')
            value = tk.Label(card, text="-", bg=CARD, fg=TEXT, anchor='w',
                             font=(FONT, 15, 'bold'))
            value.pack(fill='x')
            self.cards[key] = value

        # The maze
        self.canvas = tk.Canvas(main, bg=COLORS[mazeModule.WALL], highlightthickness=0,
                                width=600, height=300)
        self.canvas.grid(row=2, column=0, sticky='nsew')
        self.canvas.bind('<Configure>', self.onCanvasResized)
        self._buildLegend(main).grid(row=3, column=0, sticky='w', pady=(6, 0))

        # Results: a table of every run, and the same thing as plain text
        bottom = tk.Frame(main, bg=WINDOW)
        bottom.grid(row=4, column=0, sticky='ew', pady=(8, 0))
        bottom.columnconfigure(0, weight=1)
        self.tabs = ttk.Notebook(bottom, height=160)
        self.tabs.grid(row=0, column=0, sticky='ew')
        ttk.Button(bottom, text="Clear", style='Small.TButton',
                   command=self.clearOutput).place(relx=1.0, y=2, anchor='ne')

        tableFrame = tk.Frame(self.tabs, bg=CARD)
        self.table = ttk.Treeview(tableFrame, columns=[c[0] for c in RESULT_COLUMNS],
                                  show='headings', selectmode='browse')
        for name, heading, width, anchor in RESULT_COLUMNS:
            self.table.heading(name, text=heading, anchor=anchor)
            self.table.column(name, width=width, anchor=anchor, stretch=(name == 'algorithm'))
        self.table.tag_configure('escaped', foreground=TEXT)
        self.table.tag_configure('cutoff', foreground=WARN)
        self.table.tag_configure('bad', foreground=BAD)
        tableScroll = ttk.Scrollbar(tableFrame, command=self.table.yview)
        self.table.configure(yscrollcommand=tableScroll.set)
        tableScroll.pack(side='right', fill='y')
        self.table.pack(side='left', fill='both', expand=True)
        self.tabs.add(tableFrame, text="Results table")

        logFrame = tk.Frame(self.tabs, bg=CARD)
        self.output = tk.Text(logFrame, bg=CARD, fg=TEXT, insertbackground=TEXT,
                              font=(MONO, 10), relief='flat', wrap='none', padx=10, pady=8)
        logScroll = ttk.Scrollbar(logFrame, command=self.output.yview)
        self.output.configure(yscrollcommand=logScroll.set)
        logScroll.pack(side='right', fill='y')
        self.output.pack(side='left', fill='both', expand=True)
        self.tabs.add(logFrame, text="Text log  (copy for the report)")

    # ------------------------------------------------------------------
    # Reading the controls
    # ------------------------------------------------------------------
    def algorithm(self):
        return dict(ALGORITHMS)[self.algorithmBox.get()]

    def problemKind(self):
        return dict(PROBLEMS)[self.problemBox.get()]

    def readNumber(self, entry, name, convert, minimum):
        """Returns the number typed in 'entry', or None (with a message) if it is not valid."""
        try:
            value = convert(entry.get().strip())
        except ValueError:
            self.showMessage("Please type a number for the %s." % name)
            return None
        if value < minimum:
            self.showMessage("The %s must be at least %s." % (name, minimum))
            return None
        return value

    # ------------------------------------------------------------------
    # Reacting to the dropdowns
    # ------------------------------------------------------------------
    def onMazeChanged(self):
        self.maze = mazeModule.loadMaze(self.mazeBox.get())
        # The key-hunt problem is only offered on mazes that contain pieces.
        if self.maze.keys:
            self.problemBox['values'] = [name for name, kind in PROBLEMS]
            self.problemBox.set(PROBLEMS[1][0])
        else:
            self.problemBox['values'] = [PROBLEMS[0][0]]
            self.problemBox.set(PROBLEMS[0][0])
        self.onProblemChanged()
        self.resetView()

    def onProblemChanged(self):
        choices = HEURISTICS[self.problemKind()]
        self.heuristicBox['values'] = choices
        self.heuristicBox.set(choices[0])
        self.onAlgorithmChanged()

    def onAlgorithmChanged(self):
        informed = self.algorithm() in runner.INFORMED
        self.heuristicBox.configure(state='readonly' if informed else 'disabled')
        self.depthEntry.configure(state='normal' if self.algorithm() == 'dls' else 'disabled')

    def onCanvasResized(self, event):
        # Redraw once the user has stopped dragging the window edge.
        if self.resizeJob is not None:
            self.root.after_cancel(self.resizeJob)
        self.resizeJob = self.root.after(80, self.redraw)

    # ------------------------------------------------------------------
    # Title, cards, table and log
    # ------------------------------------------------------------------
    def showTitle(self):
        maze = self.maze
        text = "%s  (%d x %d)  -  %s" % (maze.name, maze.height, maze.width, maze.title)
        self.titleLabel.configure(text=text, fg=TEXT)

    def showMessage(self, text):
        """A problem with what was typed: shown in place of the title."""
        self.titleLabel.configure(text=text, fg=BAD)

    def setCards(self, result='-', cost='-', steps='-', expanded='-', time='-', color=TEXT):
        self.cards['result'].configure(text=result, fg=color)
        self.cards['cost'].configure(text=cost)
        self.cards['steps'].configure(text=steps)
        self.cards['expanded'].configure(text=expanded)
        self.cards['time'].configure(text=time)

    def summarise(self, result):
        """Short words, colour and table tag for the outcome of one search."""
        status = result['status']
        if status == 'escaped':
            return "Escaped", GOOD, 'escaped'
        if status == 'cutoff':
            return "Cutoff", WARN, 'cutoff'
        if status == 'failure':
            return "No path", BAD, 'bad'
        if status == 'invalid':
            return "Invalid path", BAD, 'bad'
        if 'timed out' in result['error']:
            return "Timed out", BAD, 'bad'
        return "Error", BAD, 'bad'

    def addTableRow(self, algorithmLabel, result):
        words, color, tag = self.summarise(result)
        escaped = result['status'] == 'escaped'
        mazeName = self.maze.name + ("  (keys)" if self.problemKind() == 'keys' else "")
        row = self.table.insert('', 'end', tags=(tag,), values=(
            mazeName, algorithmLabel, words,
            runner._fmt(result['cost']) if escaped else '-',
            result['steps'] if escaped else '-',
            result['expanded'], "%.3f" % result['time']))
        self.table.see(row)

    def write(self, text):
        self.output.insert('end', text)
        self.output.see('end')
        self.root.update_idletasks()

    def clearOutput(self):
        self.output.delete('1.0', 'end')
        self.table.delete(*self.table.get_children())

    def setBusy(self, busy):
        state = 'disabled' if busy else 'normal'
        self.runButton.configure(state=state, text="Searching..." if busy else "Run search")
        self.compareButton.configure(state=state)
        self.root.configure(cursor='watch' if busy else '')
        self.root.update()

    # ------------------------------------------------------------------
    # Running a search
    # ------------------------------------------------------------------
    def run(self):
        if str(self.runButton['state']) == 'disabled':
            return
        algorithm = self.algorithm()
        kind = self.problemKind()
        heuristicName = self.heuristicBox.get()
        timeout = self.readNumber(self.timeoutEntry, "time limit", float, 0.1)
        if timeout is None:
            return
        depth = None
        if algorithm == 'dls':
            depth = self.readNumber(self.depthEntry, "depth limit", int, 0)
            if depth is None:
                return

        self.resetView()
        self.setBusy(True)
        try:
            result = runner.solve(self.maze, kind, algorithm, heuristicName, depth, timeout)
        except Exception as error:      # e.g. RecursionError on a very deep search
            self.setCards(result="Error", color=BAD)
            self.write("ERROR - %s: %s\n\n" % (type(error).__name__, error))
            return
        finally:
            self.setBusy(False)

        # Numbers on the cards
        words, color, tag = self.summarise(result)
        if result['status'] == 'escaped':
            self.setCards(words, runner._fmt(result['cost']), str(result['steps']),
                          str(result['expanded']), "%.3f s" % result['time'], color)
        else:
            self.setCards(words, expanded=str(result['expanded']),
                          time="%.3f s" % result['time'], color=color)

        # The same run in the table and in the text log
        label = runner.ALGORITHM_NAMES[algorithm]
        if algorithm in runner.INFORMED:
            label += " [%s]" % heuristicName
        if algorithm == 'dls':
            label += " [limit %d]" % depth
        self.addTableRow(label, result)
        lines = ["Maze:           %s (%dx%d)" % (self.maze.title, self.maze.height, self.maze.width),
                 "Problem:        %s" % self.problemBox.get()]
        lines += runner.describe(result, algorithm, heuristicName, depth)
        self.write('\n'.join(lines) + '\n\n')

        actions = result['actions'] if result['status'] == 'escaped' else []
        self.showSearch(result['problem'].expandedPositions(), actions)

    def compareAll(self):
        kind = self.problemKind()
        heuristicName = self.heuristicBox.get()
        timeout = self.readNumber(self.timeoutEntry, "time limit", float, 0.1)
        if timeout is None:
            return

        self.resetView()
        self.write("%s  (%dx%d, problem: %s)\n"
                   % (self.maze.title, self.maze.height, self.maze.width, kind))
        header = "%-34s %10s %8s %10s %9s" % ("Algorithm", "Path cost", "Steps", "Expanded", "Time (s)")
        self.write(header + '\n' + '-' * len(header) + '\n')

        self.setBusy(True)
        try:
            for algorithm in ['dfs', 'bfs', 'ids', 'ucs', 'gbfs', 'astar']:
                h = heuristicName if algorithm in runner.INFORMED else None
                label = runner.ALGORITHM_NAMES[algorithm] + (" [%s]" % h if h else "")
                try:
                    r = runner.solve(self.maze, kind, algorithm, h, None, timeout)
                except Exception as error:
                    self.write("%-34s   (%s: %s)\n" % (label, type(error).__name__, error))
                    continue
                self.addTableRow(label, r)
                if r['status'] == 'escaped':
                    self.write("%-34s %10s %8d %10d %9.3f\n"
                               % (label, runner._fmt(r['cost']), r['steps'], r['expanded'], r['time']))
                else:
                    what = r['error'] if r['status'] == 'error' else r['status']
                    self.write("%-34s %10s %8s %10d %9.3f   (%s)\n"
                               % (label, '-', '-', r['expanded'], r['time'], what))
        finally:
            self.setBusy(False)
        self.write('\n')

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------
    def resetView(self):
        """Forget the search on screen and show the bare maze again."""
        self.runId += 1
        self.lastSearch = None
        self.showTitle()
        self.setCards()
        self.drawMaze()

    def redraw(self):
        """The window changed size: draw the maze, and the last search, again."""
        self.resizeJob = None
        self.runId += 1
        self.drawMaze()
        if self.lastSearch is not None:
            expanded, path = self.lastSearch
            self.skip = True
            self.animateExpansion(self.runId, expanded, 0, 1, path)

    def box(self, pos, inset=0):
        """The canvas rectangle (x0, y0, x1, y1) of the cell at 'pos'."""
        row, col = pos
        x = self.left + col * self.size
        y = self.top + row * self.size
        return (x + inset, y + inset, x + self.size - inset, y + self.size - inset)

    def drawMaze(self):
        canvas, maze = self.canvas, self.maze
        canvas.delete('all')
        self.cells = {}
        self.keyItems = {}

        # The biggest square cell that still fits the whole maze on the canvas.
        width = max(canvas.winfo_width(), 200)
        height = max(canvas.winfo_height(), 120)
        self.size = int(max(4, min(44, (width - 16) / maze.width, (height - 16) / maze.height)))
        self.left = (width - maze.width * self.size) // 2
        self.top = (height - maze.height * self.size) // 2

        for row in range(maze.height):
            for col in range(maze.width):
                color = COLORS[maze.grid[row][col]]
                self.cells[(row, col)] = canvas.create_rectangle(
                    *self.box((row, col)), fill=color, outline=color)

        font = (FONT, max(7, int(self.size * 0.55)), 'bold')
        for pos, letter in ((maze.start, 'S'), (maze.exit, 'E')):
            x0, y0, x1, y1 = self.box(pos)
            canvas.create_text((x0 + x1) / 2, (y0 + y1) / 2, text=letter,
                               fill='white', font=font, tags='marker')
        for pos in maze.keys:
            x0, y0, x1, y1 = self.box(pos, max(2, self.size // 5))
            cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
            self.keyItems[pos] = canvas.create_polygon(
                cx, y0, x1, cy, cx, y1, x0, cy, fill=KEY_COLOR, outline='white', tags='marker')
        for pos in maze.openCells():
            if maze.terrain(pos) == mazeModule.GRIEVER and self.size >= 12:
                x0, y0, x1, y1 = self.box(pos, self.size // 3)
                canvas.create_line(x0, y0, x1, y1, fill='#c4505e', width=2, tags='marker')
                canvas.create_line(x0, y1, x1, y0, fill='#c4505e', width=2, tags='marker')

    def showSearch(self, expandedPositions, actions):
        """Shade the expanded cells, then walk the runner along the path."""
        # A cell is coloured by the first time it was expanded.
        expanded = []
        seen = set()
        for pos in expandedPositions:
            if pos not in seen:
                seen.add(pos)
                expanded.append(pos)
        path = pathPositions(self.maze.start, actions)
        self.lastSearch = (expanded, path)

        self.skip = not self.animateVar.get()
        batch = max(1, len(expanded) // 150)
        self.animateExpansion(self.runId, expanded, 0, batch, path)

    def animateExpansion(self, runId, expanded, index, batch, path):
        if runId != self.runId:
            return                       # a newer run has started
        total = len(expanded)
        end = total if self.skip else min(total, index + batch)
        for i in range(index, end):
            pos = expanded[i]
            heat = _blend(HEAT_EARLY, HEAT_LATE, i / max(1, total - 1))
            color = _blend(COLORS[self.maze.terrain(pos)], heat, 0.7)
            self.canvas.itemconfig(self.cells[pos], fill=color, outline=color)
        if end < total:
            self.root.after(16, self.animateExpansion, runId, expanded, end, batch, path)
        else:
            self.drawPath(runId, path)

    def drawPath(self, runId, path):
        if len(path) < 2:
            return                       # no solution, or the start is the goal
        points = []
        for pos in path:
            x0, y0, x1, y1 = self.box(pos)
            points.extend([(x0 + x1) / 2, (y0 + y1) / 2])
        self.canvas.create_line(*points, fill=TRAIL, width=max(2, self.size // 5),
                                capstyle='round', joinstyle='round')
        self.canvas.tag_raise('marker')
        x0, y0, x1, y1 = self.box(path[0], max(1, self.size // 6))
        runnerItem = self.canvas.create_oval(x0, y0, x1, y1, fill=RUNNER,
                                             outline='white', width=2)
        stepMs = max(1, int(min(80, 6000 / (len(path) - 1))))
        delay = 1 if self.skip else 200
        self.root.after(delay, self.animateRunner, runId, path, 0, runnerItem, stepMs)

    def animateRunner(self, runId, path, index, runnerItem, stepMs):
        if runId != self.runId:
            return
        if self.skip:
            index = len(path) - 1
            for pos in path:
                self.pickUp(pos)
        self.pickUp(path[index])
        x0, y0, x1, y1 = self.box(path[index], max(1, self.size // 6))
        self.canvas.coords(runnerItem, x0, y0, x1, y1)
        self.canvas.tag_raise(runnerItem)
        if index < len(path) - 1:
            self.root.after(stepMs, self.animateRunner, runId, path, index + 1, runnerItem, stepMs)

    def pickUp(self, pos):
        """Grey out a code piece once the runner has stepped on it."""
        item = self.keyItems.pop(pos, None)
        if item is not None:
            self.canvas.itemconfig(item, fill='#b9c9dc', outline='#8899aa')

    def skipAnimation(self):
        self.skip = True


def main():
    root = tk.Tk()
    MazeRunnerApp(root)
    root.mainloop()


if __name__ == '__main__':
    main()
