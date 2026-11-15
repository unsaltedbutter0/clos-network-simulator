import unittest

from network import Network


class NetworkDisconnectTests(unittest.TestCase):
	def setUp(self):
		self.node_map = {
			"A": ({"B": 1}, (0, 0)),
			"B": ({"A": 1, "C": 1}, (1, 0)),
			"C": ({"B": 1}, (2, 0)),
		}

	def test_disconnect_frees_reservations(self):
		network = Network(False, self.node_map, "bfs")
		path = network.connect("A", "C")
		self.assertEqual(path, ["A", "B", "C"])
		self.assertIn(("A", "C"), network.reserved_conns)

		network.disconnect("A", "C")
		self.assertNotIn(("A", "C"), network.reserved_conns)
		self.assertEqual(set(), network.reserved_edges)

	def test_disconnect_allows_reconnect(self):
		network = Network(False, self.node_map, "bfs")
		self.assertEqual(network.connect("A", "C"), ["A", "B", "C"])
		network.disconnect("A", "C")

		clos = network.closes["B"]
		self.assertEqual(set(), clos.used_start_ports)
		self.assertEqual(set(), clos.used_end_ports)

		self.assertEqual(network.connect("A", "C"), ["A", "B", "C"])

	def test_disconnect_accepts_reverse_order(self):
		network = Network(False, self.node_map, "bfs")
		self.assertEqual(network.connect("A", "C"), ["A", "B", "C"])

		network.disconnect("C", "A")
		self.assertNotIn(("A", "C"), network.reserved_conns)


if __name__ == "__main__":
	unittest.main()
