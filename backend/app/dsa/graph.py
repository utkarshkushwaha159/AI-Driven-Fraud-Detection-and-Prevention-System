"""
Graph data structures and algorithms for fraud network analysis.
Implements adjacency list representation with various graph algorithms.
"""
from collections import defaultdict, deque
import heapq
import math


class Graph:
    """Adjacency list graph implementation for network analysis."""

    def __init__(self, directed=False):
        self.adj_list = defaultdict(list)  # node -> [(neighbor, weight, edge_data)]
        self.nodes = {}  # node_id -> node_data
        self.directed = directed

    def add_node(self, node_id, data=None):
        """Add a node to the graph."""
        self.nodes[node_id] = data or {}
        if node_id not in self.adj_list:
            self.adj_list[node_id] = []

    def add_edge(self, u, v, weight=1.0, data=None):
        """Add an edge between nodes u and v."""
        if u not in self.nodes:
            self.add_node(u)
        if v not in self.nodes:
            self.add_node(v)

        self.adj_list[u].append((v, weight, data or {}))
        if not self.directed:
            self.adj_list[v].append((u, weight, data or {}))

    def get_neighbors(self, node_id):
        """Get all neighbors of a node."""
        return [(n, w, d) for n, w, d in self.adj_list.get(node_id, [])]

    def get_nodes(self):
        """Get all nodes."""
        return list(self.nodes.keys())

    def get_edges(self):
        """Get all edges as (u, v, weight, data) tuples."""
        edges = []
        seen = set()
        for u in self.adj_list:
            for v, w, d in self.adj_list[u]:
                edge_key = (min(u, v), max(u, v)) if not self.directed else (u, v)
                if edge_key not in seen:
                    edges.append((u, v, w, d))
                    seen.add(edge_key)
        return edges

    def node_count(self):
        return len(self.nodes)

    def edge_count(self):
        return len(self.get_edges())

    # --- BFS ---
    def bfs(self, start):
        """Breadth-first search from start node. Returns visited order and parent map."""
        visited = set()
        order = []
        parent = {}
        queue = deque([start])
        visited.add(start)
        parent[start] = None

        while queue:
            node = queue.popleft()
            order.append(node)
            for neighbor, weight, data in self.adj_list.get(node, []):
                if neighbor not in visited:
                    visited.add(neighbor)
                    parent[neighbor] = node
                    queue.append(neighbor)

        return order, parent

    # --- DFS ---
    def dfs(self, start):
        """Depth-first search from start node. Returns visited order."""
        visited = set()
        order = []
        self._dfs_helper(start, visited, order)
        return order

    def _dfs_helper(self, node, visited, order):
        visited.add(node)
        order.append(node)
        for neighbor, weight, data in self.adj_list.get(node, []):
            if neighbor not in visited:
                self._dfs_helper(neighbor, visited, order)

    # --- Connected Components ---
    def connected_components(self):
        """Find all connected components. Returns list of sets."""
        visited = set()
        components = []

        for node in self.nodes:
            if node not in visited:
                component = set()
                queue = deque([node])
                visited.add(node)
                while queue:
                    current = queue.popleft()
                    component.add(current)
                    for neighbor, w, d in self.adj_list.get(current, []):
                        if neighbor not in visited:
                            visited.add(neighbor)
                            queue.append(neighbor)
                components.append(component)

        return components

    # --- Dijkstra ---
    def dijkstra(self, start):
        """Dijkstra's shortest path algorithm. Returns distances and predecessors."""
        distances = {node: float("inf") for node in self.nodes}
        predecessors = {node: None for node in self.nodes}
        distances[start] = 0
        pq = [(0, start)]

        while pq:
            dist, node = heapq.heappop(pq)
            if dist > distances[node]:
                continue
            for neighbor, weight, data in self.adj_list.get(node, []):
                new_dist = dist + weight
                if new_dist < distances.get(neighbor, float("inf")):
                    distances[neighbor] = new_dist
                    predecessors[neighbor] = node
                    heapq.heappush(pq, (new_dist, neighbor))

        return distances, predecessors

    def shortest_path(self, start, end):
        """Find shortest path between two nodes using Dijkstra."""
        distances, predecessors = self.dijkstra(start)
        if distances.get(end, float("inf")) == float("inf"):
            return None, float("inf")

        path = []
        current = end
        while current is not None:
            path.append(current)
            current = predecessors.get(current)
        path.reverse()
        return path, distances[end]

    # --- Bellman-Ford ---
    def bellman_ford(self, start):
        """Bellman-Ford shortest paths (handles negative weights)."""
        distances = {node: float("inf") for node in self.nodes}
        predecessors = {node: None for node in self.nodes}
        distances[start] = 0
        edges = self.get_edges()

        for _ in range(len(self.nodes) - 1):
            for u, v, w, d in edges:
                if distances[u] + w < distances[v]:
                    distances[v] = distances[u] + w
                    predecessors[v] = u
                if not self.directed and distances[v] + w < distances[u]:
                    distances[u] = distances[v] + w
                    predecessors[u] = v

        return distances, predecessors

    # --- Floyd-Warshall ---
    def floyd_warshall(self):
        """All-pairs shortest paths."""
        nodes = list(self.nodes.keys())
        n = len(nodes)
        node_idx = {node: i for i, node in enumerate(nodes)}

        dist = [[float("inf")] * n for _ in range(n)]
        for i in range(n):
            dist[i][i] = 0

        for u in self.adj_list:
            for v, w, d in self.adj_list[u]:
                i, j = node_idx[u], node_idx[v]
                dist[i][j] = min(dist[i][j], w)

        for k in range(n):
            for i in range(n):
                for j in range(n):
                    if dist[i][k] + dist[k][j] < dist[i][j]:
                        dist[i][j] = dist[i][k] + dist[k][j]

        return dist, nodes

    # --- Transitive Closure ---
    def transitive_closure(self):
        """Compute transitive closure (reachability matrix)."""
        nodes = list(self.nodes.keys())
        n = len(nodes)
        node_idx = {node: i for i, node in enumerate(nodes)}

        reach = [[False] * n for _ in range(n)]
        for i in range(n):
            reach[i][i] = True

        for u in self.adj_list:
            for v, w, d in self.adj_list[u]:
                reach[node_idx[u]][node_idx[v]] = True

        for k in range(n):
            for i in range(n):
                for j in range(n):
                    reach[i][j] = reach[i][j] or (reach[i][k] and reach[k][j])

        return reach, nodes

    # --- Prim's MST ---
    def prim_mst(self):
        """Prim's minimum spanning tree algorithm."""
        if not self.nodes:
            return [], 0

        start = next(iter(self.nodes))
        visited = {start}
        edges = []
        total_weight = 0

        candidates = [(w, start, v, d) for v, w, d in self.adj_list.get(start, [])]
        heapq.heapify(candidates)

        while candidates and len(visited) < len(self.nodes):
            weight, u, v, data = heapq.heappop(candidates)
            if v in visited:
                continue
            visited.add(v)
            edges.append((u, v, weight))
            total_weight += weight

            for neighbor, w, d in self.adj_list.get(v, []):
                if neighbor not in visited:
                    heapq.heappush(candidates, (w, v, neighbor, d))

        return edges, total_weight

    # --- Kruskal's MST ---
    def kruskal_mst(self):
        """Kruskal's minimum spanning tree using Union-Find."""
        parent = {node: node for node in self.nodes}
        rank = {node: 0 for node in self.nodes}

        def find(x):
            if parent[x] != x:
                parent[x] = find(parent[x])
            return parent[x]

        def union(x, y):
            rx, ry = find(x), find(y)
            if rx == ry:
                return False
            if rank[rx] < rank[ry]:
                rx, ry = ry, rx
            parent[ry] = rx
            if rank[rx] == rank[ry]:
                rank[rx] += 1
            return True

        edges = sorted(self.get_edges(), key=lambda e: e[2])
        mst = []
        total_weight = 0

        for u, v, w, d in edges:
            if union(u, v):
                mst.append((u, v, w))
                total_weight += w

        return mst, total_weight

    # --- Subgraph extraction ---
    def get_subgraph(self, center_node, max_depth=2):
        """Extract a subgraph around a center node up to max_depth hops."""
        visited = set()
        queue = deque([(center_node, 0)])
        visited.add(center_node)
        sub_nodes = set()
        sub_edges = []

        while queue:
            node, depth = queue.popleft()
            sub_nodes.add(node)
            if depth >= max_depth:
                continue
            for neighbor, weight, data in self.adj_list.get(node, []):
                sub_edges.append((node, neighbor, weight, data))
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, depth + 1))

        subgraph = Graph(self.directed)
        for node in sub_nodes:
            subgraph.add_node(node, self.nodes.get(node, {}))
        for u, v, w, d in sub_edges:
            if u in sub_nodes and v in sub_nodes:
                subgraph.add_edge(u, v, w, d)

        return subgraph

    def degree(self, node_id):
        """Get degree of a node."""
        return len(self.adj_list.get(node_id, []))

    def to_adjacency_matrix(self):
        """Convert to adjacency matrix representation."""
        nodes = list(self.nodes.keys())
        n = len(nodes)
        node_idx = {node: i for i, node in enumerate(nodes)}
        matrix = [[0] * n for _ in range(n)]
        for u in self.adj_list:
            for v, w, d in self.adj_list[u]:
                matrix[node_idx[u]][node_idx[v]] = w
        return matrix, nodes
