"""
tk_table.py
Tabla scrollable hecha 100% con tk puro (sin ttk).
Evita el bug de ttk.Style que cambia colores entre ejecuciones en Windows.
"""

import tkinter as tk

BG  = "#0f1117"
BG2 = "#151822"
BG3 = "#1e2130"
BG4 = "#232738"
FG  = "#e0e0e0"


class TkTable(tk.Frame):
    def __init__(self, parent, columns, height=400, row_h=24,
                 bg=BG, header_bg=BG2, row_bg1=BG3, row_bg2=BG4,
                 fg=FG, header_fg="#4fc3f7", font=("Courier New", 10),
                 header_font=("Courier New", 10, "bold"), **kwargs):
        super().__init__(parent, bg=bg, **kwargs)

        self._cols     = columns
        self._row_h    = row_h
        self._bg       = bg
        self._row_bg1  = row_bg1
        self._row_bg2  = row_bg2
        self._fg       = fg
        self._font     = font
        self._rows     = []
        self._row_frames = []

        # Cabecera fija
        header = tk.Frame(self, bg=header_bg)
        header.pack(fill="x")
        for name, w, anchor in columns:
            cell = tk.Frame(header, bg=header_bg, width=w, height=28)
            cell.pack_propagate(False)
            cell.pack(side="left")
            tk.Label(cell, text=name, font=header_font,
                     fg=header_fg, bg=header_bg,
                     anchor=anchor, padx=4).pack(fill="both", expand=True)

        tk.Frame(self, bg="#2a2a3a", height=1).pack(fill="x")

        # Canvas scrollable
        container = tk.Frame(self, bg=bg)
        container.pack(fill="both", expand=True)

        self._canvas = tk.Canvas(container, bg=bg,
                                 highlightthickness=0, height=height)
        scrollbar = tk.Scrollbar(container, orient="vertical",
                                 command=self._canvas.yview,
                                 bg=bg, troughcolor=BG2)
        self._canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self._canvas.pack(side="left", fill="both", expand=True)

        self._inner = tk.Frame(self._canvas, bg=bg)
        self._window = self._canvas.create_window(
            (0, 0), window=self._inner, anchor="nw")

        self._inner.bind("<Configure>", self._on_configure)
        self._canvas.bind("<Configure>", self._on_canvas_resize)
        self._canvas.bind("<MouseWheel>", self._on_mousewheel)

    def _on_configure(self, e):
        self._canvas.configure(scrollregion=self._canvas.bbox("all"))

    def _on_canvas_resize(self, e):
        self._canvas.itemconfig(self._window, width=e.width)

    def _on_mousewheel(self, e):
        self._canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")

    def clear(self):
        for f in self._row_frames:
            f.destroy()
        self._row_frames = []
        self._rows = []

    def insert(self, values, bg=None, fg=None):
        idx = len(self._rows)
        row_bg = bg if bg else (self._row_bg1 if idx % 2 == 0 else self._row_bg2)
        row_fg = fg if fg else self._fg

        row_frame = tk.Frame(self._inner, bg=row_bg, height=self._row_h)
        row_frame.pack(fill="x")
        row_frame.pack_propagate(False)

        for val, (_, w, anchor) in zip(values, self._cols):
            cell = tk.Frame(row_frame, bg=row_bg, width=w, height=self._row_h)
            cell.pack_propagate(False)
            cell.pack(side="left")
            tk.Label(cell, text=str(val), font=self._font,
                     fg=row_fg, bg=row_bg,
                     anchor=anchor, padx=4).pack(fill="both", expand=True)

        self._rows.append(values)
        self._row_frames.append(row_frame)

    def scroll_top(self):
        self._canvas.yview_moveto(0)