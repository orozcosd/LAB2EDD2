"""
ui_tab2.py
Pestaña 2: Verificación de Grafo Bipartito.
Documentado por Keymer Perez.

Este archivo maneja la segunda pestaña de la aplicación.
Su función es responder la pregunta:
¿Se pueden dividir todos los aeropuertos en dos grupos (A y B) de forma
que ninguna ruta conecte dos aeropuertos del mismo grupo?

Si es posible → el grafo ES BIPARTITO
Si no es posible → el grafo NO ES BIPARTITO (hay ciclos de longitud impar)

Ejemplo visual de bipartito:
  Grupo A: {JFK, LAX, BOG}
  Grupo B: {MIA, CDG, LHR}
  Todas las rutas van de A→B o B→A, nunca A→A ni B→B

En redes aéreas reales casi nunca es bipartito porque los hubs
se conectan entre sí formando triángulos (ciclos impares).
"""

import tkinter as tk    # Para crear la interfaz gráfica
import threading        # Para ejecutar el algoritmo sin congelar la pantalla


# ===========================================================================
# COLORES Y FUENTES DEL TEMA VISUAL
# (mismos que en las otras pestañas para consistencia visual)
# ===========================================================================
BG     = "#0f1117"   # Fondo principal oscuro
BG2    = "#151822"   # Fondo secundario (panel de explicación)
BG3    = "#1e2130"   # Fondo terciario (cajas de estadísticas)
FG     = "#e0e0e0"   # Texto principal gris claro
ACCENT = "#ce93d8"   # Acento morado (diferente al azul de tab1, cada pestaña tiene su color)
GREEN  = "#a5d6a7"   # Verde = resultado positivo (sí es bipartito)
YELLOW = "#ffd54f"   # Amarillo = proceso en curso
RED    = "#ef9a9a"   # Rojo = resultado negativo (no es bipartito)
FONT_MONO  = ("Courier New", 11)
FONT_TITLE = ("Courier New", 14, "bold")


