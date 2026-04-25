"""
ui_tab2.py
Pestaña 2: Verificación de grafo bipartito.
Si hay más de una componente, verifica si la componente MÁS GRANDE es bipartita.
"""

import tkinter as tk
from tkinter import ttk
import threading

BG = "#0f1117"
BG2 = "#151822"
BG3 = "#1e2130"
FG = "#e0e0e0"
ACCENT = "#ce93d8"
GREEN = "#a5d6a7"
YELLOW = "#ffd54f"
RED = "#ef9a9a"
FONT_MONO = ("Courier New", 11)
FONT_TITLE = ("Courier New", 14, "bold")


class Tab2Bipartito:
    def __init__(self, parent, graph):
        self.parent = parent
        self.graph = graph
        self._build()

    def _build(self):
        parent = self.parent

        tk.Label(
            parent,
            text="Verificación de Grafo Bipartito",
            font=FONT_TITLE,
            fg=ACCENT,
            bg=BG,
        ).pack(pady=(18, 4))

        tk.Label(
            parent,
            text="Usa BFS 2-coloring. Si el grafo no es conexo, analiza la componente más grande.",
            font=("Courier New", 10),
            fg="#888",
            bg=BG,
        ).pack()

        btn = tk.Button(
            parent,
            text="▶  Verificar Bipartitividad",
            font=FONT_MONO,
            bg=ACCENT,
            fg="#0f1117",
            activebackground="#e1bee7",
            relief="flat",
            padx=18,
            pady=8,
            cursor="hand2",
            command=self._run,
        )
        btn.pack(pady=16)

        self.result_lbl = tk.Label(parent, text="", font=("Courier New", 13, "bold"), bg=BG)
        self.result_lbl.pack()

        self.detail_lbl = tk.Label(parent, text="", font=FONT_MONO, fg=FG, bg=BG, wraplength=900, justify="left")
        self.detail_lbl.pack(pady=8)

        # Leyenda de colores si es bipartito
        legend_frame = tk.Frame(parent, bg=BG)
        legend_frame.pack(pady=6)
        tk.Label(legend_frame, text="  Grupo A ", bg="#1a3a4a", fg="#4fc3f7", font=FONT_MONO).pack(side="left", padx=4)
        tk.Label(legend_frame, text="  Grupo B ", bg="#3a1a1a", fg="#ef9a9a", font=FONT_MONO).pack(side="left", padx=4)

        # Tabla muestra de nodos coloreados
        table_frame = tk.Frame(parent, bg=BG)
        table_frame.pack(fill="both", expand=True, padx=20, pady=6)

        cols = ("Código", "Nombre", "Ciudad", "País", "Grupo")
        self.tree = ttk.Treeview(table_frame, columns=cols, show="headings", height=20)
        style = ttk.Style()
        style.configure("Treeview", background=BG3, foreground=FG, fieldbackground=BG3, rowheight=24, font=FONT_MONO)
        style.configure("Treeview.Heading", background=BG2, foreground=ACCENT, font=("Courier New", 10, "bold"))
        style.map("Treeview", background=[("selected", "#263238")])

        widths = [80, 280, 150, 150, 80]
        for col, w in zip(cols, widths):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=w, anchor="center" if col in ("Código", "Grupo") else "w")

        scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        self.tree.tag_configure("A", background="#1a3a4a", foreground="#4fc3f7")
        self.tree.tag_configure("B", background="#3a1a1a", foreground="#ef9a9a")

    def _run(self):
        self.result_lbl.config(text="Calculando…", fg=YELLOW)
        self.detail_lbl.config(text="")
        self.tree.delete(*self.tree.get_children())
        threading.Thread(target=self._compute, daemon=True).start()

    def _compute(self):
        components = self.graph.get_components()
        components.sort(key=lambda c: len(c), reverse=True)
        n_comp = len(components)
        target = components[0]  # componente más grande (o única)

        is_bip, color = self.graph.is_bipartite_component(target)
        self.parent.after(0, lambda: self._show(is_bip, color, target, n_comp))

    def _show(self, is_bip, color, target, n_comp):
        scope = "el grafo completo" if n_comp == 1 else f"la componente más grande ({len(target)} vértices)"

        if is_bip:
            self.result_lbl.config(text=f"✔  {scope.capitalize()} ES BIPARTITO.", fg="#a5d6a7")
            grp_a = sum(1 for v in color.values() if v == 0)
            grp_b = sum(1 for v in color.values() if v == 1)
            self.detail_lbl.config(
                text=f"Grupo A: {grp_a} aeropuertos   |   Grupo B: {grp_b} aeropuertos",
                fg="#a5d6a7",
            )
        else:
            self.result_lbl.config(text=f"✘  {scope.capitalize()} NO ES BIPARTITO.", fg=RED)
            self.detail_lbl.config(
                text="Se encontró un ciclo de longitud impar durante el BFS 2-coloring.",
                fg=RED,
            )

        self.tree.delete(*self.tree.get_children())
        # Mostrar hasta 200 nodos coloreados
        for code, grp in list(color.items())[:200]:
            info = self.graph.airports.get(code, {})
            label = "A" if grp == 0 else "B"
            self.tree.insert(
                "", "end",
                values=(code, info.get("name", ""), info.get("city", ""), info.get("country", ""), label),
                tags=(label,),
            )
