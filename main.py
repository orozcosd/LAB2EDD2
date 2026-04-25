"""
LABORATORIO 2 - Estructura de Datos II
Universidad del Norte
Grafo de rutas aéreas mundiales
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import os
from graph import AirportGraph
from ui_tab1 import Tab1Conectividad
from ui_tab2 import Tab2Bipartito
from ui_tab3 import Tab3MST
from ui_tab4 import Tab4CaminosMinimos
from ui_tab5 import Tab5Mapa


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Laboratorio 2 - Grafo de Rutas Aéreas")
        self.geometry("1280x800")
        self.configure(bg="#0f1117")
        self.resizable(True, True)

        self.graph = None
        self.selected_source = tk.StringVar()
        self.selected_dest = tk.StringVar()

        self._build_ui()
        threading.Thread(target=self._load_graph, daemon=True).start()

    def _build_ui(self):
        # Banner
        banner = tk.Frame(self, bg="#151822", height=56)
        banner.pack(fill="x")
        banner.pack_propagate(False)

        tk.Label(banner, text="✈  Airport Graph Explorer",
                 font=("Courier New", 18, "bold"),
                 fg="#4fc3f7", bg="#151822").pack(side="left", padx=20, pady=12)

        self.status_lbl = tk.Label(banner, text="⏳ Cargando dataset…",
                                   font=("Courier New", 11),
                                   fg="#ffd54f", bg="#151822")
        self.status_lbl.pack(side="right", padx=20)

        # Estilos del Notebook
        style = ttk.Style()
        style.theme_use("default")
        style.configure("TNotebook", background="#0f1117", borderwidth=0)
        style.configure("TNotebook.Tab", background="#1e2130", foreground="#aaaaaa",
                         padding=[14, 7], font=("Courier New", 10, "bold"))
        style.map("TNotebook.Tab",
                  background=[("selected", "#4fc3f7")],
                  foreground=[("selected", "#0f1117")])

        self.nb = ttk.Notebook(self)
        self.nb.pack(fill="both", expand=True, padx=8, pady=8)

        # Crear frames para cada pestaña
        self.tab_frames = {}
        tabs_info = [
            ("tab1", "1. Conectividad"),
            ("tab2", "2. Bipartito"),
            ("tab3", "3. Árbol Expansión Mínima"),
            ("tab4", "4. Caminos Mínimos"),
            ("tab5", "5. Mapa Interactivo"),
        ]
        for key, label in tabs_info:
            f = tk.Frame(self.nb, bg="#0f1117")
            self.nb.add(f, text=label)
            self.tab_frames[key] = f

        self._show_loading_placeholders()

    def _show_loading_placeholders(self):
        for frame in self.tab_frames.values():
            tk.Label(frame,
                     text="⏳  Cargando datos del dataset…\nEspera un momento.",
                     font=("Courier New", 14), fg="#4fc3f7", bg="#0f1117"
                     ).pack(expand=True)

    def _load_graph(self):
        # Buscar el CSV en la misma carpeta que este script
        csv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "flights_final.csv")
        try:
            g = AirportGraph(csv_path)
            g.build()
            self.graph = g
            self.after(0, self._on_graph_ready)
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Error al cargar datos", str(e)))

    def _on_graph_ready(self):
        self.status_lbl.config(
            text=f"✔  {len(self.graph.airports)} aeropuertos | {self.graph.edge_count()} aristas",
            fg="#a5d6a7")

        # Limpiar placeholders y crear las pestañas reales
        for f in self.tab_frames.values():
            for w in f.winfo_children():
                w.destroy()

        Tab1Conectividad(self.tab_frames["tab1"], self.graph)
        Tab2Bipartito(self.tab_frames["tab2"], self.graph)
        Tab3MST(self.tab_frames["tab3"], self.graph)

        self.tab4 = Tab4CaminosMinimos(
            self.tab_frames["tab4"],
            self.graph,
            self.selected_source,
            self.selected_dest,
            self._go_to_map,
        )
        self.tab5 = Tab5Mapa(
            self.tab_frames["tab5"],
            self.graph,
            self.selected_source,
            self.selected_dest,
        )

    def _go_to_map(self):
        self.nb.select(4)


if __name__ == "__main__":
    app = App()
    app.mainloop()
