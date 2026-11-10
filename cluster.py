"""Orquestador local de procesos (nodos lógicos separados en localhost)."""
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from urllib.error import URLError
from common import call_json

ROOT = Path(__file__).resolve().parent


class Cluster:
    def __init__(self, n_workers=2, base=18000, delay=0.12, keep_db=False):
        if n_workers not in (1, 2):
            raise ValueError("El prototipo contempla 1 o 2 nodos")
        self.n_workers = n_workers
        self.base = base
        self.delay = delay
        self.temp = tempfile.TemporaryDirectory(prefix="spawntech_")
        self.db = str(ROOT / "spawntech.db") if keep_db else str(Path(self.temp.name) / "tickets.db")
        self.processes = {}
        self.logs = {}
        self.gateway_url = f"http://127.0.0.1:{base}"
        self.observer_url = f"http://127.0.0.1:{base+20}"

    def _start(self, name, file, *args):
        log_file = open(Path(self.temp.name) / f"{name}.log", "wb")
        self.logs[name] = log_file
        process = subprocess.Popen([sys.executable, str(ROOT / file), *map(str, args)],
                                   stdout=log_file, stderr=subprocess.STDOUT, cwd=ROOT)
        self.processes[name] = process

    def _ready(self, url):
        for _ in range(100):
            try:
                if call_json(url + "/health", timeout=0.2).get("ok"):
                    return
            except (OSError, URLError, ValueError):
                pass
            time.sleep(0.05)
        raise RuntimeError(f"El servicio no inició: {url}")

    def start(self):
        self._start("observador", "events.py", "--port", self.base + 20)
        self._ready(self.observer_url)
        for i in range(self.n_workers):
            self._start(f"nodo-{i+1}", "worker.py", "--port", self.base + 11 + i,
                        "--id", f"nodo-{'AB'[i]}", "--delay", self.delay)
            self._ready(f"http://127.0.0.1:{self.base+11+i}")
        workers = ",".join(f"http://127.0.0.1:{self.base+11+i}" for i in range(self.n_workers))
        self._start("gateway", "gateway.py", "--port", self.base,
                    "--workers", workers, "--observer", self.observer_url, "--db", self.db)
        self._ready(self.gateway_url)
        return self

    def stop_service(self, name):
        proc = self.processes.get(name)
        if proc and proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=2)

    def stop(self):
        for name in reversed(list(self.processes)):
            self.stop_service(name)
        for log in self.logs.values():
            log.close()
        self.temp.cleanup()

    def __enter__(self):
        return self.start()

    def __exit__(self, *_):
        self.stop()
