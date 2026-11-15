import io
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

from app import App


class AppTests(unittest.TestCase):
	def test_disconnect_removes_connection_from_output(self):
		app = App()
		app.network.connect("A", "B")
		app.network.connect("A", "F")

		with (
			patch("builtins.input", side_effect=["a", "f"]),
			patch("os.system"),
			io.StringIO() as buf,
			redirect_stdout(buf),
		):
			app._disconnect()
			output = buf.getvalue()

		self.assertIn("Disconnected A and F.", output)
		self.assertIn("Active Connections:", output)
		self.assertIn("A --> B", output)
		self.assertNotIn("A --> F", output)


if __name__ == "__main__":
	unittest.main()
