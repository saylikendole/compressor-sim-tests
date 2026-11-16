"""HTTP API around the simulator, so tests talk to it over the network
the same way they would talk to a real controller on a test bench."""
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from compressor import Compressor, CommandRejected

sim = Compressor()


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body):
        data = json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *args):
        pass

    def do_GET(self):
        if self.path == "/health":
            return self._send(200, {"ok": True})
        if self.path == "/status":
            return self._send(200, sim.status())
        self._send(404, {"error": "not found"})

    def do_POST(self):
        global sim
        length = int(self.headers.get("Content-Length", 0))
        try:
            body = json.loads(self.rfile.read(length) or b"{}")
            if self.path == "/reset":
                sim = Compressor()
            elif self.path == "/command":
                action = body.get("action")
                actions = {"start": sim.start, "stop": sim.stop, "reset_alarm": sim.reset_alarm}
                if action not in actions:
                    return self._send(400, {"error": f"unknown action: {action}"})
                actions[action]()
            elif self.path == "/setpoint":
                sim.set_setpoint(float(body["suction_pressure_bar"]))
            elif self.path == "/load":
                sim.set_load(float(body["load_pct"]))
            elif self.path == "/fault":
                sim.inject_fault(float(body.get("discharge_temp_offset", 0)))
            elif self.path == "/tick":
                sim.tick(int(body["seconds"]))
            else:
                return self._send(404, {"error": "not found"})
        except CommandRejected as e:
            return self._send(409, {"error": str(e)})
        except (ValueError, KeyError) as e:
            return self._send(400, {"error": str(e)})
        self._send(200, sim.status())


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))
    print(f"compressor simulator listening on {port}", flush=True)
    ThreadingHTTPServer(("0.0.0.0", port), Handler).serve_forever()
