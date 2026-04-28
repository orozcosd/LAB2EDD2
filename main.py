"""
LABORATORIO 2 - Estructura de Datos II
Universidad del Norte
Grafo de rutas aéreas mundiales
Sección documentada por Santiago Orozco

Este archivo es el PUNTO DE ENTRADA del programa. Es el primero que
se ejecuta y su trabajo es:
1. Crear la ventana principal de la aplicación
2. Cargar el dataset de vuelos en segundo plano
3. Organizar las 5 pestañas de la interfaz gráfica
4. Conectar todo para que funcione junto
"""

# tkinter es la librería de Python para crear interfaces gráficas (ventanas, botones, etc.)
import tkinter as tk
from tkinter import ttk, messagebox  # ttk = widgets con mejor apariencia, messagebox = ventanas de error

# threading permite ejecutar tareas en paralelo para no congelar la interfaz
# mientras se carga el dataset (que pesa bastante con 66,930 registros)
import threading

# os permite trabajar con rutas de archivos del sistema operativo
import os

# Importar el grafo y las 5 pestañas que están en archivos separados
from graph import AirportGraph       # El cerebro: grafo + algoritmos
from ui_tab1 import Tab1Conectividad # Pestaña 1: ¿Es conexo el grafo?
from ui_tab2 import Tab2Bipartito    # Pestaña 2: ¿Es bipartito el grafo?
from ui_tab3 import Tab3MST          # Pestaña 3: Árbol de Expansión Mínima
from ui_tab4 import Tab4CaminosMinimos  # Pestaña 4: Dijkstra
from ui_tab5 import Tab5Mapa         # Pestaña 5: Mapa interactivo


