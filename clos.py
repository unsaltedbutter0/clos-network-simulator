# python 3.10.2

class Clos:
	FREE = 0
	USED = 1
	def __init__(self, n: int = 2, m: int = 3, r: int = 2):
		self.n = n 		# in/out ports
		self.m = m 		# middle switches
		self.r = r  	# in/out switches	

		self.N = n*r

		# "status": "free"/"blocking"
		# left_p[r][m]
		self.left_p = [[self.FREE for _ in range(m)] for _ in range(r)]
		# middle_s = [[] for _ in range(m)]
		self.right_p = [[self.FREE for _ in range(m)] for _ in range(r)]

		self.connections = {}
		self.used_start_ports = set()
		self.used_end_ports = set()

	def _can_connect(self, start_port: int, end_port: int):
		if start_port >= self.N or end_port >= self.N or start_port < 0 or end_port < 0:
			raise ValueError(f"Given port out of bounds! Must be in 0..{self.N - 1}")
		if start_port in self.used_start_ports:
			raise ValueError(f"Given start_port already in use!")
		if end_port in self.used_end_ports:
			raise ValueError(f"Given end_port already in use!")
		i = start_port // self.n
		o = end_port // self.n

		for k in range(self.m):
			if self.left_p[i][k] == self.right_p[o][k] == self.FREE:
				return k
		return None

	def _reserve(self, i: int, k: int, o: int):
		self.left_p[i][k] = self.USED
		self.right_p[o][k] = self.USED
		
	def _release(self, i: int, k: int, o: int):
		self.left_p[i][k] = self.FREE
		self.right_p[o][k] = self.FREE

	def connect(self, start_port: int, end_port: int):
		k = self._can_connect(start_port, end_port)
		if k is None:
			return False, None

		i = start_port // self.n
		o = end_port // self.n
		self._reserve(i, k, o)
		self.connections[(start_port, end_port)] = (i, k, o)
		self.used_start_ports.add(start_port); self.used_end_ports.add(end_port)
		return True, (i, k, o)
			
	def disconnect(self, start_port: int, end_port: int):
		if start_port >= self.N or end_port >= self.N or start_port < 0 or end_port < 0:
			raise ValueError(f"Given port out of bounds! Must be in 0..{self.N - 1}")
		if (start_port, end_port) not in self.connections:
			return False, None

		i, k, o = self.connections.pop((start_port, end_port))
		self._release(i, k, o)
		self.used_start_ports.discard(start_port)
		self.used_end_ports.discard(end_port)
		return True, (i, k, o)
