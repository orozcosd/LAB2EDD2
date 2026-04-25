"""
ui_tab3.py
Pestaña 3: Árbol de Expansión Mínima (Kruskal).
Si hay más de una componente, calcula el MST de cada una.
"""

import tkinter as tk
from tkinter import ttk
import threading

BG = "#0f1117"
BG2 = "#151822"
BG3 = "#1e2130"
FG = "#e0e0e0"
ACCENT = "#ffb74d"
GREEN = "#a5d6a7"
YELLOW = "#ffd54f"
RED = "#ef9a9a"
FONT_MONO = ("Courier New", 11)
FONT_TITLE = ("Courier New", 14, "bold")


class Tab3MST:
    def __init__(self, parent, graph):
        self.parent = parent
        self.graph = graph
        self._build()

    def _build(self):
        parent = self.parent

        tk.Label(
            parent,
            text="Árbol de Expansión Mínima — Kruskal",
            font=FONT_TITLE,
            fg=ACCENT,
            bg=BG,
        ).pack(pady=(18, 4))

        tk.Label(
            parent,
            text="Algoritmo de Kruskal con Union-Find. Los pesos son distancias en km (Haversine).",
            font=("Courier New", 10),
            fg="#888",
            bg=BG,
        ).pack()

        btn = tk.Button(
            parent,
            text="▶  Calcular MST(s)",
            font=FONT_MONO,
            bg=ACCENT,
            fg="#0f1117",
            activebackground="#ffe0b2",
            relief="flat",
            padx=18,
            pady=8,
            cursor="hand2",
            command=self._run,
        )
        btn.pack(pady=16)

        self.progress_lbl = tk.Label(parent, text="", font=FONT_MONO, fg=YELLOW, bg=BG)
        self.progress_lbl.pack()

        # Resumen de componentes
        summary_frame = tk.Frame(parent, bg=BG)
        summary_frame.pack(fill="x", padx=20, pady=4)

        cols_sum = ("Componente", "Vértices", "Aristas MST", "Peso Total (km)")
        self.tree_sum = ttk.Treeview(summary_frame, columns=cols_sum, show="headings", height=8)
        style = ttk.Style()
        style.configure("Treeview", background=BG3, foreground=FG, fieldbackground=BG3, rowheight=24, font=FONT_MONO)
        style.configure("Treeview.Heading", background=BG2, foreground=ACCENT, font=("Courier New", 10, "bold"))

        for col in cols_sum:
            self.tree_sum.heading(col, text=col)
            self.tree_sum.column(col, width=200, anchor="center")

        sc_sum = ttk.Scrollbar(summary_frame, orient="vertical", command=self.tree_sum.yview)
        self.tree_sum.configure(yscrollcommand=sc_sum.set)
        self.tree_sum.pack(side="left", fill="both", expand=True)
        sc_sum.pack(side="right", fill="y")
        self.tree_sum.tag_configure("big", background="#2a1e0a", foreground=ACCENT)
        self.tree_sum.tag_configure("odd", background=BG3)
        self.tree_sum.tag_configure("even", background=BG2)

        # Detalle de aristas de la componente seleccionada
        tk.Label(parent, text="Aristas del MST — haz clic en una componente", font=("Courier New", 10), fg="#888", bg=BG).pack(pady=(8, 2))

        detail_frame = tk.Frame(parent, bg=BG)
        detail_frame.pack(fill="both", expand=True, padx=20, pady=4)

        cols_det = ("Desde", "Hacia", "Distancia (km)")
        self.tree_det = ttk.Treeview(detail_frame, columns=cols_det, show="headings", height=12)
        for col in cols_det:
            self.tree_det.heading(col, text=col)
            self.tree_det.column(col, width=300, anchor="center")

        sc_det = ttk.Scrollbar(detail_frame, orient="vertical", command=self.tree_det.yview)
        self.tree_det.configure(yscrollcommand=sc_det.set)
        self.tree_det.pack(side="left", fill="both", expand=True)
        sc_det.pack(side="right", fill="y")

        self._mst_data = []  # lista de (weight, edges) por componente
        self.tree_sum.bind("<<TreeviewSelect>>", self._on_select)

    def _run(self):
        self.progress_lbl.config(text="Calculando… (puede tardar unos segundos)")
        self.tree_sum.delete(*self.tree_sum.get_children())
        self.tree_det.delete(*self.tree_det.get_children())
        self._mst_data = []
        threading.Thread(target=self._compute, daemon=True).start()

    def _compute(self):
        components = self.graph.get_components()
        components.sort(key=lambda c: len(c), reverse=True)
        results = []
        for comp in components:
            weight, edges = self.graph.kruskal_mst(comp)
            results.append((comp, weight, edges))
        self.parent.after(0, lambda: self._show(results))

    def _show(self, results):
        self.progress_lbl.config(text=f"✔  MST calculado para {len(results)} componente(s).", fg=GREEN)
        self._mst_data = results
        self.tree_sum.delete(*self.tree_sum.get_children())
        for i, (comp, weight, edges) in enumerate(results, 1):
            tag = "big" if i == 1 else ("even" if i % 2 == 0 else "odd")
            self.tree_sum.insert(
                "", "end",
                values=(i, len(comp), len(edges), f"{weight:,.2f}"),
                tags=(tag,),
                iid=str(i - 1),
            )

    def _on_select(self, event):
        sel = self.tree_sum.selection()
        if not sel:
            return
        idx = int(sel[0])
        _, _, edges = self._mst_data[idx]
        self.tree_det.delete(*self.tree_det.get_children())
        for j, (u, v, w) in enumerate(edges):
            tag = "even" if j % 2 == 0 else "odd"
            self.tree_det.insert("", "end", values=(u, v, f"{w:,.2f}"), tags=(tag,))
        self.tree_det.tag_configure("even", background=BG3)
        self.tree_det.tag_configure("odd", background=BG2)