# ===========================================================================
# CLASE APP — La ventana principal del programa
# ===========================================================================
class App(tk.Tk):
    """
    Esta clase representa la ventana principal de toda la aplicación.

    Hereda de tk.Tk, que es la clase base de tkinter para crear
    una ventana de escritorio. Al heredar de ella, nuestra App
    ES una ventana con todas sus funcionalidades.

    Responsabilidades:
    - Crear y configurar la ventana principal
    - Construir el banner superior y las pestañas
    - Cargar el grafo en segundo plano (sin congelar la pantalla)
    - Distribuir el grafo a cada pestaña cuando esté listo
    """

    def __init__(self):
        """
        Constructor: se ejecuta automáticamente al crear la aplicación.
        Aquí se configura todo lo inicial antes de mostrar nada al usuario.
        """
        # Inicializar la ventana base de tkinter
        super().__init__()

        # --- Configuración básica de la ventana ---
        self.title("Laboratorio 2 - Grafo de Rutas Aéreas")  # Título en la barra superior
        self.geometry("1280x800")        # Tamaño inicial: 1280 píxeles de ancho x 800 de alto
        self.configure(bg="#0f1117")     # Color de fondo: azul muy oscuro casi negro
        self.resizable(True, True)       # Permitir redimensionar la ventana (ancho y alto)

        # --- Variables compartidas entre pestañas ---
        # El grafo se carga después, por eso empieza como None
        self.graph = None

        # StringVar son variables especiales de tkinter que se pueden
        # compartir entre diferentes widgets y se actualizan automáticamente.
        # Aquí guardan los códigos IATA del aeropuerto origen y destino
        # seleccionados por el usuario (ej: "JFK", "BOG")
        self.selected_source = tk.StringVar()  # Aeropuerto de origen
        self.selected_dest = tk.StringVar()    # Aeropuerto de destino

        # --- Construir la interfaz visual ---
        self._build_ui()

        # --- Cargar el dataset en segundo plano ---
        # daemon=True significa que este hilo muere automáticamente
        # cuando se cierra la ventana principal (no bloquea el cierre)
        threading.Thread(target=self._load_graph, daemon=True).start()


    # ------------------------------------------------------------------
    # MÉTODO _build_ui — Construye toda la interfaz visual
    # ------------------------------------------------------------------
    def _build_ui(self):
        """
        Crea y organiza todos los elementos visuales de la ventana:
        el banner superior y el sistema de pestañas.

        Este método se llama UNA SOLA VEZ al iniciar la aplicación.
        Los contenidos de las pestañas se llenan después, cuando
        el grafo termina de cargarse.
        """

        # ── BANNER SUPERIOR ──────────────────────────────────────────────
        # Un rectángulo oscuro en la parte superior con el título del programa
        banner = tk.Frame(self, bg="#151822", height=56)
        banner.pack(fill="x")          # fill="x" = ocupa todo el ancho
        banner.pack_propagate(False)   # Fijar la altura en 56px (no se estira)

        # Título a la izquierda del banner
        tk.Label(
            banner,
            text="✈  Airport Graph Explorer",
            font=("Courier New", 18, "bold"),
            fg="#4fc3f7",    # Color azul claro
            bg="#151822"     # Mismo fondo que el banner
        ).pack(side="left", padx=20, pady=12)

        # Indicador de estado a la derecha del banner
        # Muestra "Cargando…" al inicio y luego la cantidad de aeropuertos/aristas
        self.status_lbl = tk.Label(
            banner,
            text="⏳ Cargando dataset…",
            font=("Courier New", 11),
            fg="#ffd54f",    # Color amarillo (indica proceso en curso)
            bg="#151822"
        )
        self.status_lbl.pack(side="right", padx=20)

        # ── SISTEMA DE PESTAÑAS (NOTEBOOK) ───────────────────────────────
        # El Notebook es el widget que permite tener múltiples pestañas
        # como las de un navegador web

        # Configurar el estilo visual de las pestañas
        style = ttk.Style()
        style.theme_use("default")  # Tema base que podemos personalizar

        # Estilo del contenedor de pestañas
        style.configure("TNotebook",
                        background="#0f1117",  # Fondo oscuro
                        borderwidth=0)          # Sin borde

        # Estilo de cada pestaña individual
        style.configure("TNotebook.Tab",
                        background="#1e2130",       # Fondo gris oscuro (inactiva)
                        foreground="#aaaaaa",        # Texto gris (inactiva)
                        padding=[14, 7],             # Espaciado interno
                        font=("Courier New", 10, "bold"))

        # Estilo cuando una pestaña está SELECCIONADA (activa)
        style.map("TNotebook.Tab",
                  background=[("selected", "#4fc3f7")],  # Fondo azul claro
                  foreground=[("selected", "#0f1117")])   # Texto oscuro

        # Crear el widget Notebook (el contenedor de pestañas)
        self.nb = ttk.Notebook(self)
        self.nb.pack(fill="both", expand=True, padx=8, pady=8)
        # fill="both" + expand=True = ocupa todo el espacio disponible

        # ── CREAR LAS 5 PESTAÑAS ─────────────────────────────────────────
        # Cada pestaña es un Frame (rectángulo vacío) que luego se llenará
        # con los widgets correspondientes cuando el grafo esté listo

        self.tab_frames = {}  # Diccionario para acceder a cada frame por nombre

        tabs_info = [
            ("tab1", "1. Conectividad"),
            ("tab2", "2. Bipartito"),
            ("tab3", "3. Árbol Expansión Mínima"),
            ("tab4", "4. Caminos Mínimos"),
            ("tab5", "5. Mapa Interactivo"),
        ]

        for key, label in tabs_info:
            # Crear un frame vacío con fondo oscuro
            f = tk.Frame(self.nb, bg="#0f1117")
            # Agregar ese frame como una pestaña con su etiqueta
            self.nb.add(f, text=label)
            # Guardar referencia para usarlo después
            self.tab_frames[key] = f

        # Mientras carga el dataset, mostrar mensaje de espera en cada pestaña
        self._show_loading_placeholders()


    # ------------------------------------------------------------------
    # MÉTODO _show_loading_placeholders — Mensaje de carga temporal
    # ------------------------------------------------------------------
    def _show_loading_placeholders(self):
        """
        Muestra un mensaje de "Cargando…" en cada pestaña mientras
        el dataset se está procesando en segundo plano.

        Esto es importante para que el usuario sepa que el programa
        está trabajando y no se confunda pensando que se congeló.
        """
        for frame in self.tab_frames.values():
            tk.Label(
                frame,
                text="Cargando datos del dataset…\nEspera un momento.",
                font=("Courier New", 14),
                fg="#4fc3f7",   # Texto azul claro
                bg="#0f1117"    # Fondo oscuro
            ).pack(expand=True)  # Centrar el texto en el frame


    # ------------------------------------------------------------------
    # MÉTODO _load_graph — Carga el grafo en segundo plano
    # ------------------------------------------------------------------
    def _load_graph(self):
        """
        Este método se ejecuta en un HILO SEPARADO (thread) para no
        congelar la interfaz mientras procesa los 66,930 registros del CSV.

        ¿Por qué en un hilo separado?
        Si cargáramos el grafo en el hilo principal (el mismo que maneja
        la interfaz), la ventana se congelaría completamente y el usuario
        no podría hacer nada hasta que terminara. Con threading, la interfaz
        sigue respondiendo mientras el grafo se construye en paralelo.

        Pasos:
        1. Encontrar el archivo CSV en la misma carpeta que este script
        2. Crear el grafo y construirlo desde el CSV
        3. Cuando termine, notificar a la interfaz (con self.after)
        """
        # Construir la ruta completa al archivo CSV
        # __file__ = ruta de este script (main.py)
        # os.path.dirname = carpeta donde está el script
        # os.path.join = combinar carpeta + nombre de archivo
        csv_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "flights_final.csv"
        )

        try:
            # Crear el objeto grafo con la ruta del CSV
            g = AirportGraph(csv_path)

            # Leer el CSV y construir toda la estructura del grafo
            # (aeropuertos, aristas, distancias) — esto tarda unos segundos
            g.build()

            # Guardar el grafo construido en la variable de la App
            self.graph = g

            # IMPORTANTE: No podemos modificar la interfaz desde un hilo secundario.
            # self.after(0, función) programa la función para ejecutarse en el
            # hilo principal de tkinter tan pronto como sea posible (0 milisegundos).
            self.after(0, self._on_graph_ready)

        except Exception as e:
            # Si algo falla (archivo no encontrado, datos corruptos, etc.)
            # mostrar un mensaje de error al usuario
            self.after(0, lambda: messagebox.showerror("Error al cargar datos", str(e)))


    # ------------------------------------------------------------------
    # MÉTODO _on_graph_ready — Se ejecuta cuando el grafo está listo
    # ------------------------------------------------------------------
    def _on_graph_ready(self):
        """
        Este método se ejecuta automáticamente cuando el grafo termina
        de construirse. Su trabajo es:
        1. Actualizar el indicador de estado con las estadísticas del grafo
        2. Limpiar los mensajes de "Cargando…" de cada pestaña
        3. Crear el contenido real de cada pestaña con el grafo ya disponible

        NOTA: Este método corre en el hilo principal de tkinter (gracias
        al self.after(0, ...) que lo programó), por lo que puede modificar
        la interfaz con seguridad.
        """
        # Actualizar el indicador de estado en el banner superior
        # Ahora muestra cuántos aeropuertos y aristas tiene el grafo
        self.status_lbl.config(
            text=f"✔  {len(self.graph.airports)} aeropuertos | {self.graph.edge_count()} aristas",
            fg="#a5d6a7"  # Verde claro = proceso completado exitosamente
        )

        # Limpiar los mensajes de "Cargando…" de cada pestaña
        for f in self.tab_frames.values():
            for w in f.winfo_children():  # winfo_children() = lista de widgets hijos
                w.destroy()               # destroy() = eliminar el widget de la pantalla

        # ── CREAR EL CONTENIDO REAL DE CADA PESTAÑA ──────────────────────
        # Ahora que el grafo está listo, construimos cada pestaña
        # pasándole el grafo para que pueda ejecutar sus algoritmos

        # Pestaña 1: Analizar conectividad del grafo (BFS)
        Tab1Conectividad(self.tab_frames["tab1"], self.graph)

        # Pestaña 2: Verificar si el grafo es bipartito (BFS 2-coloring)
        Tab2Bipartito(self.tab_frames["tab2"], self.graph)

        # Pestaña 3: Calcular el Árbol de Expansión Mínima (Kruskal)
        Tab3MST(self.tab_frames["tab3"], self.graph)

        # Pestaña 4: Caminos mínimos con Dijkstra
        # Recibe además las variables compartidas de origen/destino y
        # una función de callback para saltar al mapa cuando se pide una ruta
        self.tab4 = Tab4CaminosMinimos(
            self.tab_frames["tab4"],
            self.graph,
            self.selected_source,   # Variable compartida: código origen
            self.selected_dest,     # Variable compartida: código destino
            self._go_to_map,        # Función para cambiar a la pestaña del mapa
        )

        # Pestaña 5: Mapa interactivo
        # También recibe las variables compartidas para sincronizarse con la pestaña 4
        self.tab5 = Tab5Mapa(
            self.tab_frames["tab5"],
            self.graph,
            self.selected_source,   # Misma variable que usa Tab4
            self.selected_dest,     # Misma variable que usa Tab4
        )


    # ------------------------------------------------------------------
    # MÉTODO _go_to_map — Navegar a la pestaña del mapa
    # ------------------------------------------------------------------
    def _go_to_map(self):
        """
        Cambia la pestaña activa a la pestaña 5 (Mapa Interactivo).

        Este método se le pasa como función de callback a la pestaña 4.
        Cuando el usuario hace clic en "Ver ruta en mapa" desde Dijkstra,
        la pestaña 4 llama a esta función para saltar automáticamente al mapa.

        nb.select(4) selecciona la pestaña en el índice 4 (la 5ª pestaña,
        porque los índices empiezan en 0).
        """
        self.nb.select(4)  # Índice 4 = quinta pestaña = "5. Mapa Interactivo"


# ===========================================================================
# PUNTO DE ENTRADA DEL PROGRAMA
# ===========================================================================
if __name__ == "__main__":
    """
    Esta condición verifica que el script se está ejecutando directamente
    (no siendo importado por otro archivo).

    if __name__ == "__main__" es la forma estándar en Python de indicar
    el punto de inicio del programa.
    """
    # Crear la aplicación (esto llama a App.__init__ automáticamente)
    app = App()

    # mainloop() inicia el bucle principal de eventos de tkinter.
    # Este bucle:
    # - Mantiene la ventana abierta y visible
    # - Escucha eventos del usuario (clics, teclas, movimientos del mouse)
    # - Actualiza la interfaz cuando hay cambios
    # - Solo termina cuando el usuario cierra la ventana
    app.mainloop()