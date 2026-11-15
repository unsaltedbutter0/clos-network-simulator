from clos import Clos
from graph import Graph
from typing import Hashable
import math

# Routing algorithms: "bfs", "dfs", "b_f" (Bellman-Ford), "dik" (Dijkstra)
class Network:
	"""Circuit-switched network where every node is a three-stage Clos switch.

	n               -- ports per input/output switch of each node's Clos fabric
	middle_switches -- middle-stage switches (m). Defaults to 2n - 1, Clos's
	                   strict-sense non-blocking condition; a smaller value
	                   lets a node block internally.
	"""

	def __init__(
		self,
		directed: bool = False,
		node_map: dict | None = None,
		alg: str = "bfs",
		n: int = 4,
		middle_switches: int | None = None,
	):
		self.alg = alg
		self.n = n
		self.middle_switches = middle_switches
		self.node_map = node_map or {}
		self.graph = Graph(directed=directed, node_map=self.node_map)

		self.closes = self._calc_closes()
		self.clos_ports = {node: sorted(v[0].keys()) for node, v in self.node_map.items()}

		self.reserved_edges = set()
		self.reserved_conns = dict()

	def _ensure_mutable(self, action: str):
		if self.reserved_conns:
			raise ValueError(
				f"Cannot {action} while active connections exist. Disconnect first."
			)

	def _conn_key(self, from_node: Hashable, to_node: Hashable) -> tuple[Hashable, Hashable]:
		if self.graph.directed:
			return (from_node, to_node)
		return tuple(sorted((from_node, to_node)))

	def _calc_closes(self):
		closes = {}
		for k, v in self.node_map.items():
			ports = len(v[0])                      # one port per neighbouring link
			n = self.n
			r = math.ceil(ports / n)
			m = self.middle_switches if self.middle_switches is not None else 2 * n - 1
			closes[k] = Clos(n, m, r)
		return closes

	def _clos_ok(self, fro: Hashable | None, curr: Hashable, to: Hashable | None) -> bool:
		if fro is None:
			return True

		if curr not in self.closes or curr not in self.clos_ports:
			return False
		curr_ports = self.clos_ports[curr]

		try:
			start_port = curr_ports.index(fro) 
			end_port = curr_ports.index(to)
		except ValueError:
			return False

		try:
			k = self.closes[curr]._can_connect(start_port, end_port)
		except ValueError:
			return False
			
		return k is not None

	def _edge_ok(self, u: Hashable, v: Hashable):
		return ((u, v) not in self.reserved_edges) and ((v, u) not in self.reserved_edges)

	def can_connect_these(self, fro: Hashable | None, curr: Hashable, to: Hashable | None):
		return self._clos_ok(fro, curr, to) and self._edge_ok(curr, to)

	def _reconstruct_path(self, table: dict, start: Hashable, goal: Hashable) -> list[Hashable] | None:
		if goal not in table or table[goal]['thru'] is None and goal != start:
			return None

		path: list[Hashable] = []
		curr: Hashable | None = goal
		while curr is not None:
			path.append(curr)
			curr = table[curr]['thru']
		path.reverse()

		if not path or path[0] != start:
			return None
		return path

	def _get_tables(self, start_node: Hashable):
		if start_node not in self.graph.nodes:
			raise KeyError(f"Start node {start_node!r} not in graph")

		match self.alg:
			case "bfs":
				_order, table = self.graph.bfs(start_node, extra_check=self.can_connect_these)
			case "dfs":
				table = self.graph.dfs(start_node, extra_check=self.can_connect_these)
			case "b_f":
				table = self.graph.b_f(start_node, extra_check=self.can_connect_these)
			case "dik":
				table = self.graph.dijkstra(start_node, extra_check=self.can_connect_these)
			case _:
				raise ValueError(f"Unknown algorithm {self.alg!r}")
		return table

	def _reserve_path(self, path: list[Hashable]):
		for a, b in zip(path, path[1:]):
			self.reserved_edges.add((a, b))

		for prev, curr, nxt in zip(path, path[1:], path[2:]):
			ports = self.clos_ports[curr]
			i = ports.index(prev)
			o = ports.index(nxt)

			ok, _info = self.closes[curr].connect(i, o)
			if not ok:
				raise RuntimeError(f"Failed to reserve Clos at {curr} for {prev}->{curr}->{nxt}")

		self.reserved_conns[self._conn_key(path[0], path[-1])] = path

	def disconnect(self, from_node: Hashable, to_node: Hashable):
		if from_node not in self.clos_ports or to_node not in self.clos_ports:
			raise ValueError("Given node not in the node map!")

		conn_key = self._conn_key(from_node, to_node)
		if conn_key not in self.reserved_conns:
			raise ValueError(f"No active connection between {from_node} and {to_node} nodes")

		path = self.reserved_conns.pop(conn_key)

		for a, b in zip(path, path[1:]):
			self.reserved_edges.discard((a, b))

		for prev, curr, nxt in zip(path, path[1:], path[2:]):
			ports = self.clos_ports[curr]
			i = ports.index(prev)
			o = ports.index(nxt)

			ok, _info = self.closes[curr].disconnect(i, o)
			if not ok:
				raise RuntimeError(f"Failed to disconnect Clos at {curr} for {prev}->{curr}->{nxt}")

	def connect(self, from_node: Hashable, to_node: Hashable):
		if from_node not in self.clos_ports or to_node not in self.clos_ports:
			raise ValueError("Given node not in the node map!")

		table = self._get_tables(from_node)
		path = self._reconstruct_path(table, from_node, to_node)

		if path is None:
			return None

		self._reserve_path(path)
		return path

	def add_node(self, node: Hashable, pos: tuple[float, float] | None = None):
		self._ensure_mutable("add node")
		if node in self.node_map:
			raise ValueError(f"Node {node!r} already exists")
		self.node_map[node] = ({}, pos or (0.0, 0.0))
		self.graph.add_node(node, pos=pos or (0.0, 0.0))
		self.closes = self._calc_closes()
		self.clos_ports = {n: sorted(v[0].keys()) for n, v in self.node_map.items()}

	def add_edge(self, u: Hashable, v: Hashable, weight: int | float = 1):
		self._ensure_mutable("add edge")
		if u not in self.node_map:
			self.add_node(u)
		if v not in self.node_map:
			self.add_node(v)
		self.graph.add_edge(u, v, weight=weight)
		self.node_map[u][0][v] = weight
		if not self.graph.directed:
			self.node_map[v][0][u] = weight
		self.closes = self._calc_closes()
		self.clos_ports = {n: sorted(vs[0].keys()) for n, vs in self.node_map.items()}

