"""
graph.py
Documentado por Santiago Orozco
Módulo principal del grafo de aeropuertos.

Este archivo es el CEREBRO del programa. Aquí se construye el grafo
y se implementan todos los algoritmos desde cero, sin usar librerías externas.

¿Qué es un grafo? Es una estructura de datos que representa conexiones.
En este caso: los AEROPUERTOS son los vértices (puntos) y las RUTAS entre
ellos son las aristas (conexiones). Cada arista tiene un PESO que es la
distancia en kilómetros entre los dos aeropuertos.
"""

import math   # Para cálculos matemáticos (seno, coseno, raíz cuadrada)
import csv    # Para leer el archivo flights_final.csv
import heapq  # Para la cola de prioridad (min-heap) que usa Dijkstra


# ===========================================================================
# FUNCIÓN HAVERSINE
# Calcula la distancia real entre dos puntos en la superficie de la Tierra
# ===========================================================================
def haversine(lat1, lon1, lat2, lon2):
    """
    ¿Por qué no usamos distancia normal (euclidiana)?
    Porque la Tierra es ESFÉRICA, no plana. Si usáramos la fórmula normal
    de distancia entre dos puntos, el resultado sería incorrecto porque
    ignoraría la curvatura del planeta.

    La fórmula Haversine calcula la distancia más corta entre dos puntos
    sobre la superficie de una esfera (como volaría un avión en línea recta).

    Parámetros:
      lat1, lon1 : latitud y longitud del aeropuerto de origen (en grados)
      lat2, lon2 : latitud y longitud del aeropuerto de destino (en grados)

    Retorna:
      La distancia en kilómetros entre los dos aeropuertos.
    """
    R = 6371.0  # Radio de la Tierra en kilómetros (valor estándar)

    # Convertir los grados a radianes (los cálculos trigonométricos los necesitan así)
    phi1 = math.radians(lat1)   # latitud del origen en radianes
    phi2 = math.radians(lat2)   # latitud del destino en radianes
    dphi = math.radians(lat2 - lat1)  # diferencia de latitudes en radianes
    dlam = math.radians(lon2 - lon1)  # diferencia de longitudes en radianes

    # Fórmula Haversine: calcula el "cuadrado del seno de la mitad del ángulo"
    # Esta fórmula es especialmente precisa para distancias cortas y largas
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2

    # Multiplicar por el diámetro de la Tierra para obtener la distancia en km
    return R * 2 * math.asin(math.sqrt(a))


# ===========================================================================
# CLASE UNION-FIND
# Estructura auxiliar que usa el algoritmo de Kruskal para detectar ciclos
# ===========================================================================
class UnionFind:
    """
    ¿Qué hace Union-Find? Agrupa elementos y permite saber muy rápido
    si dos elementos pertenecen al mismo grupo.

    Imagínalo como familias: cada aeropuerto pertenece a una "familia".
    Cada familia tiene un REPRESENTANTE (el jefe). Para saber si dos
    aeropuertos están conectados, simplemente comparamos sus jefes.
    Si tienen el mismo jefe → ya están conectados → agregar la arista
    formaría un CICLO → la descartamos.

    Tiene dos optimizaciones importantes:
    1. Compresión de camino: hace que las búsquedas futuras sean más rápidas
    2. Unión por rango: evita que los grupos internos crezcan demasiado
    """

    def __init__(self, elements):
        """
        Inicializa la estructura. Al principio, cada elemento es
        su propio representante (cada aeropuerto es su propia familia).

        Ejemplo con 3 aeropuertos:
          parent = {JFK: JFK, LAX: LAX, BOG: BOG}
          rank   = {JFK: 0,   LAX: 0,   BOG: 0}
        """
        # parent[x] = representante (jefe) del grupo al que pertenece x
        self.parent = {e: e for e in elements}

        # rank[x] = "altura" aproximada del árbol interno del grupo de x
        # Se usa para decidir quién absorbe a quién al unir dos grupos
        self.rank = {e: 0 for e in elements}

    def find(self, x):
        """
        Encuentra y retorna el REPRESENTANTE (jefe) del grupo al que pertenece x.

        Usa COMPRESIÓN DE CAMINO: la primera vez que buscas el jefe de x,
        haces que x apunte directamente al jefe final, saltándose los intermedios.

        Sin compresión:  x → A → B → C → JEFE  (4 pasos)
        Con compresión:  x → JEFE               (1 paso, para siempre)

        Esto hace que las búsquedas futuras sean casi instantáneas.
        """
        if self.parent[x] != x:
            # x no es su propio jefe, entonces buscamos hacia arriba
            # y al mismo tiempo hacemos que x apunte directo al jefe final
            self.parent[x] = self.find(self.parent[x])  # ← aquí ocurre la compresión
        return self.parent[x]

    def union(self, x, y):
        """
        Une los grupos de x e y bajo un solo representante.

        Primero verifica si ya están en el mismo grupo (mismos jefes).
        Si ya están juntos → retorna False (agregar esta arista crearía un ciclo).
        Si son grupos distintos → los une y retorna True (arista válida para el MST).

        Usa UNIÓN POR RANGO: el grupo con mayor "altura" absorbe al de menor altura.
        Esto evita crear cadenas largas que harían las búsquedas lentas.
        """
        rx = self.find(x)  # jefe del grupo de x
        ry = self.find(y)  # jefe del grupo de y

        if rx == ry:
            # Mismo jefe = mismo grupo = esta arista formaría un CICLO
            return False

        # Unión por rango: el grupo más "alto" absorbe al más "bajo"
        if self.rank[rx] < self.rank[ry]:
            rx, ry = ry, rx  # intercambiar para que rx siempre sea el mayor

        self.parent[ry] = rx  # el jefe de ry ahora apunta al jefe rx

        # Si ambos tenían el mismo rango, el que absorbió crece un nivel
        if self.rank[rx] == self.rank[ry]:
            self.rank[rx] += 1

        return True  # unión exitosa, arista válida para el MST


