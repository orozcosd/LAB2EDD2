"""
ui_tab4.py
Pestaña 4: Caminos mínimos — Dijkstra.
"""

import tkinter as tk
from tkinter import ttk
import threading
import math

BG = "#0f1117"
BG2 = "#151822"
BG3 = "#1e2130"
FG = "#e0e0e0"
ACCENT = "#80cbc4"
GREEN = "#a5d6a7"
YELLOW = "#ffd54f"
RED = "#ef9a9a"
FONT_MONO = ("Courier New", 11)
FONT_TITLE = ("Courier New", 14, "bold")


class Tab4CaminosMinimos:
    def __init__(self, parent, graph, src_var, dst_var, go_to_map_cb):
        self.parent = parent
        self.graph = graph
        self.src_var = src_var
        self.dst_var = dst_var
        self.go_to_map = go_to_map_cb
        self._dijkstra_cache = {}
        self._last_path = []
        self._last_dist = 0
        self._build()

    def _build(self):
        parent = self.parent

        tk.Label(parent, text="Caminos Mínimos — Dijkstra",
                 font=FONT_TITLE, fg=ACCENT, bg=BG).pack(pady=(18, 4))
        tk.Label(parent,
                 text="Escribe el código del aeropuerto o selecciónalo en el mapa (pestaña 5).",
                 font=("Courier New", 10), fg="#888", bg=BG).pack()

        # ── Panel de selección ──────────────────────────────────────────
        sel = tk.Frame(parent, bg=BG2, pady=10)
        sel.pack(fill="x", padx=20, pady=10)

        # Fila 0 – Origen
        tk.Label(sel, text="Aeropuerto ORIGEN:", font=FONT_MONO,
                 fg=ACCENT, bg=BG2).grid(row=0, column=0, padx=10, pady=6, sticky="w")

        self.src_entry = tk.Entry(sel, textvariable=self.src_var,
                                  font=FONT_MONO, bg=BG3, fg=FG,
                                  insertbackground=FG, width=10)
        self.src_entry.grid(row=0, column=1, padx=6, pady=6)

        self.src_info_lbl = tk.Label(sel, text="", font=("Courier New", 10),
                                     fg=GREEN, bg=BG2)
        self.src_info_lbl.grid(row=0, column=2, padx=10, sticky="w")

        tk.Button(sel, text="▶  Ejecutar Dijkstra", font=FONT_MONO,
                  bg=ACCENT, fg="#0f1117", activebackground="#b2dfdb",
                  relief="flat", padx=12, pady=6, cursor="hand2",
                  command=self._run_dijkstra).grid(row=0, column=3, padx=18, pady=6)

        # Fila 1 – Destino
        tk.Label(sel, text="Aeropuerto DESTINO:", font=FONT_MONO,
                 fg=YELLOW, bg=BG2).grid(row=1, column=0, padx=10, pady=6, sticky="w")

        self.dst_entry = tk.Entry(sel, textvariable=self.dst_var,
                                  font=FONT_MONO, bg=BG3, fg=FG,
                                  insertbackground=FG, width=10)
        self.dst_entry.grid(row=1, column=1, padx=6, pady=6)

        self.dst_info_lbl = tk.Label(sel, text="", font=("Courier New", 10),
                                     fg=YELLOW, bg=BG2)
        self.dst_info_lbl.grid(row=1, column=2, padx=10, sticky="w")

        tk.Button(sel, text="🗺  Ver ruta en mapa", font=FONT_MONO,
                  bg=YELLOW, fg="#0f1117", activebackground="#fff176",
                  relief="flat", padx=12, pady=6, cursor="hand2",
                  command=self._show_on_map).grid(row=1, column=3, padx=18, pady=6)

        sel.columnconfigure(2, weight=1)

        # Status
        self.status_lbl = tk.Label(parent, text="", font=FONT_MONO, fg=YELLOW, bg=BG)
        self.status_lbl.pack()

        # Info del origen
        origin_frame = tk.Frame(parent, bg=BG2, pady=6)
        origin_frame.pack(fill="x", padx=20, pady=4)
        self.origin_detail = tk.Label(origin_frame, text="", font=FONT_MONO,
                                      fg=FG, bg=BG2, justify="left", anchor="w")
        self.origin_detail.pack(padx=12, fill="x")

        # ── Tabla Top-10 ────────────────────────────────────────────────
        tk.Label(parent, text="Top 10 caminos mínimos MÁS LARGOS desde el origen",
                 font=("Courier New", 10, "bold"), fg=ACCENT, bg=BG).pack(pady=(8, 2))

        table_frame = tk.Frame(parent, bg=BG)
        table_frame.pack(fill="both", expand=True, padx=20, pady=4)

        cols = ("#", "Código", "Nombre", "Ciudad", "País", "Latitud", "Longitud", "Distancia (km)")
        self.tree = ttk.Treeview(table_frame, columns=cols, show="headings", height=14)

        style = ttk.Style()
        style.configure("Treeview", background=BG3, foreground=FG,
                         fieldbackground=BG3, rowheight=24, font=FONT_MONO)
        style.configure("Treeview.Heading", background=BG2, foreground=ACCENT,
                         font=("Courier New", 10, "bold"))
        style.map("Treeview", background=[("selected", "#263238")])

        widths = [40, 70, 250, 130, 130, 80, 90, 130]
        for col, w in zip(cols, widths):
            self.tree.heading(col, text=col)
            anchor = "center" if col in ("#", "Código", "Latitud", "Longitud", "Distancia (km)") else "w"
            self.tree.column(col, width=w, anchor=anchor)

        sc = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sc.set)
        self.tree.pack(side="left", fill="both", expand=True)
        sc.pack(side="right", fill="y")

        for i in range(1, 11):
            self.tree.tag_configure(f"rank{i}",
                                    background="#1a2a2a" if i % 2 == 0 else BG3)

        self.src_var.trace_add("write", self._on_src_change)
        self.dst_var.trace_add("write", self._on_dst_change)

    # ── helpers ─────────────────────────────────────────────────────────
    def _on_src_change(self, *_):
        code = self.src_var.get().strip().upper()
        info = self.graph.airports.get(code)
        if info:
            self.src_info_lbl.config(text=f"✔ {info['name']}, {info['city']}", fg=GREEN)
        else:
            self.src_info_lbl.config(text="")

    def _on_dst_change(self, *_):
        code = self.dst_var.get().strip().upper()
        info = self.graph.airports.get(code)
        if info:
            self.dst_info_lbl.config(text=f"✔ {info['name']}, {info['city']}", fg=YELLOW)
        else:
            self.dst_info_lbl.config(text="")

    # ── Dijkstra ─────────────────────────────────────────────────────────
    def _run_dijkstra(self):
        code = self.src_var.get().strip().upper()
        if not code:
            self.status_lbl.config(text="⚠  Ingresa el código del aeropuerto origen.", fg=RED)
            return
        if code not in self.graph.airports:
            self.status_lbl.config(text=f"⚠  Código '{code}' no encontrado.", fg=RED)
            return
        self.status_lbl.config(text=f"⏳  Ejecutando Dijkstra desde {code}…", fg=YELLOW)
        self.tree.delete(*self.tree.get_children())
        self.origin_detail.config(text="")
        threading.Thread(target=self._compute, args=(code,), daemon=True).start()

    def _compute(self, code):
        dist, prev = self.graph.dijkstra(code)
        self._dijkstra_cache[code] = (dist, prev)
        self.parent.after(0, lambda: self._show(code, dist))

    def _show(self, code, dist):
        info = self.graph.airports[code]
        self.origin_detail.config(
            text=(f"Origen → Código: {info['code']}  |  Nombre: {info['name']}  |  "
                  f"Ciudad: {info['city']}  |  País: {info['country']}  |  "
                  f"Lat: {info['lat']}  |  Lon: {info['lon']}")
        )

        finite = [(d, c) for c, d in dist.items() if d < math.inf and c != code]
        finite.sort(reverse=True)
        top10 = finite[:10]

        self.tree.delete(*self.tree.get_children())
        for i, (d, c) in enumerate(top10, 1):
            ap = self.graph.airports.get(c, {})
            self.tree.insert("", "end",
                             values=(i, c, ap.get("name", ""), ap.get("city", ""),
                                     ap.get("country", ""), ap.get("lat", ""),
                                     ap.get("lon", ""), f"{d:,.2f}"),
                             tags=(f"rank{i}",))

        reachable = sum(1 for d in dist.values() if d < math.inf) - 1
        self.status_lbl.config(
            text=f"✔  Dijkstra completo. {reachable} aeropuertos alcanzables desde {code}.",
            fg=GREEN)

    # ── Ruta al mapa ─────────────────────────────────────────────────────
    def _show_on_map(self):
        src = self.src_var.get().strip().upper()
        dst = self.dst_var.get().strip().upper()
        if not src or not dst:
            self.status_lbl.config(text="⚠  Ingresa origen y destino.", fg=RED)
            return
        if src not in self.graph.airports or dst not in self.graph.airports:
            self.status_lbl.config(text="⚠  Código de aeropuerto no válido.", fg=RED)
            return
        if src not in self._dijkstra_cache:
            self.status_lbl.config(text=f"⏳  Calculando ruta {src}→{dst}…", fg=YELLOW)
            threading.Thread(target=self._compute_and_map, args=(src, dst),
                             daemon=True).start()
        else:
            self._prepare_path(src, dst)
            self.go_to_map()

    def _compute_and_map(self, src, dst):
        dist, prev = self.graph.dijkstra(src)
        self._dijkstra_cache[src] = (dist, prev)
        self.parent.after(0, lambda: (self._prepare_path(src, dst), self.go_to_map()))

    def _prepare_path(self, src, dst):
        dist, prev = self._dijkstra_cache[src]
        path = self.graph.reconstruct_path(prev, src, dst)
        if not path:
            self.status_lbl.config(text=f"✘  No hay camino entre {src} y {dst}.", fg=RED)
            return
        d = dist[dst]
        self.status_lbl.config(
            text=f"✔  Ruta {src}→{dst}: {len(path)-1} salto(s), {d:,.2f} km", fg=GREEN)
        self._last_path = path
        self._last_dist = d

    def get_last_path(self):
        return self._last_path, self._last_dist
