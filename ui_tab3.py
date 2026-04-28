"""
ui_tab3.py
Pestaña 3: Árbol de Expansión Mínima (Kruskal).
Si hay más de una componente, calcula el MST de cada una.
"""

# Librería estándar de Python para crear interfaces gráficas de escritorio
import tkinter as tk
# Módulo de tkinter que provee widgets con mejor apariencia visual (tablas, barras de scroll, etc.)
from tkinter import ttk
# Permite ejecutar tareas pesadas en segundo plano sin congelar la ventana
import threading

# ── Paleta de colores de la interfaz ──────────────────────────────────────────
BG = "#0f1117"       # Fondo principal (negro azulado oscuro)
BG2 = "#151822"      # Fondo secundario (un poco más claro)
BG3 = "#1e2130"      # Fondo terciario (para filas alternas en tablas)
FG = "#e0e0e0"       # Color del texto general (gris claro)
ACCENT = "#ffb74d"   # Color de acento (naranja) — títulos y botones
GREEN = "#a5d6a7"    # Verde — mensajes de éxito
YELLOW = "#ffd54f"   # Amarillo — mensajes de progreso/espera
RED = "#ef9a9a"      # Rojo — mensajes de error (reservado para uso futuro)
FONT_MONO = ("Courier New", 11)        # Fuente monoespaciada para datos
FONT_TITLE = ("Courier New", 14, "bold")  # Fuente grande y negrita para títulos


