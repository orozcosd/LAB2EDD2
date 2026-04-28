"""
ui_tab1.py
Pestaña 1: Conectividad del grafo.
Docuemntado por: Santiago Orozco

Este archivo maneja la primera pestaña de la aplicación.
Su función es responder la pregunta:
¿El grafo de aeropuertos está completamente conectado?
Es decir, ¿puedes llegar desde cualquier aeropuerto a cualquier otro
siguiendo rutas de vuelo?

Si NO es conexo, muestra cuántos grupos separados (componentes) existen
y cuántos aeropuertos tiene cada uno.
"""

import tkinter as tk          # Librería para crear la interfaz gráfica
from tkinter import ttk       # Widgets mejorados (tabla con scroll)
import threading              # Para ejecutar el algoritmo sin congelar la pantalla


# ===========================================================================
# COLORES Y FUENTES DEL TEMA VISUAL
# Se definen aquí arriba para poder cambiarlos fácilmente en un solo lugar
# ===========================================================================
BG     = "#0f1117"   # Fondo principal: azul muy oscuro casi negro
BG2    = "#151822"   # Fondo secundario: un poco más claro
BG3    = "#1e2130"   # Fondo terciario: para filas alternas de la tabla
FG     = "#e0e0e0"   # Color de texto principal: gris claro
ACCENT = "#4fc3f7"   # Color de acento: azul claro (títulos, botones)
GREEN  = "#a5d6a7"   # Verde suave (resultado positivo / conexo)
YELLOW = "#ffd54f"   # Amarillo (proceso en curso / calculando)
RED    = "#ef9a9a"   # Rojo suave (resultado negativo / no conexo)
FONT_MONO  = ("Courier New", 11)        # Fuente monoespaciada normal
FONT_TITLE = ("Courier New", 14, "bold") # Fuente monoespaciada para títulos