# ===========================================================================
# CLASE AIRPORTGRAPH
# El grafo principal que contiene todos los aeropuertos y rutas
# ===========================================================================
class AirportGraph:
    """
    Representa el grafo completo de rutas aéreas mundiales.

    Tipo de grafo: SIMPLE, NO DIRIGIDO y PONDERADO.
    - Simple: no hay dos aristas iguales entre el mismo par de aeropuertos.
    - No dirigido: si hay ruta de A→B, también hay ruta de B→A.
    - Ponderado: cada ruta tiene un peso = distancia en km (calculada con Haversine).

    Estructura de datos usada: LISTA DE ADYACENCIA.
    ¿Por qué no matriz? Con 3256 aeropuertos, una matriz sería de
    3256×3256 = ~10 millones de celdas, la mayoría vacías. La lista
    solo guarda las conexiones que realmente existen, ahorrando memoria.

    Atributos principales:
      airports : diccionario  código → información del aeropuerto
      adj      : diccionario  código → lista de (vecino, distancia_km)
    """

    def __init__(self, csv_path):
        """
        Constructor. Recibe la ruta del archivo CSV y prepara las
        estructuras vacías que se llenarán cuando se llame a build().
        """
        self.csv_path = csv_path
        self.airports = {}  # Guarda la información de cada aeropuerto
        self.adj = {}       # Guarda las conexiones (lista de adyacencia)

    # ------------------------------------------------------------------
    # MÉTODO BUILD — Construye el grafo leyendo el CSV
    # ------------------------------------------------------------------
    def build(self):
        """
        Lee el archivo flights_final.csv línea por línea y construye el grafo.

        Por cada fila del CSV:
        1. Registra el aeropuerto origen (si no existe ya)
        2. Registra el aeropuerto destino (si no existe ya)
        3. Crea la arista entre ellos (si no existe ya) con peso = Haversine

        ¿Cómo evitamos aristas duplicadas?
        Como el grafo es NO DIRIGIDO, la ruta JFK→LAX y LAX→JFK son la misma.
        Usamos una clave ordenada lexicográficamente: (min, max).
        Ejemplo: tanto JFK→LAX como LAX→JFK generan la clave ('JFK','LAX').
        Si esa clave ya existe en edges_seen, la saltamos.
        """
        edges_seen = set()  # Conjunto para recordar qué aristas ya procesamos

        with open(self.csv_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)  # Lee el CSV como diccionario por columnas

            for row in reader:
                # Obtener los códigos IATA de origen y destino
                src = row["Source Airport Code"].strip()       # ej: "JFK"
                dst = row["Destination Airport Code"].strip()  # ej: "LAX"

                # --- Registrar aeropuerto ORIGEN si no existe ---
                if src not in self.airports:
                    self.airports[src] = {
                        "code":    src,
                        "name":    row["Source Airport Name"].strip(),
                        "city":    row["Source Airport City"].strip(),
                        "country": row["Source Airport Country"].strip(),
                        "lat":     float(row["Source Airport Latitude"]),
                        "lon":     float(row["Source Airport Longitude"]),
                    }

                # --- Registrar aeropuerto DESTINO si no existe ---
                if dst not in self.airports:
                    self.airports[dst] = {
                        "code":    dst,
                        "name":    row["Destination Airport Name"].strip(),
                        "city":    row["Destination Airport City"].strip(),
                        "country": row["Destination Airport Country"].strip(),
                        "lat":     float(row["Destination Airport Latitude"]),
                        "lon":     float(row["Destination Airport Longitude"]),
                    }

                # --- Crear la arista si no existe ya ---
                # Clave ordenada para evitar duplicados (JFK-LAX = LAX-JFK)
                key = (min(src, dst), max(src, dst))
                if key not in edges_seen:
                    edges_seen.add(key)

                    # Calcular la distancia real entre los dos aeropuertos
                    w = haversine(
                        self.airports[src]["lat"], self.airports[src]["lon"],
                        self.airports[dst]["lat"], self.airports[dst]["lon"],
                    )

                    # Agregar la conexión en AMBAS direcciones (grafo no dirigido)
                    self.adj.setdefault(src, []).append((dst, w))
                    self.adj.setdefault(dst, []).append((src, w))

        # Garantizar que todo aeropuerto tenga su entrada en adj,
        # aunque no tenga ninguna ruta (aeropuertos aislados)
        for code in self.airports:
            self.adj.setdefault(code, [])

    def edge_count(self):
        """
        Cuenta el número total de aristas únicas en el grafo.
        Como cada arista está guardada dos veces (A→B y B→A),
        dividimos entre 2 para obtener el número real de rutas.
        """
        total = sum(len(v) for v in self.adj.values())
        return total // 2  # dividir entre 2 porque cada arista aparece 2 veces


    # ------------------------------------------------------------------
    # ALGORITMO 1: CONECTIVIDAD — BFS
    # Pestaña 1 del programa
    # ------------------------------------------------------------------
    def get_components(self):
        """
        Encuentra todas las COMPONENTES CONEXAS del grafo usando BFS.

        ¿Qué es una componente conexa? Es un grupo de aeropuertos donde
        puedes llegar de cualquiera a cualquier otro siguiendo rutas.
        Si el grafo tuviera solo 1 componente, sería CONEXO (todos conectados).

        Algoritmo BFS (Búsqueda primero en anchura):
        - Empieza en un aeropuerto no visitado
        - Visita todos sus vecinos directos
        - Luego visita los vecinos de los vecinos
        - Así hasta agotar todos los aeropuertos alcanzables
        - Todo lo visitado forma UNA componente conexa
        - Repite con el siguiente aeropuerto no visitado

        Retorna: lista de sets, donde cada set es una componente conexa.
        Ejemplo: [{JFK, LAX, MIA, ...}, {aeropuerto_aislado}, ...]
        """
        visited = set()    # Aeropuertos ya visitados (para no repetir)
        components = []    # Lista donde guardaremos cada componente encontrada

        for start in self.airports:
            # Si este aeropuerto ya fue visitado, pertenece a una componente ya encontrada
            if start in visited:
                continue

            # --- BFS desde 'start' ---
            component = set()   # Aeropuertos de esta componente
            queue = [start]     # Cola de aeropuertos por visitar
            visited.add(start)  # Marcar como visitado antes de agregar a la cola

            while queue:
                node = queue.pop(0)   # Tomar el primer aeropuerto de la cola
                component.add(node)   # Agregar a esta componente

                # Revisar todos los vecinos (aeropuertos conectados directamente)
                for neighbor, _ in self.adj[node]:
                    if neighbor not in visited:
                        visited.add(neighbor)    # Marcar como visitado
                        queue.append(neighbor)   # Agregar a la cola para procesar

            components.append(component)  # Guardar esta componente completa

        return components

    def is_connected(self):
        """
        Retorna True si el grafo es conexo (tiene exactamente 1 componente).
        Retorna False si hay aeropuertos que no se pueden alcanzar desde otros.
        """
        return len(self.get_components()) == 1


    # ------------------------------------------------------------------
    # ALGORITMO 2: BIPARTITIVIDAD — BFS 2-coloring
    # Pestaña 2 del programa
    # ------------------------------------------------------------------
    def is_bipartite_component(self, nodes):
        """
        Verifica si un grupo de aeropuertos forma un grafo BIPARTITO.

        ¿Qué es un grafo bipartito? Es un grafo donde puedes pintar todos
        los vértices con 2 colores (A y B) de forma que ninguna arista
        conecte dos vértices del mismo color.

        Algoritmo BFS 2-coloring:
        - Asigna color 0 al aeropuerto inicial
        - Para cada vecino: asigna el color CONTRARIO (1 - color_actual)
        - Si encuentras un vecino que ya tiene el MISMO color que el nodo actual
          → hay un ciclo de longitud impar → NO es bipartito

        Parámetro:
          nodes : conjunto de códigos de aeropuertos a analizar

        Retorna:
          (True, colores)  si es bipartito
          (False, colores) si NO es bipartito (colores parciales hasta el conflicto)
        """
        color = {}  # Diccionario: código aeropuerto → color (0 o 1)

        # Empezar desde el primer aeropuerto del grupo
        start = next(iter(nodes))
        color[start] = 0   # Color inicial: 0 (grupo A)
        queue = [start]

        while queue:
            node = queue.pop(0)

            for neighbor, _ in self.adj[node]:
                # Solo analizar vecinos que pertenecen al grupo que nos pasaron
                if neighbor not in nodes:
                    continue

                if neighbor not in color:
                    # Vecino sin color: asignarle el color contrario
                    color[neighbor] = 1 - color[node]  # 0→1 o 1→0
                    queue.append(neighbor)

                elif color[neighbor] == color[node]:
                    # Vecino con el MISMO color → ciclo impar → NO bipartito
                    return False, color

        # Si llegamos aquí sin conflictos, el grafo SÍ es bipartito
        return True, color


    # ------------------------------------------------------------------
    # ALGORITMO 3: ÁRBOL DE EXPANSIÓN MÍNIMA — Kruskal con Union-Find
    # Pestaña 3 del programa
    # ------------------------------------------------------------------
    def kruskal_mst(self, nodes):
        """
        Calcula el ÁRBOL DE EXPANSIÓN MÍNIMA (MST) de un grupo de aeropuertos.

        ¿Qué es el MST? Es el conjunto de rutas que conecta TODOS los aeropuertos
        del grupo usando la MENOR distancia total posible, sin crear ciclos.
        Visualmente: es como tender cables entre todas las ciudades con el
        mínimo cable posible.

        Algoritmo de Kruskal:
        1. Recopilar todas las aristas del subgrafo
        2. Ordenarlas de MENOR a MAYOR peso (distancia)
        3. Ir agregando aristas una por una:
           - Si une dos grupos distintos → agregarla al MST (usando Union-Find)
           - Si une dos del mismo grupo → descartarla (formaría un ciclo)
        4. Parar cuando el MST tenga exactamente V-1 aristas (V = nº de vértices)

        Parámetro:
          nodes : conjunto de códigos de aeropuertos (una componente conexa)

        Retorna:
          (peso_total, lista_aristas)
          peso_total  : suma de distancias de todas las aristas del MST en km
          lista_aristas: lista de (aeropuerto1, aeropuerto2, distancia_km)
        """
        node_set = set(nodes)

        # --- Paso 1: Recopilar todas las aristas únicas del subgrafo ---
        edges = []   # Lista de (peso, origen, destino)
        seen = set() # Para no agregar la misma arista dos veces

        for u in node_set:
            for v, w in self.adj[u]:
                if v not in node_set:
                    continue  # Solo aristas dentro del grupo

                # Clave ordenada para evitar duplicados
                key = (min(u, v), max(u, v))
                if key not in seen:
                    seen.add(key)
                    edges.append((w, u, v))  # (peso, origen, destino)

        # --- Paso 2: Ordenar aristas de menor a mayor peso ---
        edges.sort()  # Python ordena por el primer elemento (el peso)

        # --- Paso 3: Aplicar Kruskal con Union-Find ---
        uf = UnionFind(node_set)  # Inicializar Union-Find con todos los aeropuertos
        mst_edges = []            # Aristas que formarán el MST
        total_weight = 0.0        # Peso total acumulado del MST

        for w, u, v in edges:
            # uf.union retorna True si u y v estaban en grupos distintos
            # (arista válida) y los une. Retorna False si ya estaban juntos
            # (formaría ciclo, se descarta).
            if uf.union(u, v):
                mst_edges.append((u, v, w))   # Agregar al MST
                total_weight += w             # Sumar al peso total

                # El MST está completo cuando tiene exactamente V-1 aristas
                if len(mst_edges) == len(node_set) - 1:
                    break  # Ya terminamos, no hace falta revisar más aristas

        return total_weight, mst_edges


    # ------------------------------------------------------------------
    # ALGORITMO 4: CAMINOS MÍNIMOS — Dijkstra
    # Pestaña 4 y 5 del programa
    # ------------------------------------------------------------------
    def dijkstra(self, source):
        """
        Calcula el camino más corto desde un aeropuerto origen hasta
        TODOS los demás aeropuertos del grafo.

        ¿Cómo funciona Dijkstra?
        Imagina que tienes una lista de aeropuertos con su distancia
        tentativa desde el origen. Al principio todos están en ∞ excepto
        el origen que está en 0.

        En cada paso:
        1. Tomar el aeropuerto con la MENOR distancia tentativa (usando min-heap)
        2. Revisar todos sus vecinos
        3. Si pasar por este aeropuerto da un camino más corto al vecino
           → actualizar la distancia del vecino (esto se llama RELAJAR la arista)
        4. Repetir hasta haber procesado todos los aeropuertos

        ¿Por qué usamos min-heap (heapq)?
        Para encontrar siempre el aeropuerto con menor distancia sin revisar
        todos. Sin heap sería O(V²), con heap es O(E log V) — mucho más rápido.

        Parámetro:
          source : código IATA del aeropuerto de origen (ej: "JFK")

        Retorna:
          dist : diccionario código → distancia mínima en km desde source
                 (math.inf si ese aeropuerto no es alcanzable desde source)
          prev : diccionario código → aeropuerto previo en el camino mínimo
                 (se usa para reconstruir el camino exacto después)
        """
        # Inicializar todas las distancias como infinito (desconocidas)
        dist = {node: math.inf for node in self.airports}
        # Inicializar todos los predecesores como None (sin camino conocido)
        prev = {node: None for node in self.airports}

        # La distancia del origen a sí mismo es 0
        dist[source] = 0.0

        # Min-heap: lista de (distancia, aeropuerto)
        # El heap siempre nos da el aeropuerto con menor distancia primero
        heap = [(0.0, source)]

        while heap:
            # Extraer el aeropuerto con la menor distancia conocida
            d, u = heapq.heappop(heap)

            # Si la distancia que guardamos en el heap ya está desactualizada,
            # ignorar esta entrada (el aeropuerto ya fue procesado con una
            # distancia mejor)
            if d > dist[u]:
                continue

            # Revisar todos los vecinos del aeropuerto actual
            for v, w in self.adj[u]:
                # Distancia alternativa: pasar por u para llegar a v
                alt = dist[u] + w

                # RELAJACIÓN: si encontramos un camino más corto a v
                if alt < dist[v]:
                    dist[v] = alt    # Actualizar la distancia mínima a v
                    prev[v] = u      # Recordar que llegamos a v desde u
                    # Agregar v al heap con su nueva distancia (más corta)
                    heapq.heappush(heap, (alt, v))

        return dist, prev

    def reconstruct_path(self, prev, source, target):
        """
        Reconstruye el camino mínimo desde source hasta target
        usando el diccionario 'prev' que generó Dijkstra.

        ¿Cómo funciona?
        Dijkstra guarda en 'prev' el aeropuerto anterior de cada uno en
        el camino más corto. Para reconstruir el camino, empezamos desde
        el DESTINO y vamos hacia atrás siguiendo los predecesores hasta
        llegar al ORIGEN.

        Ejemplo:
          prev = {LAX: JFK, MIA: LAX, BOG: MIA}
          Para ir de JFK a BOG:
          BOG → MIA → LAX → JFK  (al revés)
          Invertimos: JFK → LAX → MIA → BOG ✔

        Parámetros:
          prev   : diccionario generado por dijkstra()
          source : código del aeropuerto de origen
          target : código del aeropuerto de destino

        Retorna:
          Lista de códigos de aeropuertos desde source hasta target.
          Lista vacía [] si no existe camino entre source y target.
        """
        path = []
        node = target

        # Ir hacia atrás desde target siguiendo los predecesores
        while node is not None:
            path.append(node)
            node = prev[node]  # Moverse al aeropuerto anterior

        # El camino está al revés, invertirlo
        path.reverse()

        # Verificar que realmente llegamos al origen
        # (si no hay camino, path[0] no será source)
        if not path or path[0] != source:
            return []  # No hay camino entre source y target

        return path