"""
ui_tab2.py
Pestaña 2: Verificación de grafo bipartito.
"""

import tkinter as tk
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

        tk.Label(parent, text="Verificación de Grafo Bipartito",
                 font=FONT_TITLE, fg=ACCENT, bg=BG).pack(pady=(18, 6))

        # Explicación del concepto
        explain_frame = tk.Frame(parent, bg=BG2, pady=10)
        explain_frame.pack(fill="x", padx=30, pady=(0, 10))

        tk.Label(explain_frame, text="¿Qué es un grafo bipartito?",
                 font=("Courier New", 11, "bold"), fg=ACCENT, bg=BG2).pack(anchor="w", padx=14, pady=(6, 2))

        tk.Label(explain_frame,
                 text=(
                     "Un grafo es bipartito si se puede dividir en dos grupos (A y B)\n"
                     "de forma que NINGUNA arista conecte dos aeropuertos del mismo grupo.\n"
                     "Algoritmo: BFS 2-coloring — si dos vecinos tienen el mismo color, NO es bipartito."
                 ),
                 font=("Courier New", 10), fg="#aaaaaa", bg=BG2, justify="left"
                 ).pack(anchor="w", padx=14, pady=(0, 6))

        tk.Button(
            parent, text="▶  Verificar Bipartitividad",
            font=FONT_MONO, bg=ACCENT, fg="#0f1117",
            activebackground="#e1bee7", relief="flat",
            padx=18, pady=8, cursor="hand2",
            command=self._run,
        ).pack(pady=10)

        self.result_lbl = tk.Label(parent, text="", font=("Courier New", 13, "bold"), bg=BG)
        self.result_lbl.pack()

        self.detail_lbl = tk.Label(parent, text="", font=FONT_MONO, fg="#aaaaaa",
                                   bg=BG, wraplength=900, justify="center")
        self.detail_lbl.pack(pady=8)

        tk.Label(parent, text="─" * 100, fg="#333", bg=BG).pack()

        # Cajas de estadísticas
        stats_frame = tk.Frame(parent, bg=BG)
        stats_frame.pack(pady=16)

        self.box_scope  = self._make_box(stats_frame, "Componente analizada", "—", FG)
        self.box_result = self._make_box(stats_frame, "¿Es bipartito?",        "—", FG)
        self.box_a      = self._make_box(stats_frame, "Grupo A (color 0)",     "—", "#4fc3f7")
        self.box_b      = self._make_box(stats_frame, "Grupo B (color 1)",     "—", "#ef9a9a")

        for box in (self.box_scope, self.box_result, self.box_a, self.box_b):
            box.pack(side="left", padx=14)

        # Explicación del resultado
        self.explain_result = tk.Label(
            parent, text="", font=("Courier New", 10),
            fg="#888", bg=BG, wraplength=900, justify="center"
        )
        self.explain_result.pack(pady=(12, 0))

    def _make_box(self, parent, title, value, color):
        frame = tk.Frame(parent, bg=BG3, padx=20, pady=12)
        tk.Label(frame, text=title, font=("Courier New", 9),
                 fg="#888", bg=BG3).pack()
        lbl = tk.Label(frame, text=value, font=("Courier New", 15, "bold"),
                       fg=color, bg=BG3)
        lbl.pack()
        frame._lbl = lbl
        frame._color = color
        return frame

    def _run(self):
        self.result_lbl.config(text="Calculando…", fg=YELLOW)
        self.detail_lbl.config(text="")
        self.explain_result.config(text="")
        for box in (self.box_scope, self.box_result, self.box_a, self.box_b):
            box._lbl.config(text="…")
        threading.Thread(target=self._compute, daemon=True).start()

    def _compute(self):
        components = self.graph.get_components()
        components.sort(key=lambda c: len(c), reverse=True)
        n_comp = len(components)
        target = components[0]
        is_bip, color = self.graph.is_bipartite_component(target)
        self.parent.after(0, lambda: self._show(is_bip, color, target, n_comp))

    def _show(self, is_bip, color, target, n_comp):
        total = len(self.graph.airports)
        scope = (
            "Grafo completo" if n_comp == 1
            else f"{len(target)} vértices\n(de {total} totales)"
        )
        self.box_scope._lbl.config(text=scope, fg=ACCENT)

        if is_bip:
            grp_a = sum(1 for v in color.values() if v == 0)
            grp_b = sum(1 for v in color.values() if v == 1)
            self.result_lbl.config(text="✔  ES BIPARTITO", fg=GREEN)
            self.detail_lbl.config(
                text="Los aeropuertos se pueden dividir en 2 grupos sin aristas entre nodos del mismo grupo.",
                fg=GREEN)
            self.box_result._lbl.config(text="SÍ ✔", fg=GREEN)
            self.box_a._lbl.config(text=str(grp_a), fg="#4fc3f7")
            self.box_b._lbl.config(text=str(grp_b), fg="#ef9a9a")
            self.explain_result.config(text="", fg="#888")
        else:
            self.result_lbl.config(text="✘  NO ES BIPARTITO", fg=RED)
            self.detail_lbl.config(
                text="Se encontró un ciclo de longitud IMPAR durante el BFS 2-coloring.",
                fg=RED)
            self.box_result._lbl.config(text="NO ✘", fg=RED)
            self.box_a._lbl.config(text="N/A", fg="#555")
            self.box_b._lbl.config(text="N/A", fg="#555")
            self.explain_result.config(
                text=(
                    "¿Por qué NO es bipartito?\n"
                    "En redes aéreas reales los hubs se conectan entre sí directamente.\n"
                    "Ejemplo: ORD ↔ DFW ↔ LAX ↔ ORD forma un triángulo (ciclo de 3 aristas = impar).\n"
                    "Cualquier ciclo de longitud impar hace que el grafo NO sea bipartito."
                ),
                fg="#888"
            )