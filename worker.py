"""Nodo procesador de solicitudes de soporte o desarrollo (prototipo didáctico)."""
import argparse
import threading
import time
from http.server import ThreadingHTTPServer
from common import JsonHandler, utc_now


class WorkerServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, address, handler, worker_id, max_active=2, delay=0.12):
        super().__init__(address, handler)
        self.worker_id = worker_id
        self.limit = threading.BoundedSemaphore(max_active)
        self.delay = delay
        self.processed = 0
        self.lock = threading.Lock()
        self.cache = {}


class WorkerHandler(JsonHandler):
    def do_GET(self):
        if self.path == "/health":
            return self.send_json(200, {"ok": True, "nodo": self.server.worker_id,
                                        "procesadas": self.server.processed})
        return self.send_json(404, {"error": "Ruta no encontrada"})

    def do_POST(self):
        if self.path != "/process":
            return self.send_json(404, {"error": "Ruta no encontrada"})
        try:
            ticket = self.read_json()
            if not isinstance(ticket, dict) or not ticket.get("id") or ticket.get("categoria") not in ("soporte", "desarrollo"):
                raise ValueError("Se requiere id y categoria valida")
        except ValueError as exc:
            return self.send_json(400, {"error": str(exc)})
        with self.server.lock:
            previous = self.server.cache.get(ticket["id"])
        if previous:
            return self.send_json(200, previous)
        with self.server.limit:
            # Simulación reproducible de un trabajo de clasificación/encolamiento de I/O.
            time.sleep(self.server.delay)
            result = {
                "id": ticket["id"], "estado": "en_cola_de_atencion",
                "cola": "soporte_tecnico" if ticket["categoria"] == "soporte" else "desarrollo_software",
                "nodo": self.server.worker_id,
                "hilo": threading.current_thread().name,
                "procesado_en": utc_now(),
            }
            with self.server.lock:
                self.server.cache[ticket["id"]] = result
                self.server.processed += 1
        return self.send_json(200, result)


def main():
    p = argparse.ArgumentParser(description="Nodo procesador SpawnTech")
    p.add_argument("--port", type=int, default=8101)
    p.add_argument("--id", default="nodo-A")
    p.add_argument("--max-active", type=int, default=2)
    p.add_argument("--delay", type=float, default=0.12)
    args = p.parse_args()
    server = WorkerServer(("127.0.0.1", args.port), WorkerHandler, args.id, args.max_active, args.delay)
    print(f"[Worker {args.id}] http://127.0.0.1:{args.port}, hilos activos={args.max_active}", flush=True)
    try:
        server.serve_forever(poll_interval=0.2)
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
