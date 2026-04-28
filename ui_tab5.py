"""
ui_tab5.py
Pestaña 5: Mapa interactivo con tkintermapview.
Docuemntado por Juan Salcedo
- El mapa arranca limpio (sin marcadores).
- Solo muestra marcadores cuando se dibuja una ruta mínima.
- Verde = origen, Rojo = destino, Amarillo = intermedios.
"""

import tkinter as tk
from tkinter import ttk
import threading
# Librería externa que permite incrustar un mapa interactivo (tipo Google Maps)
# directamente dentro de una ventana de tkinter. Requiere conexión a internet.
import tkintermapview

BG = "#0f1117"
BG2 = "#151822"
BG3 = "#1e2130"
FG = "#e0e0e0"
ACCENT = "#4fc3f7"   # Color de acento (azul claro) — distinto a las otras pestañas
GREEN = "#a5d6a7"
YELLOW = "#ffd54f"
RED = "#ef9a9a"
FONT_MONO = ("Courier New", 10)
FONT_TITLE = ("Courier New", 13, "bold")


class Tab5Mapa:
    """
    Clase que representa la pestaña 5 de la aplicación.
    Muestra un mapa interactivo del mundo donde el usuario puede:
    - Hacer clic en marcadores para seleccionar aeropuertos como origen/destino.
    - Dibujar la ruta más corta entre dos aeropuertos como una línea sobre el mapa.
    - Ver la lista de aeropuertos intermedios del camino en una tabla lateral.
    """

    def __init__(self, parent, graph, src_var, dst_var):
        """
        Constructor: guarda las referencias necesarias e inicializa el estado interno.

        parent  → el contenedor visual donde se dibuja la pestaña
        graph   → el grafo con aeropuertos y rutas
        src_var → variable compartida con el código del aeropuerto ORIGEN
        dst_var → variable compartida con el código del aeropuerto DESTINO
        """
        self.parent = parent
        self.graph = graph
        self.src_var = src_var
        self.dst_var = dst_var

        # Diccionario de marcadores activos en el mapa: { código: objeto_marcador }
        self._markers = {}

        # Objeto que representa la línea dibujada sobre el mapa (la ruta)
        self._path_line = None

        # Lista de marcadores colocados sobre los aeropuertos de la ruta actual
        self._path_markers = []

        # Bandera: indica si el widget del mapa ya terminó de cargar
        self._map_ready = False

        self._build()

    def _build(self):
        """
        Construye la interfaz gráfica de la pestaña, dividida en dos zonas:
        - Panel izquierdo (left): controles, información del aeropuerto seleccionado
          y tabla con los pasos de la ruta.
        - Panel derecho (right): el mapa interactivo propiamente dicho.
        """
        parent = self.parent

        # ── Panel izquierdo: controles y datos ────────────────────────────────
        left = tk.Frame(parent, bg=BG2, width=300)
        left.pack(side="left", fill="y")
        left.pack_propagate(False)  # Evita que el frame se encoja según su contenido

        tk.Label(left, text="Mapa Interactivo", font=FONT_TITLE,
                 fg=ACCENT, bg=BG2).pack(pady=(14, 4))

        tk.Label(left, text="Al hacer clic en un marcador:",
                 font=FONT_MONO, fg="#888", bg=BG2).pack(anchor="w", padx=12)

        # ── Selector de modo: el clic en un marcador asigna ORIGEN o DESTINO ──
        self.mode_var = tk.StringVar(value="src")  # Por defecto asigna como ORIGEN
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

        # ── Indicadores del aeropuerto ORIGEN y DESTINO actualmente elegidos ──
        src_f = tk.Frame(left, bg=BG3, pady=4)
        src_f.pack(fill="x", padx=12, pady=(8, 2))
        tk.Label(src_f, text="ORIGEN:", font=FONT_MONO, fg=GREEN, bg=BG3).pack(side="left", padx=6)
        # textvariable=self.src_var: se actualiza automáticamente cuando cambia el origen
        tk.Label(src_f, textvariable=self.src_var,
                 font=("Courier New", 11, "bold"), fg=GREEN, bg=BG3).pack(side="left")

        dst_f = tk.Frame(left, bg=BG3, pady=4)
        dst_f.pack(fill="x", padx=12, pady=2)
        tk.Label(dst_f, text="DESTINO:", font=FONT_MONO, fg=YELLOW, bg=BG3).pack(side="left", padx=6)
        tk.Label(dst_f, textvariable=self.dst_var,
                 font=("Courier New", 11, "bold"), fg=YELLOW, bg=BG3).pack(side="left")

        # ── Botón para calcular y dibujar la ruta mínima en el mapa ──────────
        tk.Button(left, text="Dibujar Ruta Mínima", font=FONT_MONO,
                  bg=ACCENT, fg="#0f1117", relief="flat", padx=10, pady=6,
                  cursor="hand2", command=self._draw_route).pack(fill="x", padx=12, pady=(10, 4))

        # ── Botón para borrar la ruta y limpiar el mapa ───────────────────────
        tk.Button(left, text="Limpiar Ruta", font=FONT_MONO,
                  bg=BG3, fg=RED, relief="flat", padx=10, pady=4,
                  cursor="hand2", command=self._clear_route).pack(fill="x", padx=12)

        # ── Etiqueta de estado: muestra mensajes sobre la ruta calculada ──────
        self.route_status = tk.Label(left, text="", font=FONT_MONO, fg=FG,
                                     bg=BG2, wraplength=270, justify="left")
        self.route_status.pack(pady=8, padx=12, anchor="w")

        # ── Sección de información del aeropuerto clicado en el mapa ─────────
        tk.Label(left, text="─" * 34, fg="#333", bg=BG2).pack()
        tk.Label(left, text="Aeropuerto seleccionado:", font=FONT_MONO,
                 fg="#888", bg=BG2).pack(anchor="w", padx=12, pady=(6, 2))
        self.info_lbl = tk.Label(left, text="—", font=FONT_MONO, fg=FG,
                                 bg=BG2, wraplength=280, justify="left")
        self.info_lbl.pack(anchor="w", padx=12)

        # ── Tabla que lista los aeropuertos del camino mínimo, paso a paso ───
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

        # ── Panel derecho: contenedor del mapa ────────────────────────────────
        right = tk.Frame(parent, bg="#111")
        right.pack(side="right", fill="both", expand=True)

        # Mensaje de espera mientras el mapa se descarga e inicializa
        self.loading_lbl = tk.Label(right,
                                    text="Cargando mapa… (requiere conexión a internet)",
                                    font=("Courier New", 12), fg=ACCENT, bg="#111")
        self.loading_lbl.place(relx=0.5, rely=0.5, anchor="center")

        # Espera 800 ms antes de inicializar el mapa para que la ventana
        # termine de dibujarse primero y no se vea un parpadeo
        right.after(800, lambda: self._init_map(right))

    def _init_map(self, container):
        """
        Inicializa el widget del mapa interactivo dentro del panel derecho.
        - Centra la vista en el ecuador (lat=20, lon=0) con zoom mundial.
        - Registra el callback para clics en el mapa.
        - Si falla (sin internet o error de librería), muestra el mensaje de error.
        """
        try:
            self.map_widget = tkintermapview.TkinterMapView(container, corner_radius=0)
            self.map_widget.pack(fill="both", expand=True)
            self.map_widget.set_position(20, 0)   # Vista inicial: centro del mundo
            self.map_widget.set_zoom(2)            # Zoom alejado para ver todo el globo
            # Registra la función que se llamará cada vez que el usuario haga clic en el mapa
            self.map_widget.add_left_click_map_command(self._on_map_click)
            self._map_ready = True
            self.loading_lbl.destroy()  # Elimina el mensaje "Cargando…"
        except Exception as e:
            self.loading_lbl.config(text=f"Error al cargar el mapa:\n{e}", fg=RED)

    def _on_map_click(self, coords):
        """
        Se ejecuta cuando el usuario hace clic en cualquier punto del mapa
        (no sobre un marcador). Actualmente no hace nada, pero está disponible
        como punto de extensión futura (por ejemplo, buscar el aeropuerto más cercano).
        
        coords → tupla (latitud, longitud) del punto clicado
        """
        pass

    def _on_marker_click(self, code):
        """
        Se ejecuta cuando el usuario hace clic sobre el marcador de un aeropuerto.
        1. Muestra la información completa del aeropuerto en el panel lateral.
        2. Asigna ese aeropuerto como ORIGEN o DESTINO según el modo seleccionado
           con los botones de radio del panel izquierdo.

        code → código IATA del aeropuerto clicado (ej: "BOG", "JFK")
        """
        ap = self.graph.airports.get(code, {})
        self.info_lbl.config(
            text=(f"Código: {ap.get('code')}\n"
                  f"Nombre: {ap.get('name')}\n"
                  f"Ciudad: {ap.get('city')}\n"
                  f"País: {ap.get('country')}\n"
                  f"Lat: {ap.get('lat')}  Lon: {ap.get('lon')}")
        )
        # Asigna el aeropuerto al campo que corresponda según el modo activo
        if self.mode_var.get() == "src":
            self.src_var.set(code)
        else:
            self.dst_var.set(code)

    def _draw_route(self):
        """
        Se ejecuta al presionar "Dibujar Ruta Mínima".
        Valida que haya un origen y destino válidos, luego lanza el cálculo
        de Dijkstra en un hilo separado para no congelar la interfaz.
        """
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
        """
        Ejecuta Dijkstra en segundo plano y reconstruye el camino más corto.
        Al terminar, solicita a tkinter que dibuje la ruta en el mapa de forma segura.

        src → código del aeropuerto origen
        dst → código del aeropuerto destino
        """
        dist, prev = self.graph.dijkstra(src)
        # Reconstruye la lista ordenada de aeropuertos desde src hasta dst
        path = self.graph.reconstruct_path(prev, src, dst)
        d = dist.get(dst, float("inf"))  # float("inf") si dst no es alcanzable
        self.parent.after(0, lambda: self._render_path(path, d, src, dst))

    def _render_path(self, path, dist_km, src, dst):
        """
        Dibuja la ruta sobre el mapa y actualiza la tabla de pasos.
        Se ejecuta siempre en el hilo principal (llamado via after()).

        1. Limpia cualquier ruta previa.
        2. Extrae las coordenadas de cada aeropuerto en el camino.
        3. Centra y ajusta el zoom del mapa según la longitud de la ruta.
        4. Dibuja la línea amarilla que conecta los aeropuertos.
        5. Coloca marcadores: verde para el origen, rojo para el destino,
           amarillo para los intermedios.
        6. Llena la tabla lateral con los aeropuertos del camino.
        7. Muestra el resumen (saltos y distancia total).

        path    → lista de códigos de aeropuertos en orden (ej: ["BOG","MIA","JFK"])
        dist_km → distancia total de la ruta en km
        src     → código del aeropuerto origen
        dst     → código del aeropuerto destino
        """
        self._clear_route()
        import math
        if not path or dist_km == math.inf:
            self.route_status.config(text=f"No hay camino entre {src} y {dst}.", fg=RED)
            return

        # Obtiene la lista de (latitud, longitud) para cada aeropuerto del camino
        coords = [(self.graph.airports[c]["lat"], self.graph.airports[c]["lon"]) for c in path]

        # Centra el mapa en el punto medio del camino y elige el zoom según la cantidad de saltos
        mid = coords[len(coords) // 2]
        self.map_widget.set_position(*mid)
        zoom = 5 if len(path) <= 3 else (4 if len(path) <= 8 else 3)
        self.map_widget.set_zoom(zoom)

        # Dibuja la línea que conecta todos los aeropuertos del camino
        self._path_line = self.map_widget.set_path(coords, color="#ffd54f", width=3)

        # Coloca un marcador en cada aeropuerto del camino con el color correspondiente
        for i, code in enumerate(path):
            ap = self.graph.airports[code]
            # Verde = primer aeropuerto (origen), Rojo = último (destino), Amarillo = intermedios
            color = "#a5d6a7" if i == 0 else ("#ef9a9a" if i == len(path) - 1 else "#ffd54f")
            label = f"{code}  {ap.get('city', '')}"
            m = self.map_widget.set_marker(
                ap["lat"], ap["lon"], text=label,
                marker_color_circle=color,
                marker_color_outside="#222",
                # lambda con c=code captura el código correcto en cada iteración del bucle
                command=lambda mk, c=code: self._on_marker_click(c),
            )
            self._path_markers.append(m)

        # Llena la tabla lateral con el paso a paso de la ruta
        self.path_tree.delete(*self.path_tree.get_children())
        for i, code in enumerate(path):
            ap = self.graph.airports.get(code, {})
            # Etiqueta para colorear: origen verde, destino rojo, intermedios amarillo
            tag = "src" if i == 0 else ("dst" if i == len(path) - 1 else "mid")
            self.path_tree.insert("", "end",
                                  values=(i + 1, code, ap.get("city", "")),
                                  tags=(tag,))

        self.path_tree.tag_configure("src", background="#1a3a1a", foreground=GREEN)
        self.path_tree.tag_configure("dst", background="#3a1a1a", foreground=RED)
        self.path_tree.tag_configure("mid", background=BG3, foreground=YELLOW)

        # Muestra el resumen de la ruta: saltos y distancia total
        self.route_status.config(
            text=f"✔ {src} → {dst}\n{len(path)-1} salto(s) | {dist_km:,.2f} km",
            fg=GREEN)

    def _clear_route(self):
        """
        Elimina del mapa la ruta actualmente dibujada:
        - Borra la línea del camino.
        - Elimina todos los marcadores de los aeropuertos de la ruta.
        - Limpia la tabla de pasos y el mensaje de estado.
        Los try/except evitan que un error al borrar un elemento rompa toda la limpieza.
        """
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
        """
        Método público llamado desde otras pestañas (especialmente Tab4).
        Permite que la pestaña 4 le "envíe" una ruta ya calculada al mapa
        para que la dibuje sin necesidad de recalcular Dijkstra.

        path    → lista de códigos de aeropuertos en orden
        dist_km → distancia total de la ruta en km

        Solo actúa si el mapa ya terminó de cargar (_map_ready = True).
        """
        if path and self._map_ready:
            self._render_path(path, dist_km, path[0], path[-1])