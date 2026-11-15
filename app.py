import copy
import json
import os
from typing import Hashable
from network import Network

# Example topology: node -> ({neighbour: link weight}, (x, y) position)
DEFAULT_MAP = {
	"A": ({"B": 3, "D": 2}, (0, 0)),
	"B": ({"A": 3, "D": 4}, (0, -1)),
	"C": ({"D": 3, "F": 6}, (1, 0)),
	"D": ({"A": 2, "B": 4, "C": 3, "G": 1}, (1, -1)),
	"E": ({"G": 5, "H": 2}, (1, -2)),
	"F": ({"C": 6, "G": 2}, (2, 0)),
	"G": ({"D": 1, "E": 5, "F": 2, "H": 2}, (2, -1)),
	"H": ({"E": 2, "G": 2}, (2, -2)),
}

class App:
	def __init__(self):
		self.network = Network(False, copy.deepcopy(DEFAULT_MAP), "bfs")

	def run(self):
		while True:
			self.print_options()
			match input(">"):
				case "0":
					self._import_map()
				case "1":
					self._add_node()
				case "2":
					self._add_edge()
				case "3":
					self._connect()
				case "4":
					self._disconnect()
				case "5":
					self._print_connections()
				case "6":
					self._change_alg()
				case "7":
					break
				case _:
					os.system('cls' if os.name == 'nt' else 'clear')
					print("[!]Not a valid option.")

				

	def print_options(self):
		
		print("0 - Import node map from json file (drops all connections)")
		print("1 - Add node")
		print("2 - Add edge")
		print("3 - Make a connection")
		print("4 - Remove the connection")
		print("5 - List active connections")
		print("6 - Change used algorithm")
		print("7 - exit")
		print("Stats:")
		self._status()
		
	def _status(self):
		from tabulate import tabulate

		data = [{
			"Algorithm": self.network.alg,
			"Active Conn": str(len(self.network.reserved_conns))
			}]
		print(tabulate(data, headers="keys"))

	def _change_alg(self):
		print("Which algorithm to use?")
		print("0 - BFS")
		print("1 - DFS")
		print("2 - Bellman Ford")
		print("3 - Dijkstra")

		match input(">"):
			case "0":
				self.network.alg = "bfs"
			case "1":
				self.network.alg = "dfs"
			case "2":
				self.network.alg = "b_f"
			case "3":
				self.network.alg = "dik"

	def _disconnect(self):
		os.system('cls' if os.name == 'nt' else 'clear')
		u = input("Disconnect node:\n>").strip().upper()
		v = input("And node:\n>").strip().upper()
		try:
			self.network.disconnect(u, v)
			print(f"Disconnected {u} and {v}.")
			self._print_connections(clear=False)
		except ValueError as e:
			print(f"[!]Error while disconnecting: {e}")

	def _print_connections(self, *, clear: bool = True):
		if clear:
			os.system('cls' if os.name == 'nt' else 'clear')
		print("Active Connections:")
		for i, (x, y) in enumerate(self.network.reserved_conns.items()):
			print(f"{i}. {x[0]} --> {x[1]}; thru: ({y})")

	def _connect(self):
		os.system('cls' if os.name == 'nt' else 'clear')
		u = input("Connect from node:\n>").strip().upper()
		v = input("To node:\n>").strip().upper()
		if self.network.connect(u, v) is None:
			print("[!]Connecting unsuccessful!")

	def _add_edge(self):
		os.system('cls' if os.name == 'nt' else 'clear')
		u = input("Give first node\n>").strip().upper()
		v = input("Give second node\n>").strip().upper()
		try:
			self.network.add_edge(u, v)
		except ValueError as e:
			print(f"[!]Error while adding edge: {e}")

	def _add_node(self):
		os.system('cls' if os.name == 'nt' else 'clear')
		node = input("What node to add?\n>").strip().upper()
		try:
			self.network.add_node(node)
		except ValueError as e:
			print(f"[!]Error while adding node: {e}")

	def _import_map(self):
		file_path = input("What's the path to the file?")
		with open(file_path) as f:
			nmap = json.loads(f.read())
			self.network = Network(False, nmap, "bfs")

if __name__ == "__main__":
	app = App()
	app.run()
