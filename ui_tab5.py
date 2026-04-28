"""
ui_tab5.py
Pestaña 5: Mapa interactivo con tkintermapview.
- El mapa arranca limpio (sin marcadores).
- Solo muestra marcadores cuando se dibuja una ruta mínima.
- Verde = origen, Rojo = destino, Amarillo = intermedios.
"""

import tkinter as tk
from tkinter import ttk
import threading
import tkintermapview

BG = "#0f1117"
BG2 = "#151822"
BG3 = "#1e2130"
FG = "#e0e0e0"
ACCENT = "#4fc3f7"
GREEN = "#a5d6a7"
YELLOW = "#ffd54f"
RED = "#ef9a9a"
FONT_MONO = ("Courier New", 10)
FONT_TITLE = ("Courier New", 13, "bold")


class Tab5Mapa:
    def __init__(self, parent, graph, src_var, dst_var):
        self.parent = parent
        self.graph = graph
        self.src_var = src_var
        self.dst_var = dst_var
        self._markers = {}
        self._path_line = None
        self._path_markers = []
        self._map_ready = False
        self._build()

    def _build(self):
        parent = self.parent

        left = tk.Frame(parent, bg=BG2, width=300)
        left.pack(side="left", fill="y")
        left.pack_propagate(False)

        tk.Label(left, text="Mapa Interactivo", font=FONT_TITLE,
                 fg=ACCENT, bg=BG2).pack(pady=(14, 4))

        tk.Label(left, text="Al hacer clic en un marcador:",
                 font=FONT_MONO, fg="#888", bg=BG2).pack(anchor="w", padx=12)

        self.mode_var = tk.StringVar(value="src")
        mode_frame = tk.Frame(left, bg=BG2)
        mode_frame.pack(fill="x", padx=12, pady=4)
        tk.Radiobutton(mode_frame, text="Establecer ORIGEN",
                       variable=self.mode_var, value="src",
                       bg=BG2, fg=GREEN, selectcolor=BG3,
                       activebackground=BG2, font=FONT_MONO).pack(anchor="w")
        tk.Radiobutton(mode_frame, text="Establecer DESTINO",
                       variable=self.mode_var, value="dst",
                       bg=BG2, fg=YELLOW, selectcolor=BG3,
                       activebackground=BG2, font=FONT_MONO).pack(anchor="w")

        src_f = tk.Frame(left, bg=BG3, pady=4)
        src_f.pack(fill="x", padx=12, pady=(8, 2))
        tk.Label(src_f, text="ORIGEN:", font=FONT_MONO, fg=GREEN, bg=BG3).pack(side="left", padx=6)
        tk.Label(src_f, textvariable=self.src_var,
                 font=("Courier New", 11, "bold"), fg=GREEN, bg=BG3).pack(side="left")

        dst_f = tk.Frame(left, bg=BG3, pady=4)
        dst_f.pack(fill="x", padx=12, pady=2)
        tk.Label(dst_f, text="DESTINO:", font=FONT_MONO, fg=YELLOW, bg=BG3).pack(side="left", padx=6)
        tk.Label(dst_f, textvariable=self.dst_var,
                 font=("Courier New", 11, "bold"), fg=YELLOW, bg=BG3).pack(side="left")

        tk.Button(left, text="Dibujar Ruta Mínima", font=FONT_MONO,
                  bg=ACCENT, fg="#0f1117", relief="flat", padx=10, pady=6,
                  cursor="hand2", command=self._draw_route).pack(fill="x", padx=12, pady=(10, 4))

        tk.Button(left, text="Limpiar Ruta", font=FONT_MONO,
                  bg=BG3, fg=RED, relief="flat", padx=10, pady=4,
                  cursor="hand2", command=self._clear_route).pack(fill="x", padx=12)

        self.route_status = tk.Label(left, text="", font=FONT_MONO, fg=FG,
                                     bg=BG2, wraplength=270, justify="left")
        self.route_status.pack(pady=8, padx=12, anchor="w")

        tk.Label(left, text="─" * 34, fg="#333", bg=BG2).pack()
        tk.Label(left, text="Aeropuerto seleccionado:", font=FONT_MONO,
                 fg="#888", bg=BG2).pack(anchor="w", padx=12, pady=(6, 2))
        self.info_lbl = tk.Label(left, text="—", font=FONT_MONO, fg=FG,
                                 bg=BG2, wraplength=280, justify="left")
        self.info_lbl.pack(anchor="w", padx=12)

        tk.Label(left, text="─" * 34, fg="#333", bg=BG2).pack(pady=(10, 0))
        tk.Label(left, text="Vértices del camino mínimo:", font=FONT_MONO,
                 fg="#888", bg=BG2).pack(anchor="w", padx=12, pady=(4, 2))

        path_frame = tk.Frame(left, bg=BG2)
        path_frame.pack(fill="both", expand=True, padx=6, pady=4)

        self.path_tree = ttk.Treeview(path_frame,
                                      columns=("Paso", "Código", "Ciudad"),
                                      show="headings", height=14)
        style = ttk.Style()
        style.configure("Treeview", background=BG3, foreground=FG,
                         fieldbackground=BG3, rowheight=22, font=FONT_MONO)
        style.configure("Treeview.Heading", background=BG2, foreground=ACCENT,
                         font=("Courier New", 9, "bold"))

        self.path_tree.heading("Paso", text="#")
        self.path_tree.heading("Código", text="Código")
        self.path_tree.heading("Ciudad", text="Ciudad")
        self.path_tree.column("Paso", width=30, anchor="center")
        self.path_tree.column("Código", width=65, anchor="center")
        self.path_tree.column("Ciudad", width=160)

        sc = ttk.Scrollbar(path_frame, orient="vertical", command=self.path_tree.yview)
        self.path_tree.configure(yscrollcommand=sc.set)
        self.path_tree.pack(side="left", fill="both", expand=True)
        sc.pack(side="right", fill="y")

        right = tk.Frame(parent, bg="#111")
        right.pack(side="right", fill="both", expand=True)

        self.loading_lbl = tk.Label(right,
                                    text="Cargando mapa… (requiere conexión a internet)",
                                    font=("Courier New", 12), fg=ACCENT, bg="#111")
        self.loading_lbl.place(relx=0.5, rely=0.5, anchor="center")

        right.after(800, lambda: self._init_map(right))

    def _init_map(self, container):
        try:
            self.map_widget = tkintermapview.TkinterMapView(container, corner_radius=0)
            self.map_widget.pack(fill="both", expand=True)
            self.map_widget.set_position(20, 0)
            self.map_widget.set_zoom(2)
            self.map_widget.add_left_click_map_command(self._on_map_click)
            self._map_ready = True
            self.loading_lbl.destroy()
        except Exception as e:
            self.loading_lbl.config(text=f"Error al cargar el mapa:\n{e}", fg=RED)

    def _on_map_click(self, coords):
        pass

    def _on_marker_click(self, code):
        ap = self.graph.airports.get(code, {})
        self.info_lbl.config(
            text=(f"Código: {ap.get('code')}\n"
                  f"Nombre: {ap.get('name')}\n"
                  f"Ciudad: {ap.get('city')}\n"
                  f"País: {ap.get('country')}\n"
                  f"Lat: {ap.get('lat')}  Lon: {ap.get('lon')}")
        )
        if self.mode_var.get() == "src":
            self.src_var.set(code)
        else:
            self.dst_var.set(code)

    def _draw_route(self):
        src = self.src_var.get().strip().upper()
        dst = self.dst_var.get().strip().upper()
        if not src or not dst:
            self.route_status.config(text="Selecciona origen y destino.", fg=RED)
            return
        if src not in self.graph.airports or dst not in self.graph.airports:
            self.route_status.config(text="Código no válido.", fg=RED)
            return
        self.route_status.config(text="Calculando camino mínimo…", fg=YELLOW)
        threading.Thread(target=self._compute_route, args=(src, dst), daemon=True).start()

    def _compute_route(self, src, dst):
        dist, prev = self.graph.dijkstra(src)
        path = self.graph.reconstruct_path(prev, src, dst)
        d = dist.get(dst, float("inf"))
        self.parent.after(0, lambda: self._render_path(path, d, src, dst))

    def _render_path(self, path, dist_km, src, dst):
        self._clear_route()
        import math
        if not path or dist_km == math.inf:
            self.route_status.config(text=f"No hay camino entre {src} y {dst}.", fg=RED)
            return

        coords = [(self.graph.airports[c]["lat"], self.graph.airports[c]["lon"]) for c in path]

        # Centrar el mapa en el punto medio del camino
        mid = coords[len(coords) // 2]
        self.map_widget.set_position(*mid)
        zoom = 5 if len(path) <= 3 else (4 if len(path) <= 8 else 3)
        self.map_widget.set_zoom(zoom)

        # Dibujar polilínea
        self._path_line = self.map_widget.set_path(coords, color="#ffd54f", width=3)

        # Solo marcadores de los aeropuertos del camino (mapa limpio)
        for i, code in enumerate(path):
            ap = self.graph.airports[code]
            color = "#a5d6a7" if i == 0 else ("#ef9a9a" if i == len(path) - 1 else "#ffd54f")
            label = f"{code}  {ap.get('city', '')}"
            m = self.map_widget.set_marker(
                ap["lat"], ap["lon"], text=label,
                marker_color_circle=color,
                marker_color_outside="#222",
                command=lambda mk, c=code: self._on_marker_click(c),
            )
            self._path_markers.append(m)

        # Tabla de vértices
        self.path_tree.delete(*self.path_tree.get_children())
        for i, code in enumerate(path):
            ap = self.graph.airports.get(code, {})
            tag = "src" if i == 0 else ("dst" if i == len(path) - 1 else "mid")
            self.path_tree.insert("", "end",
                                  values=(i + 1, code, ap.get("city", "")),
                                  tags=(tag,))

        self.path_tree.tag_configure("src", background="#1a3a1a", foreground=GREEN)
        self.path_tree.tag_configure("dst", background="#3a1a1a", foreground=RED)
        self.path_tree.tag_configure("mid", background=BG3, foreground=YELLOW)

        self.route_status.config(
            text=f"✔ {src} → {dst}\n{len(path)-1} salto(s) | {dist_km:,.2f} km",
            fg=GREEN)

    def _clear_route(self):
        if self._path_line:
            try:
                self._path_line.delete()
            except Exception:
                pass
            self._path_line = None
        for m in self._path_markers:
            try:
                m.delete()
            except Exception:
                pass
        self._path_markers = []
        self.path_tree.delete(*self.path_tree.get_children())
        self.route_status.config(text="")

    def draw_external_path(self, path, dist_km):
        if path and self._map_ready:
            self._render_path(path, dist_km, path[0], path[-1])