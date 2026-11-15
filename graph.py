from heapq import heappush, heappop
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Hashable, Any, Callable, TYPE_CHECKING

if TYPE_CHECKING:
	import matplotlib.pyplot as plt

EdgeCheck = Callable[[Hashable | None, Hashable, Hashable], bool]

@dataclass
class Graph:
	directed: bool = False
	# "A": {"pos": (0.0, 0.0), "clos": Clos},
	nodes: dict[Hashable, dict[str, Any]] = field(default_factory=dict)
	# "A": {"B": {"weight": 5}, "D": {"weight": 1}}
	adj: dict[Hashable, dict[Hashable, dict[str, Any]]] = field(default_factory=lambda: defaultdict(dict))

	def __init__(self, directed: bool = False, node_map: dict | None = None):
		self.directed = directed
		self.nodes = {}
		self.adj = defaultdict(dict)

		if node_map is not None:
			self._from_node_map(node_map)

	def _from_node_map(self, node_map):
		for u, meta in node_map.items():
			# vs, pos, clos = meta
			vs, pos = meta
			self.add_node(u, pos=pos)
			for v, w in vs.items():
				self.add_edge(u, v, weight=w)

	def get_map(self):
		return self.adj

	def add_node(self, u: Hashable, **attrs):
		self.nodes.setdefault(u, {}).update(attrs)

	def add_edge(self, u: Hashable, v: Hashable, **attrs):
		self.add_node(u)
		self.add_node(v)
		if "weight" not in attrs and "weight" not in self.adj[u].get(v, {}):
			attrs["weight"] = 1
		self.adj[u][v] = {**self.adj[u].get(v, {}), **attrs}
		if not self.directed:
			self.adj[v][u] = {**self.adj[v].get(u, {}), **attrs}

	def neighbors(self, u: Hashable, reverse: bool = False, key: Callable | None = None): 
		if key is not None:
			return sorted(self.adj[u].keys(), reverse=reverse, key=key)
		return sorted(self.adj[u].keys(), reverse=reverse)

	def edges(self):
		edges = []
		for u, vs in self.adj.items():
			for v, data in vs.items():
				edges.append([u, v, data.get('weight', 1)])
		return edges

	def draw_graph(
		self,
		*,
		ax: "plt.Axes | None" = None,
		node_radius: float = 0.05,
		node_face="white",
		node_edge="black",
		edge_color="0.2",
		label_color="0.1",
		highlight_tree_edges: list[tuple[Hashable, Hashable]] | None = None,
		node_colors_from_table: dict | None = None,
		curved_edges: dict[tuple[Hashable, Hashable], float] | None = None,  # (u,v)->rad
		figsize=(7, 5),
		title: str | None = None,
		show: bool = False
	):
		import numpy as np
		import matplotlib.pyplot as plt
		from matplotlib.patches import FancyArrowPatch

		if ax is None:
			fig, ax = plt.subplots(figsize=figsize)
		else:
			fig = ax.figure

		# collect positions
		pos = {}
		for u, attrs in self.nodes.items():
			if "pos" not in attrs:
				raise ValueError(f"Node {u!r} has no 'pos' attribute.")
			pos[u] = attrs["pos"]

		# 1) draw nodes first and keep their patch objects (so arrows can 'shrink' to them)
		node_patches = {}
		for u, (x, y) in pos.items():
			face = node_face if not (node_colors_from_table and u in node_colors_from_table) \
				   else node_colors_from_table[u]
			circ = plt.Circle((x, y), node_radius, facecolor=face, edgecolor=node_edge,
							  linewidth=1.6, zorder=4)
			ax.add_patch(circ)
			node_patches[u] = circ
			ax.text(x, y, str(u), ha="center", va="center", color=label_color, fontsize=12, zorder=5)

		# helper to add one edge (straight or curved)
		def _add_edge(u, v, *, color=edge_color, lw=1.6, rad: float | None = None, z=2):
			(x1, y1), (x2, y2) = pos[u], pos[v]
			cs = f"arc3,rad={rad or 0.0}"
			arrow = FancyArrowPatch(
				(x1, y1), (x2, y2),
				connectionstyle=cs,
				arrowstyle="-|>" if self.directed else "-",
				mutation_scale=12.0,
				linewidth=lw,
				color=color,
				zorder=z,
				patchA=node_patches[u],
				patchB=node_patches[v],
				shrinkA=0, shrinkB=0,
			)
			ax.add_patch(arrow)
			return arrow

		def _label_edge(arrow, text):
			if text is None:
				return
			# Quadratic Bezier: 3 vertices -> midpoint & normal for a tidy offset
			path = arrow.get_path()
			verts = path.vertices
			if len(verts) < 3:
				return
			P0, P1, P2 = verts[0], verts[1], verts[2]
			t = 0.5
			mid = (1 - t)**2 * P0 + 2 * (1 - t) * t * P1 + t**2 * P2
			# tangent and normal
			d = 2 * (1 - t) * (P1 - P0) + 2 * t * (P2 - P1)
			n = np.array([-d[1], d[0]])
			if np.linalg.norm(n) != 0:
				n = n / np.linalg.norm(n)
			# small offset so the label doesn’t sit on the line
			offset = -0.06  # tweak for your coordinate scale
			xy = mid + offset * n
			ax.text(
				xy[0], xy[1], str(text),
				ha="center", va="center",
				fontsize=10, color=label_color, zorder=6,
				bbox=dict(boxstyle="round,pad=0.2", fc="none", ec="none", alpha=0.8),
			)

		# 2) base edges
		curved_edges = curved_edges or {}
		for u in self.adj:
			for v, data in self.adj[u].items():
				# avoid duplicate labels on undirected graphs
				if not self.directed and str(u) > str(v):
					continue
				weight = data.get("weight")
				rad = curved_edges.get((u, v))
				arrow = _add_edge(u, v, color=edge_color, lw=1.4, rad=rad, z=2)
				_label_edge(arrow, weight)


		# 3) highlight tree edges on top
		if highlight_tree_edges:
			for (u, v) in highlight_tree_edges:
				rad = curved_edges.get((u, v))
				_add_edge(u, v, color="#1f77b4", lw=3.0, rad=rad, z=3)

		ax.set_aspect("equal")
		ax.set_xticks([]); ax.set_yticks([])
		ax.margins(0.2)
		if title:
			ax.set_title(title)
		fig.tight_layout()
		if show:
			plt.show()
		return ax

	def _bfs_table(self):
		table: dict[Hashable, dict[str, Any]] = {}
		for node in self.nodes:
			table[node] = {
				'thru': None,
				'distance': float("inf"),
				'status': 'waiting',   # waiting / visited / done
			}
		return table

	def bfs(
		self,
		start_node: Hashable,
		reverse: bool = False,
		extra_check: EdgeCheck | None = None,
	):
		if start_node not in self.nodes:
			raise KeyError(f"Start node {start_node!r} not in graph")

		extra_check = extra_check or (lambda _prev, _u, _v: True)

		queue = deque([start_node])
		order: list[Hashable] = []
		table = self._bfs_table()

		table[start_node]['thru'] = None
		table[start_node]['distance'] = 0
		table[start_node]['status'] = 'visited'

		while queue:
			current = queue.popleft()
			order.append(current)

			prev = table[current]['thru']  # this is the node we came from to reach `current`

			for nbr in self.neighbors(current, reverse=reverse):
				# run extra check *before* enqueuing / relaxing this edge
				if not extra_check(prev, current, nbr):
					continue

				if table[nbr]['status'] == 'waiting':
					table[nbr]['thru'] = current
					table[nbr]['distance'] = table[current]['distance'] + 1
					table[nbr]['status'] = 'visited'
					queue.append(nbr)

			table[current]['status'] = 'done'

		return order, table

	# ---------- DFS ----------

	def _dfs_table(self):
		table: dict[Hashable, dict[str, Any]] = {}
		for node in self.nodes:
			table[node] = {
				'thru': None,
				'discovery_time': float("inf"),
				'finish_time': float("inf"),
				'status': 'waiting',   # waiting / visited / done
			}
		return table

	def dfs(
		self,
		start_node: Hashable,
		reverse: bool = False,
		extra_check: EdgeCheck | None = None,
	):
		if start_node not in self.nodes:
			raise KeyError(f"Start node {start_node!r} not in graph")

		extra_check = extra_check or (lambda _prev, _u, _v: True)

		table = self._dfs_table()
		time = 1

		def _go(node: Hashable, parent: Hashable | None):
			nonlocal time
			table[node]['thru'] = parent
			table[node]['status'] = 'visited'
			table[node]['discovery_time'] = time
			time += 1

			for nbr in self.neighbors(node, reverse=reverse):
				if table[nbr]['status'] == 'waiting':
					# `parent` is the node we entered `node` from
					if not extra_check(parent, node, nbr):
						continue
					_go(nbr, node)

			table[node]['status'] = 'done'
			table[node]['finish_time'] = time
			time += 1

		_go(start_node, None)
		return table

	# ---------- Bellman–Ford ----------

	def _b_f_table(self):
		table: dict[Hashable, dict[str, Any]] = {}
		for node in self.nodes:
			table[node] = {
				'thru': None,
				'distance': float("inf"),
			}
		return table

	def b_f(
		self,
		start_node: Hashable,
		extra_check: EdgeCheck | None = None,
	):
		if start_node not in self.nodes:
			raise KeyError(f"Start node {start_node!r} not in graph")

		extra_check = extra_check or (lambda _prev, _u, _v: True)

		table = self._b_f_table()
		table[start_node]['distance'] = 0
		edges = self.edges()  # list of (u, v, w)

		# relax edges |V|-1 times
		for _ in range(len(self.nodes) - 1):
			updated = False
			for u, v, w in edges:
				if table[u]['distance'] == float("inf"):
					continue

				prev = table[u]['thru']
				if not extra_check(prev, u, v):
					continue

				if table[u]['distance'] + w < table[v]['distance']:
					table[v]['distance'] = table[u]['distance'] + w
					table[v]['thru'] = u
					updated = True

			if not updated:
				break

		# negative cycle check
		for u, v, w in edges:
			if table[u]['distance'] == float("inf"):
				continue

			prev = table[u]['thru']
			if not extra_check(prev, u, v):
				continue

			if table[u]['distance'] + w < table[v]['distance']:
				raise Exception("Negative cycle detected!")

		return table

	# ---------- Dijkstra ----------

	def dijkstra(
		self,
		start_node: Hashable,
		extra_check: EdgeCheck | None = None,
	):
		if start_node not in self.nodes:
			raise KeyError(f"Start node {start_node!r} not in graph")

		extra_check = extra_check or (lambda _prev, _u, _v: True)

		table = self._b_f_table()
		table[start_node]['distance'] = 0

		heap: list[tuple[float, Hashable]] = [(0.0, start_node)]
		visited: set[Hashable] = set()

		while heap:
			dist_u, u = heappop(heap)
			if u in visited:
				continue
			visited.add(u)

			if dist_u > table[u]['distance']:
				continue

			prev = table[u]['thru']

			for v, data in self.adj[u].items():
				w = data['weight']
				if w < 0:
					raise Exception("Cannot use Dijkstra for negative edges!")

				if not extra_check(prev, u, v):
					continue

				if dist_u + w < table[v]['distance']:
					table[v]['distance'] = dist_u + w
					table[v]['thru'] = u
					heappush(heap, (table[v]['distance'], v))

		return table
