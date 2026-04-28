"""
tk_table.py
Documentado por Juan Salcedo
Tabla scrollable hecha 100% con tk puro (sin ttk).
Evita un que presentabamos con ttk.Style que cambiaba los colores entre ejecuciones.
"""

import tkinter as tk

# ── Paleta de colores para la tabla ───────────────────────────────────────────
BG  = "#0f1117"   # Fondo principal
BG2 = "#151822"   # Fondo de la cabecera
BG3 = "#1e2130"   # Color de filas pares
BG4 = "#232738"   # Color de filas impares (ligeramente distinto para alternar)
FG  = "#e0e0e0"   # Color del texto


class TkTable(tk.Frame):
    """
    Tabla personalizada con scroll vertical, construida completamente con tk puro.
    Se usa en lugar de ttk.Treeview porque ttk tiene un bug en Windows donde
    los colores de fondo de las celdas se pierden o cambian entre ejecuciones.

    Cada instancia de esta clase ES un Frame (hereda de tk.Frame), por lo que
    se puede colocar en la ventana como cualquier otro widget de tkinter.
    """

    def __init__(self, parent, columns, height=400, row_h=24,
                 bg=BG, header_bg=BG2, row_bg1=BG3, row_bg2=BG4,
                 fg=FG, header_fg="#4fc3f7", font=("Courier New", 10),
                 header_font=("Courier New", 10, "bold"), **kwargs):
        """
        Constructor: crea y configura la tabla completa.

        parent      → el contenedor donde se colocará la tabla
        columns     → lista de tuplas que definen cada columna:
                      (nombre_cabecera, ancho_en_px, alineación)
                      Ejemplo: [("Código", 70, "center"), ("Ciudad", 150, "w")]
        height      → altura visible de la tabla en píxeles (el resto se scrollea)
        row_h       → altura de cada fila en píxeles
        bg          → color de fondo general
        header_bg   → color de fondo de la fila de cabecera
        row_bg1     → color de fondo para filas pares
        row_bg2     → color de fondo para filas impares (efecto zebra)
        fg          → color del texto de las filas
        header_fg   → color del texto de la cabecera
        font        → fuente para el contenido de las filas
        header_font → fuente para los títulos de la cabecera
        **kwargs    → parámetros adicionales que se pasan al Frame padre
        """
        # Inicializa el Frame base del que hereda esta clase
        super().__init__(parent, bg=bg, **kwargs)

        # Guarda la configuración para usarla al insertar filas
        self._cols     = columns    # Definición de columnas
        self._row_h    = row_h      # Altura de cada fila
        self._bg       = bg         # Fondo general
        self._row_bg1  = row_bg1    # Fondo filas pares
        self._row_bg2  = row_bg2    # Fondo filas impares
        self._fg       = fg         # Color de texto
        self._font     = font       # Fuente del texto
        self._rows     = []         # Lista con los datos de cada fila insertada
        self._row_frames = []       # Lista con los widgets Frame de cada fila (para poder borrarlos)

        # ── Cabecera fija (no hace scroll, siempre visible arriba) ────────────
        header = tk.Frame(self, bg=header_bg)
        header.pack(fill="x")

        # Crea una celda por cada columna definida en 'columns'
        for name, w, anchor in columns:
            cell = tk.Frame(header, bg=header_bg, width=w, height=28)
            cell.pack_propagate(False)   # Impide que el Frame se achique según el Label interno
            cell.pack(side="left")
            tk.Label(cell, text=name, font=header_font,
                     fg=header_fg, bg=header_bg,
                     anchor=anchor, padx=4).pack(fill="both", expand=True)

        # Línea separadora visual entre la cabecera y las filas de datos
        tk.Frame(self, bg="#2a2a3a", height=1).pack(fill="x")

        # ── Área scrollable: Canvas + Scrollbar + Frame interno ───────────────
        # Se necesita un Canvas porque tkinter no permite hacer scroll
        # directamente sobre un Frame; hay que "poner" el Frame dentro del Canvas.
        container = tk.Frame(self, bg=bg)
        container.pack(fill="both", expand=True)

        self._canvas = tk.Canvas(container, bg=bg,
                                 highlightthickness=0, height=height)
        # Scrollbar vertical que controla el desplazamiento del Canvas
        scrollbar = tk.Scrollbar(container, orient="vertical",
                                 command=self._canvas.yview,
                                 bg=bg, troughcolor=BG2)
        self._canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self._canvas.pack(side="left", fill="both", expand=True)

        # Frame interno que contiene todas las filas de datos;
        # vive "dentro" del Canvas y es el que realmente se desplaza
        self._inner = tk.Frame(self._canvas, bg=bg)
        # create_window incrusta el Frame dentro del Canvas en la posición (0,0)
        self._window = self._canvas.create_window(
            (0, 0), window=self._inner, anchor="nw")

        # Eventos para mantener el Canvas sincronizado con su contenido
        # Se llama cada vez que el Frame interno cambia de tamaño (al agregar filas)
        self._inner.bind("<Configure>", self._on_configure)
        # Se llama cada vez que el Canvas cambia de tamaño (al redimensionar la ventana)
        self._canvas.bind("<Configure>", self._on_canvas_resize)
        # Permite hacer scroll con la rueda del ratón sobre la tabla
        self._canvas.bind("<MouseWheel>", self._on_mousewheel)

    def _on_configure(self, e):
        """
        Se dispara cada vez que el Frame interno cambia de tamaño
        (por ejemplo, al agregar una nueva fila).
        Actualiza la región scrollable del Canvas para que el scroll
        llegue hasta el final del contenido.
        """
        self._canvas.configure(scrollregion=self._canvas.bbox("all"))

    def _on_canvas_resize(self, e):
        """
        Se dispara cuando el Canvas cambia de ancho (al redimensionar la ventana).
        Ajusta el ancho del Frame interno para que siempre ocupe todo el ancho
        disponible del Canvas, evitando que las filas queden cortadas o con espacio vacío.
        """
        self._canvas.itemconfig(self._window, width=e.width)

    def _on_mousewheel(self, e):
        """
        Permite desplazar la tabla con la rueda del ratón.
        e.delta devuelve cuánto giró la rueda: positivo = arriba, negativo = abajo.
        Se divide entre 120 porque Windows reporta el delta en múltiplos de 120.
        El int(-1 * ...) invierte la dirección para que sea intuitiva.
        """
        self._canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")

    def clear(self):
        """
        Elimina todas las filas de datos de la tabla.
        Destruye cada widget Frame de fila (lo que elimina también sus Labels internos)
        y vacía las listas internas de datos y widgets.
        Se usa antes de cargar nuevos resultados para no acumular filas viejas.
        """
        for f in self._row_frames:
            f.destroy()
        self._row_frames = []
        self._rows = []

    def insert(self, values, bg=None, fg=None):
        """
        Agrega una nueva fila al final de la tabla.

        values → lista o tupla con los valores de cada celda, en el mismo orden
                 que las columnas definidas al crear la tabla.
                 Ejemplo: ("BOG", "El Dorado", "Bogotá", "Colombia")

        bg     → color de fondo personalizado para esta fila (opcional).
                 Si no se indica, se alternan automáticamente row_bg1 y row_bg2.
        fg     → color de texto personalizado para esta fila (opcional).
                 Si no se indica, usa el color fg por defecto de la tabla.
        """
        idx = len(self._rows)  # Número de filas actuales → determina si es par o impar
        row_bg = bg if bg else (self._row_bg1 if idx % 2 == 0 else self._row_bg2)
        row_fg = fg if fg else self._fg

        # Frame que representa la fila completa
        row_frame = tk.Frame(self._inner, bg=row_bg, height=self._row_h)
        row_frame.pack(fill="x")
        row_frame.pack_propagate(False)  # Mantiene la altura fija aunque el Label sea pequeño

        # Crea una celda por cada columna, asignando el valor correspondiente
        for val, (_, w, anchor) in zip(values, self._cols):
            cell = tk.Frame(row_frame, bg=row_bg, width=w, height=self._row_h)
            cell.pack_propagate(False)
            cell.pack(side="left")
            tk.Label(cell, text=str(val), font=self._font,
                     fg=row_fg, bg=row_bg,
                     anchor=anchor, padx=4).pack(fill="both", expand=True)

        # Guarda la referencia al frame y los datos para poder borrarlos luego con clear()
        self._rows.append(values)
        self._row_frames.append(row_frame)

    def scroll_top(self):
        """
        Desplaza el scroll de la tabla hasta arriba del todo (posición 0.0 = inicio).
        Útil para volver al principio después de cargar nuevos resultados,
        para que el usuario vea desde la primera fila.
        """
        self._canvas.yview_moveto(0)