class Tab3MST:
    """
    Clase que representa la pestaña 3 de la aplicación.
    Se encarga de calcular y mostrar el Árbol de Expansión Mínima (MST)
    usando el algoritmo de Kruskal para cada componente conexa del grafo.
    """

    def __init__(self, parent, graph):
        """
        Constructor: se ejecuta cuando se crea la pestaña.
        
        parent → el contenedor visual (frame) donde se dibujará todo
        graph  → el objeto que contiene los aeropuertos y sus conexiones
        """
        self.parent = parent
        self.graph = graph
        self._build()  # Construye todos los elementos visuales

    def _build(self):
        """
        Construye la interfaz gráfica completa de esta pestaña:
        título, botón, tabla resumen por componente y tabla de detalle de aristas.
        """
        parent = self.parent

        # ── Título principal de la pestaña ────────────────────────────────────
        tk.Label(
            parent,
            text="Árbol de Expansión Mínima — Kruskal",
            font=FONT_TITLE,
            fg=ACCENT,
            bg=BG,
        ).pack(pady=(18, 4))

        # ── Subtítulo explicativo ─────────────────────────────────────────────
        tk.Label(
            parent,
            text="Algoritmo de Kruskal con Union-Find. Los pesos son distancias en km (Haversine).",
            font=("Courier New", 10),
            fg="#888",
            bg=BG,
        ).pack()

        # ── Botón para iniciar el cálculo del MST ────────────────────────────
        btn = tk.Button(
            parent,
            text="Calcular MST(s)",
            font=FONT_MONO,
            bg=ACCENT,
            fg="#0f1117",
            activebackground="#ffe0b2",
            relief="flat",
            padx=18,
            pady=8,
            cursor="hand2",
            command=self._run,  # Al hacer clic, llama al método _run
        )
        btn.pack(pady=16)

        # ── Etiqueta de estado que muestra mensajes como "Calculando…" ────────
        self.progress_lbl = tk.Label(parent, text="", font=FONT_MONO, fg=YELLOW, bg=BG)
        self.progress_lbl.pack()

        # ── Tabla resumen: una fila por cada componente conexa del grafo ──────
        summary_frame = tk.Frame(parent, bg=BG)
        summary_frame.pack(fill="x", padx=20, pady=4)

        cols_sum = ("Componente", "Vértices", "Aristas MST", "Peso Total (km)")
        self.tree_sum = ttk.Treeview(summary_frame, columns=cols_sum, show="headings", height=8)

        # Estilo visual para todas las tablas (fondo oscuro, texto claro)
        style = ttk.Style()
        style.configure("Treeview", background=BG3, foreground=FG, fieldbackground=BG3, rowheight=24, font=FONT_MONO)
        style.configure("Treeview.Heading", background=BG2, foreground=ACCENT, font=("Courier New", 10, "bold"))

        # Configura el ancho y alineación de cada columna del resumen
        for col in cols_sum:
            self.tree_sum.heading(col, text=col)
            self.tree_sum.column(col, width=200, anchor="center")

        # Barra de scroll vertical para la tabla resumen
        sc_sum = ttk.Scrollbar(summary_frame, orient="vertical", command=self.tree_sum.yview)
        self.tree_sum.configure(yscrollcommand=sc_sum.set)
        self.tree_sum.pack(side="left", fill="both", expand=True)
        sc_sum.pack(side="right", fill="y")

        # Estilos de filas: naranja para la componente más grande, alternas para las demás
        self.tree_sum.tag_configure("big", background="#2a1e0a", foreground=ACCENT)
        self.tree_sum.tag_configure("odd", background=BG3)
        self.tree_sum.tag_configure("even", background=BG2)

        # ── Instrucción sobre la tabla de detalle ─────────────────────────────
        tk.Label(parent, text="Aristas del MST — haz clic en una componente", font=("Courier New", 10), fg="#888", bg=BG).pack(pady=(8, 2))

        # ── Tabla de detalle: muestra las aristas del MST de la componente seleccionada ──
        detail_frame = tk.Frame(parent, bg=BG)
        detail_frame.pack(fill="both", expand=True, padx=20, pady=4)

        cols_det = ("Desde", "Hacia", "Distancia (km)")
        self.tree_det = ttk.Treeview(detail_frame, columns=cols_det, show="headings", height=12)

        # Configura columnas de la tabla de detalle
        for col in cols_det:
            self.tree_det.heading(col, text=col)
            self.tree_det.column(col, width=300, anchor="center")

        # Barra de scroll para la tabla de detalle
        sc_det = ttk.Scrollbar(detail_frame, orient="vertical", command=self.tree_det.yview)
        self.tree_det.configure(yscrollcommand=sc_det.set)
        self.tree_det.pack(side="left", fill="both", expand=True)
        sc_det.pack(side="right", fill="y")

        # Lista interna que guarda los resultados del MST por componente
        # Cada elemento es una tupla: (lista_vertices, peso_total, lista_aristas)
        self._mst_data = []

        # Cuando el usuario haga clic en una fila del resumen, se llama a _on_select
        self.tree_sum.bind("<<TreeviewSelect>>", self._on_select)

    def _run(self):
        """
        Se ejecuta al hacer clic en el botón "Calcular MST(s)".
        Limpia los resultados anteriores y lanza el cálculo en un hilo separado
        para que la ventana no se congele mientras trabaja.
        """
        self.progress_lbl.config(text="Calculando… (puede tardar unos segundos)")
        self.tree_sum.delete(*self.tree_sum.get_children())  # Limpia tabla resumen
        self.tree_det.delete(*self.tree_det.get_children())  # Limpia tabla detalle
        self._mst_data = []
        # Lanza _compute en segundo plano (daemon=True: el hilo muere si se cierra la app)
        threading.Thread(target=self._compute, daemon=True).start()

    def _compute(self):
        """
        Realiza el cálculo pesado en segundo plano (fuera del hilo principal).
        1. Obtiene todas las componentes conexas del grafo (grupos de aeropuertos conectados).
        2. Las ordena de mayor a menor según cantidad de vértices.
        3. Aplica Kruskal a cada componente para obtener su MST.
        4. Cuando termina, pide a tkinter que muestre los resultados de forma segura.
        """
        components = self.graph.get_components()
        components.sort(key=lambda c: len(c), reverse=True)  # La más grande primero
        results = []
        for comp in components:
            weight, edges = self.graph.kruskal_mst(comp)  # Kruskal sobre esta componente
            results.append((comp, weight, edges))
        # after() es la forma segura de actualizar la UI desde un hilo secundario
        self.parent.after(0, lambda: self._show(results))

    def _show(self, results):
        """
        Muestra los resultados en la tabla resumen una vez que el cálculo terminó.
        Cada fila representa una componente conexa con: número, vértices, aristas MST y peso total.
        
        results → lista de tuplas (componente, peso_total, aristas)
        """
        self.progress_lbl.config(text=f"MST calculado para {len(results)} componente(s).", fg=GREEN)
        self._mst_data = results
        self.tree_sum.delete(*self.tree_sum.get_children())

        for i, (comp, weight, edges) in enumerate(results, 1):
            # La componente más grande se resalta en naranja; las demás alternan colores
            tag = "big" if i == 1 else ("even" if i % 2 == 0 else "odd")
            self.tree_sum.insert(
                "", "end",
                values=(i, len(comp), len(edges), f"{weight:,.2f}"),
                tags=(tag,),
                iid=str(i - 1),  # ID de fila = índice en _mst_data
            )

    def _on_select(self, event):
        """
        Se ejecuta cuando el usuario hace clic en una fila de la tabla resumen.
        Carga y muestra en la tabla de detalle todas las aristas del MST
        de la componente seleccionada (origen → destino → distancia en km).
        """
        sel = self.tree_sum.selection()
        if not sel:
            return  # No hay nada seleccionado, no hacer nada

        idx = int(sel[0])  # El IID de la fila corresponde al índice en _mst_data
        _, _, edges = self._mst_data[idx]  # Extrae solo las aristas de esa componente

        self.tree_det.delete(*self.tree_det.get_children())  # Limpia detalle anterior

        # Inserta cada arista (u→v con peso w) como una fila en la tabla de detalle
        for j, (u, v, w) in enumerate(edges):
            tag = "even" if j % 2 == 0 else "odd"
            self.tree_det.insert("", "end", values=(u, v, f"{w:,.2f}"), tags=(tag,))

        # Aplica colores alternos a las filas del detalle
        self.tree_det.tag_configure("even", background=BG3)
        self.tree_det.tag_configure("odd", background=BG2)