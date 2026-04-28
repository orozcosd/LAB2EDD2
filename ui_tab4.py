"""
ui_tab4.py
Pestaña 4: Caminos mínimos — Dijkstra.
"""

import tkinter as tk
from tkinter import ttk
import threading
# Módulo matemático estándar; aquí se usa math.inf para representar "distancia infinita"
# (aeropuertos inalcanzables desde el origen)
import math

BG = "#0f1117"
BG2 = "#151822"
BG3 = "#1e2130"
FG = "#e0e0e0"
ACCENT = "#80cbc4"   # Color de acento (verde azulado) — distinto al de Tab3
GREEN = "#a5d6a7"
YELLOW = "#ffd54f"
RED = "#ef9a9a"
FONT_MONO = ("Courier New", 11)
FONT_TITLE = ("Courier New", 14, "bold")


class Tab4CaminosMinimos:
    """
    Clase que representa la pestaña 4 de la aplicación.
    Permite al usuario ingresar un aeropuerto ORIGEN y uno DESTINO,
    ejecutar el algoritmo de Dijkstra para encontrar el camino más corto,
    y visualizar los 10 destinos más lejanos alcanzables desde el origen.
    También puede enviar la ruta calculada al mapa interactivo (pestaña 5).
    """

    def __init__(self, parent, graph, src_var, dst_var, go_to_map_cb):
        """
        Constructor: inicializa la pestaña con todos los datos que necesita.

        parent       → el contenedor visual (frame) donde se dibuja todo
        graph        → el grafo con aeropuertos y rutas
        src_var      → variable compartida con el código del aeropuerto ORIGEN
                       (compartida con el mapa para sincronización)
        dst_var      → variable compartida con el código del aeropuerto DESTINO
        go_to_map_cb → función callback: al llamarla, cambia a la pestaña del mapa
        """
        self.parent = parent
        self.graph = graph
        self.src_var = src_var
        self.dst_var = dst_var
        self.go_to_map = go_to_map_cb

        # Caché de resultados Dijkstra: evita recalcular si ya se corrió desde el mismo origen
        # Formato: { "BOG": (dist_dict, prev_dict), "JFK": (...), ... }
        self._dijkstra_cache = {}

        # Última ruta calculada (lista de códigos de aeropuertos) y su distancia total
        self._last_path = []
        self._last_dist = 0

        self._build()

    def _build(self):
        """
        Construye toda la interfaz gráfica de esta pestaña:
        - Título y subtítulo
        - Panel con campos de texto para ORIGEN y DESTINO
        - Botones "Ejecutar Dijkstra" y "Ver ruta en mapa"
        - Etiqueta de estado (mensajes de progreso/error)
        - Información detallada del aeropuerto origen
        - Tabla con el Top 10 de destinos más lejanos
        """
        parent = self.parent

        # ── Título principal ───────────────────────────────────────────────────
        tk.Label(parent, text="Caminos Mínimos — Dijkstra",
                 font=FONT_TITLE, fg=ACCENT, bg=BG).pack(pady=(18, 4))

        # ── Subtítulo con instrucciones ────────────────────────────────────────
        tk.Label(parent,
                 text="Escribe el código del aeropuerto o selecciónalo en el mapa (pestaña 5).",
                 font=("Courier New", 10), fg="#888", bg=BG).pack()

        # ── Panel de selección de aeropuertos (origen y destino) ──────────────
        sel = tk.Frame(parent, bg=BG2, pady=10)
        sel.pack(fill="x", padx=20, pady=10)

        # Fila 0: campo de texto para el ORIGEN + botón Dijkstra
        tk.Label(sel, text="Aeropuerto ORIGEN:", font=FONT_MONO,
                 fg=ACCENT, bg=BG2).grid(row=0, column=0, padx=10, pady=6, sticky="w")

        # Campo de texto enlazado a src_var: si cambia aquí, cambia en el mapa también
        self.src_entry = tk.Entry(sel, textvariable=self.src_var,
                                  font=FONT_MONO, bg=BG3, fg=FG,
                                  insertbackground=FG, width=10)
        self.src_entry.grid(row=0, column=1, padx=6, pady=6)

        # Etiqueta que muestra el nombre del aeropuerto origen al reconocer su código
        self.src_info_lbl = tk.Label(sel, text="", font=("Courier New", 10),
                                     fg=GREEN, bg=BG2)
        self.src_info_lbl.grid(row=0, column=2, padx=10, sticky="w")

        # Botón que dispara el algoritmo Dijkstra desde el aeropuerto origen
        tk.Button(sel, text="Ejecutar Dijkstra", font=FONT_MONO,
                  bg=ACCENT, fg="#0f1117", activebackground="#b2dfdb",
                  relief="flat", padx=12, pady=6, cursor="hand2",
                  command=self._run_dijkstra).grid(row=0, column=3, padx=18, pady=6)

        # Fila 1: campo de texto para el DESTINO + botón Ver en mapa
        tk.Label(sel, text="Aeropuerto DESTINO:", font=FONT_MONO,
                 fg=YELLOW, bg=BG2).grid(row=1, column=0, padx=10, pady=6, sticky="w")

        # Campo de texto enlazado a dst_var
        self.dst_entry = tk.Entry(sel, textvariable=self.dst_var,
                                  font=FONT_MONO, bg=BG3, fg=FG,
                                  insertbackground=FG, width=10)
        self.dst_entry.grid(row=1, column=1, padx=6, pady=6)

        # Etiqueta que muestra el nombre del aeropuerto destino al reconocer su código
        self.dst_info_lbl = tk.Label(sel, text="", font=("Courier New", 10),
                                     fg=YELLOW, bg=BG2)
        self.dst_info_lbl.grid(row=1, column=2, padx=10, sticky="w")

        # Botón que calcula la ruta y cambia a la pestaña del mapa para visualizarla
        tk.Button(sel, text="🗺  Ver ruta en mapa", font=FONT_MONO,
                  bg=YELLOW, fg="#0f1117", activebackground="#fff176",
                  relief="flat", padx=12, pady=6, cursor="hand2",
                  command=self._show_on_map).grid(row=1, column=3, padx=18, pady=6)

        # La columna 2 (donde están los nombres) se expande si hay espacio disponible
        sel.columnconfigure(2, weight=1)

        # ── Etiqueta de estado: muestra mensajes de progreso, éxito o error ───
        self.status_lbl = tk.Label(parent, text="", font=FONT_MONO, fg=YELLOW, bg=BG)
        self.status_lbl.pack()

        # ── Banda informativa con los datos completos del aeropuerto origen ───
        origin_frame = tk.Frame(parent, bg=BG2, pady=6)
        origin_frame.pack(fill="x", padx=20, pady=4)
        self.origin_detail = tk.Label(origin_frame, text="", font=FONT_MONO,
                                      fg=FG, bg=BG2, justify="left", anchor="w")
        self.origin_detail.pack(padx=12, fill="x")

        # ── Tabla Top-10: los 10 destinos alcanzables con mayor distancia ─────
        tk.Label(parent, text="Top 10 caminos mínimos MÁS LARGOS desde el origen",
                 font=("Courier New", 10, "bold"), fg=ACCENT, bg=BG).pack(pady=(8, 2))

        table_frame = tk.Frame(parent, bg=BG)
        table_frame.pack(fill="both", expand=True, padx=20, pady=4)

        cols = ("#", "Código", "Nombre", "Ciudad", "País", "Latitud", "Longitud", "Distancia (km)")
        self.tree = ttk.Treeview(table_frame, columns=cols, show="headings", height=14)

        # Estilo oscuro para la tabla
        style = ttk.Style()
        style.configure("Treeview", background=BG3, foreground=FG,
                         fieldbackground=BG3, rowheight=24, font=FONT_MONO)
        style.configure("Treeview.Heading", background=BG2, foreground=ACCENT,
                         font=("Courier New", 10, "bold"))
        style.map("Treeview", background=[("selected", "#263238")])

        # Anchos de cada columna en píxeles, en el mismo orden que 'cols'
        widths = [40, 70, 250, 130, 130, 80, 90, 130]
        for col, w in zip(cols, widths):
            self.tree.heading(col, text=col)
            # Columnas numéricas centradas; columnas de texto alineadas a la izquierda
            anchor = "center" if col in ("#", "Código", "Latitud", "Longitud", "Distancia (km)") else "w"
            self.tree.column(col, width=w, anchor=anchor)

        # Barra de scroll vertical para la tabla
        sc = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sc.set)
        self.tree.pack(side="left", fill="both", expand=True)
        sc.pack(side="right", fill="y")

        # Colores alternos para las 10 filas del ranking
        for i in range(1, 11):
            self.tree.tag_configure(f"rank{i}",
                                    background="#1a2a2a" if i % 2 == 0 else BG3)

        # Cada vez que el usuario escribe en los campos, se actualiza la etiqueta de nombre
        self.src_var.trace_add("write", self._on_src_change)
        self.dst_var.trace_add("write", self._on_dst_change)

    # ── Helpers de autocompletado ──────────────────────────────────────────────

    def _on_src_change(self, *_):
        """
        Se dispara automáticamente cada vez que el usuario escribe en el campo ORIGEN.
        Si el código ingresado existe en el grafo, muestra el nombre y ciudad del aeropuerto.
        Si no existe aún, limpia la etiqueta informativa.
        """
        code = self.src_var.get().strip().upper()
        info = self.graph.airports.get(code)
        if info:
            self.src_info_lbl.config(text=f"{info['name']}, {info['city']}", fg=GREEN)
        else:
            self.src_info_lbl.config(text="")

    def _on_dst_change(self, *_):
        """
        Igual que _on_src_change pero para el campo DESTINO.
        Muestra el nombre del aeropuerto destino en amarillo mientras el usuario escribe.
        """
        code = self.dst_var.get().strip().upper()
        info = self.graph.airports.get(code)
        if info:
            self.dst_info_lbl.config(text=f"{info['name']}, {info['city']}", fg=YELLOW)
        else:
            self.dst_info_lbl.config(text="")

    # ── Dijkstra ───────────────────────────────────────────────────────────────

    def _run_dijkstra(self):
        """
        Se ejecuta al presionar el botón "Ejecutar Dijkstra".
        Valida que el código ingresado sea correcto y luego lanza el cálculo
        en un hilo separado para no congelar la interfaz.
        """
        code = self.src_var.get().strip().upper()

        # Validaciones antes de calcular
        if not code:
            self.status_lbl.config(text="Ingresa el código del aeropuerto origen.", fg=RED)
            return
        if code not in self.graph.airports:
            self.status_lbl.config(text=f"Código '{code}' no encontrado.", fg=RED)
            return

        self.status_lbl.config(text=f"Ejecutando Dijkstra desde {code}…", fg=YELLOW)
        self.tree.delete(*self.tree.get_children())  # Limpia la tabla anterior
        self.origin_detail.config(text="")           # Limpia la info del origen anterior

        # Lanza el cálculo pesado en segundo plano
        threading.Thread(target=self._compute, args=(code,), daemon=True).start()

    def _compute(self, code):
        """
        Ejecuta el algoritmo de Dijkstra en segundo plano (hilo separado).
        Guarda el resultado en caché para no repetir el cálculo si se vuelve
        a pedir la misma ruta desde el mismo origen.

        Retorna dos diccionarios:
          dist → { código_aeropuerto: distancia_mínima_en_km }
          prev → { código_aeropuerto: aeropuerto_anterior_en_la_ruta }
        """
        dist, prev = self.graph.dijkstra(code)
        self._dijkstra_cache[code] = (dist, prev)  # Guarda en caché
        # Solicita a tkinter que muestre los resultados de forma segura desde el hilo principal
        self.parent.after(0, lambda: self._show(code, dist))

    def _show(self, code, dist):
        """
        Muestra los resultados de Dijkstra en la interfaz (se ejecuta en el hilo principal).
        1. Muestra los datos completos del aeropuerto origen.
        2. Filtra los destinos alcanzables (distancia < infinito).
        3. Los ordena de mayor a menor distancia y toma los primeros 10.
        4. Llena la tabla con esos 10 destinos.
        5. Actualiza el mensaje de estado con cuántos aeropuertos son alcanzables.
        """
        # Muestra información detallada del aeropuerto origen
        info = self.graph.airports[code]
        self.origin_detail.config(
            text=(f"Origen → Código: {info['code']}  |  Nombre: {info['name']}  |  "
                  f"Ciudad: {info['city']}  |  País: {info['country']}  |  "
                  f"Lat: {info['lat']}  |  Lon: {info['lon']}")
        )

        # Filtra aeropuertos alcanzables (descarta los de distancia infinita y el propio origen)
        finite = [(d, c) for c, d in dist.items() if d < math.inf and c != code]
        finite.sort(reverse=True)  # Ordena de mayor a menor distancia
        top10 = finite[:10]        # Toma solo los 10 más lejanos

        # Llena la tabla con los 10 destinos más lejanos
        self.tree.delete(*self.tree.get_children())
        for i, (d, c) in enumerate(top10, 1):
            ap = self.graph.airports.get(c, {})
            self.tree.insert("", "end",
                             values=(i, c, ap.get("name", ""), ap.get("city", ""),
                                     ap.get("country", ""), ap.get("lat", ""),
                                     ap.get("lon", ""), f"{d:,.2f}"),
                             tags=(f"rank{i}",))

        # Cuenta cuántos aeropuertos son alcanzables (excluyendo el origen)
        reachable = sum(1 for d in dist.values() if d < math.inf) - 1
        self.status_lbl.config(
            text=f"Dijkstra completo. {reachable} aeropuertos alcanzables desde {code}.",
            fg=GREEN)

    # ── Visualización en mapa ──────────────────────────────────────────────────

    def _show_on_map(self):
        """
        Se ejecuta al presionar "Ver ruta en mapa".
        Valida los códigos de origen y destino, luego:
        - Si ya existe el resultado de Dijkstra en caché → reconstruye la ruta directamente.
        - Si no → lanza Dijkstra en segundo plano y después muestra el mapa.
        """
        src = self.src_var.get().strip().upper()
        dst = self.dst_var.get().strip().upper()

        # Validaciones básicas
        if not src or not dst:
            self.status_lbl.config(text="Ingresa origen y destino.", fg=RED)
            return
        if src not in self.graph.airports or dst not in self.graph.airports:
            self.status_lbl.config(text="Código de aeropuerto no válido.", fg=RED)
            return

        if src not in self._dijkstra_cache:
            # Dijkstra no se ha corrido desde este origen → calcularlo primero
            self.status_lbl.config(text=f"Calculando ruta {src}→{dst}…", fg=YELLOW)
            threading.Thread(target=self._compute_and_map, args=(src, dst),
                             daemon=True).start()
        else:
            # Ya existe el resultado en caché → usar directamente
            self._prepare_path(src, dst)
            self.go_to_map()

    def _compute_and_map(self, src, dst):
        """
        Versión combinada: ejecuta Dijkstra en segundo plano y al terminar
        reconstruye la ruta y cambia al mapa. Se usa cuando el resultado
        no está en caché y el usuario presionó "Ver ruta en mapa".
        """
        dist, prev = self.graph.dijkstra(src)
        self._dijkstra_cache[src] = (dist, prev)
        # Llama a _prepare_path y go_to_map de forma segura desde el hilo principal
        self.parent.after(0, lambda: (self._prepare_path(src, dst), self.go_to_map()))

    def _prepare_path(self, src, dst):
        """
        Reconstruye el camino más corto entre src y dst usando el diccionario
        'prev' que genera Dijkstra (cada nodo apunta a su predecesor en la ruta).
        Si existe la ruta, guarda la lista de aeropuertos y la distancia total
        en self._last_path y self._last_dist para que el mapa pueda leerlos.
        Si no hay camino posible, muestra un mensaje de error.
        """
        dist, prev = self._dijkstra_cache[src]
        path = self.graph.reconstruct_path(prev, src, dst)

        if not path:
            self.status_lbl.config(text=f"No hay camino entre {src} y {dst}.", fg=RED)
            return

        d = dist[dst]
        self.status_lbl.config(
            text=f"Ruta {src}→{dst}: {len(path)-1} salto(s), {d:,.2f} km", fg=GREEN)

        # Guarda la ruta para que la pestaña del mapa pueda acceder a ella
        self._last_path = path
        self._last_dist = d

    def get_last_path(self):
        """
        Método público que devuelve la última ruta calculada.
        Es llamado por la pestaña del mapa (Tab5) para saber qué ruta dibujar.

        Retorna:
          _last_path → lista ordenada de códigos de aeropuertos (ej: ["BOG","MIA","JFK"])
          _last_dist → distancia total de la ruta en km
        """
        return self._last_path, self._last_dist