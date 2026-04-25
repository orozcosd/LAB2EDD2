# Laboratorio 2 — Estructura de Datos II
## Universidad del Norte — Grafo de Rutas Aéreas

### Descripción
Aplicación de escritorio en Python que construye un grafo **simple, no dirigido y ponderado**
de rutas aéreas mundiales a partir del dataset `flights_final.csv` (66 930 registros).

El peso de cada arista es la **distancia Haversine** (km) entre los aeropuertos conectados.

---

### Estructura del proyecto

```
lab2/
├── main.py          # Punto de entrada, ventana principal y pestañas
├── graph.py         # Grafo y todos los algoritmos (sin librerías externas)
├── ui_tab1.py       # Pestaña 1: Conectividad (BFS)
├── ui_tab2.py       # Pestaña 2: Bipartitividad (BFS 2-coloring)
├── ui_tab3.py       # Pestaña 3: Árbol de Expansión Mínima (Kruskal + Union-Find)
├── ui_tab4.py       # Pestaña 4: Caminos mínimos (Dijkstra)
├── ui_tab5.py       # Pestaña 5: Mapa interactivo (tkintermapview)
├── flights_final.csv
└── requirements.txt
```

---

### Instalación

```bash
pip install tkintermapview
```

### Ejecución

```bash
python main.py
```

---

### Funcionalidades

| Pestaña | Funcionalidad | Algoritmo |
|---------|--------------|-----------|
| 1 — Conectividad | ¿Es el grafo conexo? Número y tamaño de componentes | BFS manual |
| 2 — Bipartito | ¿Es bipartito? (o la componente más grande) | BFS 2-coloring |
| 3 — MST | Peso del árbol de expansión mínima por componente | Kruskal + Union-Find |
| 4 — Caminos mínimos | Top-10 caminos más largos desde un origen | Dijkstra manual |
| 5 — Mapa | Geolocalización de aeropuertos + ruta sobre el mapa | Dijkstra + tkintermapview |

---

### Restricciones cumplidas
- ✅ **Sin librerías externas** para conectividad, bipartitividad, MST ni caminos mínimos.
- ✅ Todos los algoritmos implementados manualmente en `graph.py`.
- ✅ Distancia entre coordenadas: fórmula **Haversine** implementada desde cero.
- ✅ Código documentado con docstrings y comentarios en cada módulo.

---

### Dataset
- **Archivo:** `flights_final.csv`
- **Registros:** 66 930 vuelos
- **Vértices generados:** 3 256 aeropuertos
- **Aristas únicas:** 18 929 rutas
- **Componentes conexas:** 7 (componente principal con 3 230 aeropuertos)