# ===========================================================================
# CLASE TAB1CONECTIVIDAD
# Controla todo lo que ocurre dentro de la Pestaña 1
# ===========================================================================
class Tab1Conectividad:
    """
    Esta clase construye y maneja la pestaña de Conectividad.

    Flujo de uso:
    1. Al crearse, construye todos los elementos visuales (_build)
    2. El usuario hace clic en el botón → _run se activa
    3. _run lanza el cálculo en un hilo separado → _compute corre en paralelo
    4. Cuando _compute termina, llama a _show para actualizar la pantalla
    """

    def __init__(self, parent, graph):
        """
        Constructor de la pestaña.

        Parámetros:
          parent : el Frame (contenedor) de tkinter donde se dibujará esta pestaña
          graph  : el grafo de aeropuertos ya construido (objeto AirportGraph)
        """
        self.parent = parent  # Guardar referencia al contenedor padre
        self.graph  = graph   # Guardar referencia al grafo para usar sus algoritmos
        self._build()         # Construir inmediatamente todos los elementos visuales


    # ------------------------------------------------------------------
    # MÉTODO _build — Construye todos los elementos visuales de la pestaña
    # ------------------------------------------------------------------
    def _build(self):
        """
        Crea y organiza todos los widgets (elementos visuales) de la pestaña:
        - Título descriptivo
        - Subtítulo explicativo
        - Botón para ejecutar el análisis
        - Etiqueta para mostrar el resultado
        - Tabla con las componentes encontradas

        Este método se llama solo una vez al crear la pestaña.
        """
        parent = self.parent  # Alias corto para no escribir self.parent todo el tiempo

        # ── TÍTULO PRINCIPAL ──────────────────────────────────────────────
        tk.Label(
            parent,
            text="Análisis de Conectividad del Grafo",
            font=FONT_TITLE,
            fg=ACCENT,   # Texto azul claro
            bg=BG,       # Fondo oscuro
        ).pack(pady=(18, 4))
        # pady=(18, 4) = 18 píxeles arriba, 4 píxeles abajo

        # ── SUBTÍTULO EXPLICATIVO ─────────────────────────────────────────
        tk.Label(
            parent,
            text="Determina si el grafo es conexo usando BFS sobre todos los vértices.",
            font=("Courier New", 10),
            fg="#888",   # Gris oscuro (texto secundario)
            bg=BG,
        ).pack()

        # ── BOTÓN PARA EJECUTAR EL ANÁLISIS ──────────────────────────────
        btn = tk.Button(
            parent,
            text="Analizar Conectividad",
            font=FONT_MONO,
            bg=ACCENT,              # Fondo azul claro
            fg="#0f1117",           # Texto oscuro (contraste sobre azul)
            activebackground="#81d4fa",  # Color al hacer clic
            relief="flat",          # Sin borde en relieve (apariencia moderna)
            padx=18,                # Espaciado horizontal interno
            pady=8,                 # Espaciado vertical interno
            cursor="hand2",         # Cursor de mano al pasar sobre el botón
            command=self._run,      # Función que se llama al hacer clic
        )
        btn.pack(pady=16)  # 16 píxeles de margen arriba y abajo

        # ── ETIQUETA DE RESULTADO ─────────────────────────────────────────
        # Empieza vacía y se llena con el resultado después del análisis
        # Puede mostrar: "El grafo ES CONEXO" o "NO ES CONEXO → X componentes"
        self.result_lbl = tk.Label(
            parent,
            text="",                          # Vacía al inicio
            font=("Courier New", 13, "bold"),
            bg=BG,
        )
        self.result_lbl.pack()

        # ── TABLA DE COMPONENTES ──────────────────────────────────────────
        # Muestra cada componente conexa con su número, cantidad de vértices
        # y una muestra de los aeropuertos que la forman

        # Frame contenedor de la tabla (para poder colocar la barra de scroll al lado)
        table_frame = tk.Frame(parent, bg=BG)
        table_frame.pack(fill="both", expand=True, padx=20, pady=10)
        # fill="both" + expand=True = ocupa todo el espacio disponible

        # Definir las columnas de la tabla
        cols = ("#", "Vértices", "Aeropuertos (muestra)")

        # Crear la tabla (Treeview es el widget de tabla de ttk)
        # height=24 = mostrar hasta 24 filas sin necesidad de scroll
        self.tree = ttk.Treeview(table_frame, columns=cols, show="headings", height=24)
        # show="headings" = mostrar solo los encabezados, sin columna de árbol

        # Configurar el estilo visual de la tabla
        style = ttk.Style()
        style.configure("Treeview",
                        background=BG3,        # Fondo de las filas
                        foreground=FG,         # Color del texto
                        fieldbackground=BG3,   # Fondo del área de datos
                        rowheight=24,          # Altura de cada fila en píxeles
                        font=FONT_MONO)
        style.configure("Treeview.Heading",
                        background=BG2,        # Fondo de los encabezados
                        foreground=ACCENT,     # Texto azul en encabezados
                        font=("Courier New", 10, "bold"))
        style.map("Treeview",
                  background=[("selected", "#263238")])  # Color al seleccionar fila

        # Configurar cada columna: encabezado y ancho
        for col in cols:
            self.tree.heading(col, text=col)  # Texto del encabezado
        self.tree.column("#",                     width=50,  anchor="center")
        self.tree.column("Vértices",              width=100, anchor="center")
        self.tree.column("Aeropuertos (muestra)", width=700)

        # Crear barra de scroll vertical para la tabla
        scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        # Conectar la barra de scroll con la tabla (se mueven juntas)
        self.tree.configure(yscrollcommand=scroll.set)

        # Colocar la tabla y la barra de scroll lado a lado
        self.tree.pack(side="left",  fill="both", expand=True)
        scroll.pack(side="right", fill="y")


    # ------------------------------------------------------------------
    # MÉTODO _run — Se activa cuando el usuario hace clic en el botón
    # ------------------------------------------------------------------
    def _run(self):
        """
        Prepara la interfaz para el análisis y lanza el cálculo
        en un hilo separado para no congelar la pantalla.

        ¿Por qué en un hilo separado?
        El BFS sobre 3256 aeropuertos puede tardar un momento.
        Si lo ejecutáramos directamente aquí, la ventana se congelaría
        hasta que terminara. Con threading, la interfaz sigue respondiendo.
        """
        # Mostrar mensaje de "calculando" mientras espera el resultado
        self.result_lbl.config(text="Calculando…", fg=YELLOW)

        # Limpiar la tabla de resultados anteriores
        # get_children() retorna todos los IDs de filas existentes
        # El * desempaqueta la lista para pasarla como argumentos individuales
        self.tree.delete(*self.tree.get_children())

        # Lanzar el cálculo en un hilo secundario
        # daemon=True = el hilo se cierra automáticamente con la ventana
        threading.Thread(target=self._compute, daemon=True).start()


    # ------------------------------------------------------------------
    # MÉTODO _compute — Ejecuta el algoritmo BFS (corre en hilo secundario)
    # ------------------------------------------------------------------
    def _compute(self):
        """
        Ejecuta el algoritmo de conectividad usando el grafo.
        Este método corre en un hilo separado, NO en el hilo principal.

        IMPORTANTE: Desde un hilo secundario NO se puede modificar la
        interfaz directamente. Por eso al terminar usamos self.parent.after()
        para programar la actualización visual en el hilo principal.
        """
        # Llamar al método del grafo que ejecuta BFS y retorna las componentes
        # Resultado: lista de sets, ej: [{JFK, LAX, ...}, {aeropuerto_aislado}]
        components = self.graph.get_components()

        # Verificar si el grafo es conexo (solo 1 componente = todos conectados)
        connected = len(components) == 1

        # Ordenar las componentes de MAYOR a MENOR cantidad de vértices
        # La componente principal (más grande) aparecerá primera en la tabla
        components.sort(key=lambda c: len(c), reverse=True)

        # Programar la actualización de la interfaz en el hilo principal
        # after(0, función) = ejecutar 'función' lo antes posible en el hilo principal
        # Usamos lambda para pasar los parámetros a _show
        self.parent.after(0, lambda: self._show(components, connected))


    # ------------------------------------------------------------------
    # MÉTODO _show — Actualiza la interfaz con los resultados
    # ------------------------------------------------------------------
    def _show(self, components, connected):
        """
        Muestra los resultados del análisis en la interfaz.
        Este método corre en el hilo PRINCIPAL (llamado por after()).

        Parámetros:
          components : lista de sets con las componentes conexas encontradas
          connected  : True si el grafo es conexo, False si no lo es
        """

        # ── MOSTRAR RESULTADO PRINCIPAL ───────────────────────────────────
        if connected:
            # El grafo tiene solo 1 componente: todos los aeropuertos están conectados
            self.result_lbl.config(
                text="El grafo ES CONEXO.",
                fg=GREEN,  # Verde = resultado positivo
            )
        else:
            # El grafo tiene múltiples componentes: hay aeropuertos aislados
            self.result_lbl.config(
                text=f"El grafo NO ES CONEXO → {len(components)} componentes conexas.",
                fg=RED,    # Rojo = resultado negativo
            )

        # ── LLENAR LA TABLA CON LAS COMPONENTES ──────────────────────────
        # Limpiar filas anteriores antes de agregar las nuevas
        self.tree.delete(*self.tree.get_children())

        for i, comp in enumerate(components, 1):
            # Crear una muestra de hasta 8 aeropuertos de esta componente
            # sorted() ordena los códigos alfabéticamente para consistencia
            sample = ", ".join(sorted(comp)[:8])

            # Si la componente tiene más de 8 aeropuertos, indicar cuántos faltan
            if len(comp) > 8:
                sample += f"  … ({len(comp) - 8} más)"

            # Asignar una etiqueta (tag) para dar color diferente a cada fila:
            # "big"  = primera fila (componente más grande) → fondo verde oscuro
            # "even" = filas pares → fondo BG2
            # "odd"  = filas impares → fondo BG3
            tag = "big" if i == 1 else ("even" if i % 2 == 0 else "odd")

            # Insertar la fila en la tabla
            # "" = insertar en la raíz (no como hijo de otra fila)
            # "end" = agregar al final de la tabla
            # values = los datos de cada celda en orden de columnas
            self.tree.insert("", "end", values=(i, len(comp), sample), tags=(tag,))

        # Configurar los colores de cada tipo de etiqueta
        # La componente más grande (i=1) se resalta en verde
        self.tree.tag_configure("big",  background="#1a2a1a", foreground=GREEN)
        self.tree.tag_configure("odd",  background=BG3)
        self.tree.tag_configure("even", background=BG2)