# ===========================================================================
# CLASE TAB2BIPARTITO
# Controla todo lo que ocurre dentro de la Pestaña 2
# ===========================================================================
class Tab2Bipartito:
    """
    Esta clase construye y maneja la pestaña de Bipartitividad.

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
          parent : el Frame contenedor donde se dibujará esta pestaña
          graph  : el grafo de aeropuertos ya construido (AirportGraph)
        """
        self.parent = parent
        self.graph  = graph
        self._build()  # Construir la interfaz inmediatamente


    # ------------------------------------------------------------------
    # MÉTODO _build — Construye todos los elementos visuales de la pestaña
    # ------------------------------------------------------------------
    def _build(self):
        """
        Crea y organiza todos los widgets de la pestaña:
        - Título
        - Panel de explicación del concepto
        - Botón para ejecutar la verificación
        - Etiqueta de resultado principal
        - Etiqueta de detalle
        - Separador visual
        - 4 cajas de estadísticas
        - Etiqueta de explicación del resultado
        """
        parent = self.parent

        # ── TÍTULO PRINCIPAL ──────────────────────────────────────────────
        tk.Label(
            parent,
            text="Verificación de Grafo Bipartito",
            font=FONT_TITLE,
            fg=ACCENT,   # Morado
            bg=BG
        ).pack(pady=(18, 6))

        # ── PANEL DE EXPLICACIÓN DEL CONCEPTO ────────────────────────────
        # Un rectángulo oscuro que explica qué es un grafo bipartito
        # para que el usuario entienda el resultado sin necesitar conocimientos previos
        explain_frame = tk.Frame(parent, bg=BG2, pady=10)
        explain_frame.pack(fill="x", padx=30, pady=(0, 10))
        # fill="x" = ocupa todo el ancho disponible
        # padx=30 = margen de 30px a cada lado

        # Pregunta en negrita
        tk.Label(
            explain_frame,
            text="¿Qué es un grafo bipartito?",
            font=("Courier New", 11, "bold"),
            fg=ACCENT,
            bg=BG2
        ).pack(anchor="w", padx=14, pady=(6, 2))
        # anchor="w" = alinear a la izquierda (west)

        # Explicación del concepto y del algoritmo usado
        tk.Label(
            explain_frame,
            text=(
                "Un grafo es bipartito si se puede dividir en dos grupos (A y B)\n"
                "de forma que NINGUNA arista conecte dos aeropuertos del mismo grupo.\n"
                "Algoritmo: BFS 2-coloring — si dos vecinos tienen el mismo color, NO es bipartito."
            ),
            font=("Courier New", 10),
            fg="#aaaaaa",      # Gris claro (texto secundario)
            bg=BG2,
            justify="left"     # Alinear texto a la izquierda
        ).pack(anchor="w", padx=14, pady=(0, 6))

        # ── BOTÓN PARA EJECUTAR LA VERIFICACIÓN ──────────────────────────
        tk.Button(
            parent,
            text="Verificar Bipartitividad",
            font=FONT_MONO,
            bg=ACCENT,
            fg="#0f1117",
            activebackground="#e1bee7",  # Color más claro al hacer clic
            relief="flat",
            padx=18,
            pady=8,
            cursor="hand2",
            command=self._run,   # Llamar a _run cuando se haga clic
        ).pack(pady=10)

        # ── ETIQUETA DE RESULTADO PRINCIPAL ──────────────────────────────
        # Mostrará "ES BIPARTITO" o "NO ES BIPARTITO" en grande
        self.result_lbl = tk.Label(
            parent,
            text="",                           # Vacía al inicio
            font=("Courier New", 13, "bold"),
            bg=BG
        )
        self.result_lbl.pack()

        # ── ETIQUETA DE DETALLE ───────────────────────────────────────────
        # Muestra una frase corta explicando el resultado
        # wraplength=900 = el texto se rompe en líneas si supera 900px de ancho
        self.detail_lbl = tk.Label(
            parent,
            text="",
            font=FONT_MONO,
            fg="#aaaaaa",
            bg=BG,
            wraplength=900,
            justify="center"
        )
        self.detail_lbl.pack(pady=8)

        # ── LÍNEA SEPARADORA VISUAL ───────────────────────────────────────
        # Una línea de guiones "─" para separar visualmente el resultado
        # de las cajas de estadísticas
        tk.Label(parent, text="─" * 100, fg="#333", bg=BG).pack()

        # ── CAJAS DE ESTADÍSTICAS ─────────────────────────────────────────
        # 4 cajas alineadas horizontalmente que muestran:
        # 1. Qué parte del grafo se analizó
        # 2. Si es o no bipartito
        # 3. Cuántos aeropuertos hay en el Grupo A
        # 4. Cuántos aeropuertos hay en el Grupo B

        # Frame contenedor horizontal para las 4 cajas
        stats_frame = tk.Frame(parent, bg=BG)
        stats_frame.pack(pady=16)

        # Crear cada caja usando el método auxiliar _make_box
        # Parámetros: (contenedor, título, valor_inicial, color_del_valor)
        self.box_scope  = self._make_box(stats_frame, "Componente analizada", "—", FG)
        self.box_result = self._make_box(stats_frame, "¿Es bipartito?",        "—", FG)
        self.box_a      = self._make_box(stats_frame, "Grupo A (color 0)",     "—", "#4fc3f7")  # Azul
        self.box_b      = self._make_box(stats_frame, "Grupo B (color 1)",     "—", "#ef9a9a")  # Rojo

        # Colocar las 4 cajas en fila horizontal
        for box in (self.box_scope, self.box_result, self.box_a, self.box_b):
            box.pack(side="left", padx=14)  # side="left" = alinear de izquierda a derecha

        # ── ETIQUETA DE EXPLICACIÓN DEL RESULTADO ────────────────────────
        # Aparece solo cuando NO es bipartito, explicando por qué
        # con un ejemplo real de aeropuertos (triángulo ORD↔DFW↔LAX)
        self.explain_result = tk.Label(
            parent,
            text="",           # Vacía al inicio, se llena según el resultado
            font=("Courier New", 10),
            fg="#888",
            bg=BG,
            wraplength=900,    # Máximo 900px por línea antes de romper
            justify="center"
        )
        self.explain_result.pack(pady=(12, 0))


    # ------------------------------------------------------------------
    # MÉTODO _make_box — Crea una caja de estadística reutilizable
    # ------------------------------------------------------------------
    def _make_box(self, parent, title, value, color):
        """
        Crea una caja visual con título arriba y valor grande abajo.
        Se usa para mostrar estadísticas de forma clara y destacada.

        Ejemplo visual:
        ┌─────────────────────┐
        │  Componente analizada │  ← título pequeño gris
        │       3230 vértices   │  ← valor grande y colorido
        └─────────────────────┘

        Parámetros:
          parent : frame donde se coloca la caja
          title  : texto pequeño del encabezado (ej: "¿Es bipartito?")
          value  : valor inicial mostrado (ej: "—" o "N/A")
          color  : color del valor (verde, rojo, azul, etc.)

        Retorna:
          frame : el Frame de la caja, con dos atributos extra añadidos:
                  frame._lbl   = referencia a la etiqueta del valor (para actualizarla)
                  frame._color = color original del valor (para restaurarlo)
        """
        # Crear el rectángulo de la caja con fondo BG3 y padding interno
        frame = tk.Frame(parent, bg=BG3, padx=20, pady=12)

        # Título pequeño en gris (encabezado de la caja)
        tk.Label(
            frame,
            text=title,
            font=("Courier New", 9),
            fg="#888",   # Gris oscuro
            bg=BG3
        ).pack()

        # Valor grande y colorido (el dato principal de la caja)
        lbl = tk.Label(
            frame,
            text=value,
            font=("Courier New", 15, "bold"),
            fg=color,    # Color pasado como parámetro
            bg=BG3
        )
        lbl.pack()

        # Guardar referencias en el frame para poder actualizar el valor después
        # Esto es un truco de Python: agregamos atributos dinámicamente al objeto frame
        frame._lbl   = lbl    # Referencia a la etiqueta del valor
        frame._color = color  # Color original del valor

        return frame  # Retornar el frame completo para que quien lo llame lo coloque


    # ------------------------------------------------------------------
    # MÉTODO _run — Se activa cuando el usuario hace clic en el botón
    # ------------------------------------------------------------------
    def _run(self):
        """
        Prepara la interfaz para el análisis y lanza el cálculo
        en un hilo separado.

        Antes de lanzar el cálculo:
        1. Muestra "Calculando…" en el resultado principal
        2. Limpia las etiquetas de detalle y explicación
        3. Pone "…" en todas las cajas de estadísticas
        4. Lanza el algoritmo en un hilo secundario
        """
        # Indicar que el cálculo está en proceso
        self.result_lbl.config(text="Calculando…", fg=YELLOW)

        # Limpiar resultados anteriores
        self.detail_lbl.config(text="")
        self.explain_result.config(text="")

        # Resetear todas las cajas a "…" (cargando)
        for box in (self.box_scope, self.box_result, self.box_a, self.box_b):
            box._lbl.config(text="…")

        # Lanzar el cálculo en segundo plano para no congelar la interfaz
        threading.Thread(target=self._compute, daemon=True).start()


    # ------------------------------------------------------------------
    # MÉTODO _compute — Ejecuta el algoritmo (corre en hilo secundario)
    # ------------------------------------------------------------------
    def _compute(self):
        """
        Ejecuta el algoritmo BFS 2-coloring para verificar bipartitividad.
        Este método corre en un hilo separado, NO en el hilo principal.

        Pasos:
        1. Obtener todas las componentes conexas del grafo
        2. Ordenarlas por tamaño (mayor primero)
        3. Tomar la componente MÁS GRANDE para analizarla
           (si hay más de una componente, el enunciado pide analizar la mayor)
        4. Ejecutar BFS 2-coloring sobre esa componente
        5. Programar la actualización visual en el hilo principal
        """
        # Obtener todas las componentes conexas usando BFS
        components = self.graph.get_components()

        # Ordenar de mayor a menor cantidad de vértices
        components.sort(key=lambda c: len(c), reverse=True)

        # Cantidad total de componentes (para saber si el grafo es conexo o no)
        n_comp = len(components)

        # Tomar la componente más grande (índice 0 después de ordenar)
        # Si el grafo es conexo, esta es la única componente (el grafo completo)
        target = components[0]

        # Ejecutar BFS 2-coloring sobre la componente más grande
        # is_bip  = True si es bipartito, False si no
        # color   = diccionario {aeropuerto: 0 o 1} con el color asignado a cada uno
        is_bip, color = self.graph.is_bipartite_component(target)

        # Programar la actualización de la interfaz en el hilo principal
        # (no podemos modificar la interfaz directamente desde un hilo secundario)
        self.parent.after(0, lambda: self._show(is_bip, color, target, n_comp))


    # ------------------------------------------------------------------
    # MÉTODO _show — Actualiza la interfaz con los resultados
    # ------------------------------------------------------------------
    def _show(self, is_bip, color, target, n_comp):
        """
        Muestra los resultados del análisis en la interfaz.
        Este método corre en el hilo PRINCIPAL (llamado por after()).

        Parámetros:
          is_bip  : True si la componente es bipartita, False si no
          color   : diccionario {aeropuerto: 0 o 1} con los colores asignados
          target  : set de aeropuertos de la componente analizada
          n_comp  : número total de componentes del grafo
        """
        total = len(self.graph.airports)  # Total de aeropuertos en el grafo

        # ── ACTUALIZAR CAJA "COMPONENTE ANALIZADA" ────────────────────────
        # Mostrar qué parte del grafo se analizó
        scope = (
            "Grafo completo"          # Si solo hay 1 componente = grafo completo
            if n_comp == 1
            else f"{len(target)} vértices\n(de {total} totales)"  # Si hay varias
        )
        self.box_scope._lbl.config(text=scope, fg=ACCENT)

        # ── MOSTRAR RESULTADO SEGÚN SI ES BIPARTITO O NO ──────────────────
        if is_bip:
            # ── CASO: SÍ ES BIPARTITO ─────────────────────────────────────
            # Contar cuántos aeropuertos quedaron en cada grupo
            grp_a = sum(1 for v in color.values() if v == 0)  # Los de color 0 = Grupo A
            grp_b = sum(1 for v in color.values() if v == 1)  # Los de color 1 = Grupo B

            # Resultado principal en verde
            self.result_lbl.config(text="ES BIPARTITO", fg=GREEN)

            # Descripción del resultado
            self.detail_lbl.config(
                text="Los aeropuertos se pueden dividir en 2 grupos sin aristas entre nodos del mismo grupo.",
                fg=GREEN
            )

            # Actualizar cajas de estadísticas
            self.box_result._lbl.config(text="SÍ ✔", fg=GREEN)
            self.box_a._lbl.config(text=str(grp_a), fg="#4fc3f7")  # Azul con cantidad grupo A
            self.box_b._lbl.config(text=str(grp_b), fg="#ef9a9a")  # Rojo con cantidad grupo B

            # Limpiar la explicación (no hace falta cuando es bipartito)
            self.explain_result.config(text="", fg="#888")

        else:
            # ── CASO: NO ES BIPARTITO ─────────────────────────────────────
            # Resultado principal en rojo
            self.result_lbl.config(text="NO ES BIPARTITO", fg=RED)

            # Explicar por qué falló el algoritmo
            self.detail_lbl.config(
                text="Se encontró un ciclo de longitud IMPAR durante el BFS 2-coloring.",
                fg=RED
            )

            # Actualizar cajas de estadísticas
            self.box_result._lbl.config(text="NO ✘", fg=RED)
            # Los grupos A y B no aplican cuando no es bipartito
            self.box_a._lbl.config(text="N/A", fg="#555")
            self.box_b._lbl.config(text="N/A", fg="#555")

            # Mostrar explicación detallada de por qué NO es bipartito
            # con un ejemplo real de aeropuertos que forman un triángulo
            self.explain_result.config(
                text=(
                    "¿Por qué NO es bipartito?\n"
                    "En redes aéreas reales los hubs se conectan entre sí directamente.\n"
                    "Ejemplo: ORD ↔ DFW ↔ LAX ↔ ORD forma un triángulo (ciclo de 3 aristas = impar).\n"
                    "Cualquier ciclo de longitud impar hace que el grafo NO sea bipartito."
                ),
                fg="#888"
            )