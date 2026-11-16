import os
import time

import pytest
import requests

SIM_URL = os.environ.get("SIM_URL", "http://localhost:8000")


class Controller:
    """Small test client for the controller API."""

    def __init__(self, base_url):
        self.base = base_url

    def _post(self, path, body=None):
        return requests.post(f"{self.base}{path}", json=body or {}, timeout=5)

    def status(self):
        return requests.get(f"{self.base}/status", timeout=5).json()

    def command(self, action):
        return self._post("/command", {"action": action})

    def set_setpoint(self, bar):
        return self._post("/setpoint", {"suction_pressure_bar": bar})

    def set_load(self, pct):
        return self._post("/load", {"load_pct": pct})

    def inject_fault(self, offset):
        return self._post("/fault", {"discharge_temp_offset": offset})

    def tick(self, seconds):
        return self._post("/tick", {"seconds": seconds}).json()

    def start_and_wait_running(self):
        assert self.command("start").status_code == 200
        status = self.tick(10)
        assert status["state"] == "RUNNING"
        return status


@pytest.fixture(scope="session")
def base_url():
    deadline = time.time() + 30
    while time.time() < deadline:
        try:
            if requests.get(f"{SIM_URL}/health", timeout=1).ok:
                return SIM_URL
        except requests.ConnectionError:
            pass
        time.sleep(0.5)
    pytest.exit(f"simulator not reachable at {SIM_URL}", returncode=2)


@pytest.fixture
def ctrl(base_url):
    """Fresh controller for every test, so tests never depend on each other."""
    requests.post(f"{base_url}/reset", timeout=5)
    return Controller(base_url)
