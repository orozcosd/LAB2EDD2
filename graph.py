"""
graph.py
Módulo principal del grafo de aeropuertos.
Implementa:
  - Construcción del grafo desde el CSV
  - Cálculo de distancia Haversine (peso de aristas)
  - Conectividad (BFS/DFS manual)
  - Detección de grafo bipartito (BFS 2-coloring manual)
  - Árbol de expansión mínima (Kruskal manual con Union-Find)
  - Caminos mínimos (Dijkstra manual)
"""

import math
import csv
import heapq


# ---------------------------------------------------------------------------
# Distancia Haversine entre dos coordenadas geográficas (resultado en km)
# ---------------------------------------------------------------------------
def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0  # Radio de la Tierra en km
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return R * 2 * math.asin(math.sqrt(a))


# ---------------------------------------------------------------------------
# Union-Find (para Kruskal)
# ---------------------------------------------------------------------------
class UnionFind:
    def __init__(self, elements):
        self.parent = {e: e for e in elements}
        self.rank = {e: 0 for e in elements}

    def find(self, x):
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])  # compresión de camino
        return self.parent[x]

    def union(self, x, y):
        rx, ry = self.find(x), self.find(y)
        if rx == ry:
            return False
        if self.rank[rx] < self.rank[ry]:
            rx, ry = ry, rx
        self.parent[ry] = rx
        if self.rank[rx] == self.rank[ry]:
            self.rank[rx] += 1
        return True


# ---------------------------------------------------------------------------
# Grafo principal
# ---------------------------------------------------------------------------
class AirportGraph:
    """
    Grafo simple, no dirigido y ponderado de aeropuertos.

    Atributos:
      airports : dict  código -> {name, city, country, lat, lon}
      adj      : dict  código -> list[(vecino, peso)]
    """

    def __init__(self, csv_path):
        self.csv_path = csv_path
        self.airports = {}   # código -> info dict
        self.adj = {}        # lista de adyacencia

    # ------------------------------------------------------------------
    # Construcción del grafo
    # ------------------------------------------------------------------
    def build(self):
        """Lee el CSV y construye el grafo (aristas únicas, sin duplicados)."""
        edges_seen = set()

        with open(self.csv_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                src = row["Source Airport Code"].strip()
                dst = row["Destination Airport Code"].strip()

                # Registrar aeropuertos
                if src not in self.airports:
                    self.airports[src] = {
                        "code": src,
                        "name": row["Source Airport Name"].strip(),
                        "city": row["Source Airport City"].strip(),
                        "country": row["Source Airport Country"].strip(),
                        "lat": float(row["Source Airport Latitude"]),
                        "lon": float(row["Source Airport Longitude"]),
                    }
                if dst not in self.airports:
                    self.airports[dst] = {
                        "code": dst,
                        "name": row["Destination Airport Name"].strip(),
                        "city": row["Destination Airport City"].strip(),
                        "country": row["Destination Airport Country"].strip(),
                        "lat": float(row["Destination Airport Latitude"]),
                        "lon": float(row["Destination Airport Longitude"]),
                    }

                # Arista única (grafo no dirigido → guardamos en orden lexicográfico)
                key = (min(src, dst), max(src, dst))
                if key not in edges_seen:
                    edges_seen.add(key)
                    w = haversine(
                        self.airports[src]["lat"], self.airports[src]["lon"],
                        self.airports[dst]["lat"], self.airports[dst]["lon"],
                    )
                    self.adj.setdefault(src, []).append((dst, w))
                    self.adj.setdefault(dst, []).append((src, w))

        # Asegurar que todo aeropuerto tenga entrada en adj aunque sea vacía
        for code in self.airports:
            self.adj.setdefault(code, [])

    def edge_count(self):
        total = sum(len(v) for v in self.adj.values())
        return total // 2

    # ------------------------------------------------------------------
    # 1. CONECTIVIDAD — BFS para encontrar componentes conexas
    # ------------------------------------------------------------------
    def get_components(self):
        """
        Retorna una lista de sets, donde cada set contiene los códigos
        de aeropuertos que forman una componente conexa.
        """
        visited = set()
        components = []

        for start in self.airports:
            if start in visited:
                continue
            # BFS
            component = set()
            queue = [start]
            visited.add(start)
            while queue:
                node = queue.pop(0)
                component.add(node)
                for neighbor, _ in self.adj[node]:
                    if neighbor not in visited:
                        visited.add(neighbor)
                        queue.append(neighbor)
            components.append(component)

        return components

    def is_connected(self):
        return len(self.get_components()) == 1

    # ------------------------------------------------------------------
    # 2. BIPARTITO — BFS 2-coloring
    # ------------------------------------------------------------------
    def is_bipartite_component(self, nodes):
        """
        Verifica si el subgrafo inducido por `nodes` es bipartito
        usando coloreo BFS con 2 colores.
        Retorna (True/False, color_dict)
        """
        color = {}
        start = next(iter(nodes))
        color[start] = 0
        queue = [start]

        while queue:
            node = queue.pop(0)
            for neighbor, _ in self.adj[node]:
                if neighbor not in nodes:
                    continue
                if neighbor not in color:
                    color[neighbor] = 1 - color[node]
                    queue.append(neighbor)
                elif color[neighbor] == color[node]:
                    return False, color

        return True, color

    # ------------------------------------------------------------------
    # 3. ÁRBOL DE EXPANSIÓN MÍNIMA — Kruskal con Union-Find
    # ------------------------------------------------------------------
    def kruskal_mst(self, nodes):
        """
        Calcula el MST del subgrafo inducido por `nodes`.
        Retorna (peso_total, lista_de_aristas) donde cada arista es (u, v, w).
        """
        node_set = set(nodes)
        # Recopilar aristas únicas del subgrafo
        edges = []
        seen = set()
        for u in node_set:
            for v, w in self.adj[u]:
                if v not in node_set:
                    continue
                key = (min(u, v), max(u, v))
                if key not in seen:
                    seen.add(key)
                    edges.append((w, u, v))

        edges.sort()  # ordenar por peso

        uf = UnionFind(node_set)
        mst_edges = []
        total_weight = 0.0

        for w, u, v in edges:
            if uf.union(u, v):
                mst_edges.append((u, v, w))
                total_weight += w
                if len(mst_edges) == len(node_set) - 1:
                    break

        return total_weight, mst_edges

    # ------------------------------------------------------------------
    # 4. CAMINOS MÍNIMOS — Dijkstra manual
    # ------------------------------------------------------------------
    def dijkstra(self, source):
        """
        Calcula las distancias mínimas desde `source` a todos los vértices.
        Retorna (dist_dict, prev_dict).
        dist_dict: código -> distancia mínima (float, inf si inalcanzable)
        prev_dict: código -> nodo previo en el camino mínimo
        """
        dist = {node: math.inf for node in self.airports}
        prev = {node: None for node in self.airports}
        dist[source] = 0.0

        # Min-heap: (distancia, nodo)
        heap = [(0.0, source)]

        while heap:
            d, u = heapq.heappop(heap)
            if d > dist[u]:
                continue
            for v, w in self.adj[u]:
                alt = dist[u] + w
                if alt < dist[v]:
                    dist[v] = alt
                    prev[v] = u
                    heapq.heappush(heap, (alt, v))

        return dist, prev

    def reconstruct_path(self, prev, source, target):
        """Reconstruye el camino mínimo de source a target usando prev dict."""
        path = []
        node = target
        while node is not None:
            path.append(node)
            node = prev[node]
        path.reverse()
        if path[0] != source:
            return []  # no hay camino
        return path
