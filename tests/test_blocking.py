import unittest

from network import Network


def star_map():
	# X is a switch with four neighbours, so all paths between leaves pass through it.
	return {
		"X": ({"A": 1, "B": 1, "C": 1, "D": 1}, (0, 0)),
		"A": ({"X": 1}, (-1, 1)),
		"B": ({"X": 1}, (1, 1)),
		"C": ({"X": 1}, (-1, -1)),
		"D": ({"X": 1}, (1, -1)),
	}


class ClosBlockingTests(unittest.TestCase):
	def test_default_fabric_is_non_blocking(self):
		network = Network(False, star_map(), "bfs")
		self.assertEqual(network.connect("A", "B"), ["A", "X", "B"])
		self.assertEqual(network.connect("C", "D"), ["C", "X", "D"])

	def test_small_fabric_blocks_internally(self):
		# With a single middle switch, X can carry only one connection at a time,
		# even though the links to C and D are free.
		network = Network(False, star_map(), "bfs", middle_switches=1)
		self.assertEqual(network.connect("A", "B"), ["A", "X", "B"])
		self.assertIsNone(network.connect("C", "D"))

		network.disconnect("A", "B")
		self.assertEqual(network.connect("C", "D"), ["C", "X", "D"])


class LinkBlockingTests(unittest.TestCase):
	def test_reserved_link_cannot_be_reused(self):
		node_map = {
			"A": ({"B": 1}, (0, 0)),
			"B": ({"A": 1, "C": 1}, (1, 0)),
			"C": ({"B": 1}, (2, 0)),
		}
		network = Network(False, node_map, "dik")
		self.assertEqual(network.connect("A", "C"), ["A", "B", "C"])
		self.assertIsNone(network.connect("B", "C"))


class AlgorithmTests(unittest.TestCase):
	def test_dijkstra_and_bellman_ford_find_cheapest_route(self):
		node_map = {
			"A": ({"B": 1, "C": 5}, (0, 0)),
			"B": ({"A": 1, "C": 1}, (1, 1)),
			"C": ({"A": 5, "B": 1}, (2, 0)),
		}
		for alg in ("dik", "b_f"):
			with self.subTest(alg=alg):
				network = Network(False, {k: (dict(v[0]), v[1]) for k, v in node_map.items()}, alg)
				self.assertEqual(network.connect("A", "C"), ["A", "B", "C"])

	def test_bfs_finds_fewest_hops(self):
		node_map = {
			"A": ({"B": 1, "C": 5}, (0, 0)),
			"B": ({"A": 1, "C": 1}, (1, 1)),
			"C": ({"A": 5, "B": 1}, (2, 0)),
		}
		network = Network(False, node_map, "bfs")
		self.assertEqual(network.connect("A", "C"), ["A", "C"])

	def test_topology_is_locked_while_connections_exist(self):
		network = Network(False, star_map(), "bfs")
		network.connect("A", "B")
		with self.assertRaises(ValueError):
			network.add_edge("A", "C")


if __name__ == "__main__":
	unittest.main()
