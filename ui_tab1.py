"""
ui_tab1.py
Pestaña 1: Conectividad del grafo.
Determina si el grafo es conexo. Si no lo es, muestra el número de
componentes y la cantidad de vértices de cada una.
"""

import tkinter as tk
from tkinter import ttk
import threading


# Colores del tema
BG = "#0f1117"
BG2 = "#151822"
BG3 = "#1e2130"
FG = "#e0e0e0"
ACCENT = "#4fc3f7"
GREEN = "#a5d6a7"
YELLOW = "#ffd54f"
RED = "#ef9a9a"
FONT_MONO = ("Courier New", 11)
FONT_TITLE = ("Courier New", 14, "bold")


class Tab1Conectividad:
    def __init__(self, parent, graph):
        self.parent = parent
        self.graph = graph
        self._build()

    def _build(self):
        parent = self.parent

        # Título
        tk.Label(
            parent,
            text="Análisis de Conectividad del Grafo",
            font=FONT_TITLE,
            fg=ACCENT,
            bg=BG,
        ).pack(pady=(18, 4))

        tk.Label(
            parent,
            text="Determina si el grafo es conexo usando BFS sobre todos los vértices.",
            font=("Courier New", 10),
            fg="#888",
            bg=BG,
        ).pack()

        # Botón
        btn = tk.Button(
            parent,
            text="▶  Analizar Conectividad",
            font=FONT_MONO,
            bg=ACCENT,
            fg="#0f1117",
            activebackground="#81d4fa",
            relief="flat",
            padx=18,
            pady=8,
            cursor="hand2",
            command=self._run,
        )
        btn.pack(pady=16)

        # Resultado rápido
        self.result_lbl = tk.Label(
            parent,
            text="",
            font=("Courier New", 13, "bold"),
            bg=BG,
        )
        self.result_lbl.pack()

        # Tabla de componentes
        table_frame = tk.Frame(parent, bg=BG)
        table_frame.pack(fill="both", expand=True, padx=20, pady=10)

        cols = ("#", "Vértices", "Aeropuertos (muestra)")
        self.tree = ttk.Treeview(table_frame, columns=cols, show="headings", height=24)
        style = ttk.Style()
        style.configure("Treeview", background=BG3, foreground=FG, fieldbackground=BG3, rowheight=24, font=FONT_MONO)
        style.configure("Treeview.Heading", background=BG2, foreground=ACCENT, font=("Courier New", 10, "bold"))
        style.map("Treeview", background=[("selected", "#263238")])

        for col in cols:
            self.tree.heading(col, text=col)
        self.tree.column("#", width=50, anchor="center")
        self.tree.column("Vértices", width=100, anchor="center")
        self.tree.column("Aeropuertos (muestra)", width=700)

        scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

    def _run(self):
        self.result_lbl.config(text="Calculando…", fg=YELLOW)
        self.tree.delete(*self.tree.get_children())
        threading.Thread(target=self._compute, daemon=True).start()

    def _compute(self):
        components = self.graph.get_components()
        n = len(components)
        connected = n == 1

        # Ordenar componentes de mayor a menor
        components.sort(key=lambda c: len(c), reverse=True)

        self.parent.after(0, lambda: self._show(components, connected))

    def _show(self, components, connected):
        if connected:
            self.result_lbl.config(
                text="✔  El grafo ES CONEXO.",
                fg=GREEN,
            )
        else:
            self.result_lbl.config(
                text=f"✘  El grafo NO ES CONEXO → {len(components)} componentes conexas.",
                fg=RED,
            )

        self.tree.delete(*self.tree.get_children())
        for i, comp in enumerate(components, 1):
            sample = ", ".join(sorted(comp)[:8])
            if len(comp) > 8:
                sample += f"  … ({len(comp) - 8} más)"
            tag = "big" if i == 1 else ("even" if i % 2 == 0 else "odd")
            self.tree.insert("", "end", values=(i, len(comp), sample), tags=(tag,))

        self.tree.tag_configure("big", background="#1a2a1a", foreground=GREEN)
        self.tree.tag_configure("odd", background=BG3)
        self.tree.tag_configure("even", background=BG2)
