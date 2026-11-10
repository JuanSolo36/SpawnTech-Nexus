"""Observador remoto: recibe los eventos 'ticket_creado' y los expone."""
import argparse
import threading
from http.server import ThreadingHTTPServer
from common import JsonHandler, utc_now


class EventServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, address, handler):
        super().__init__(address, handler)
        self.events = []
        self.lock = threading.Lock()


class EventHandler(JsonHandler):
    def do_GET(self):
        if self.path == "/health":
            return self.send_json(200, {"ok": True, "servicio": "observador"})
        if self.path == "/events":
            with self.server.lock:
                events = list(self.server.events)
            return self.send_json(200, {"cantidad": len(events), "eventos": events[-100:]})
        return self.send_json(404, {"error": "Ruta no encontrada"})

    def do_POST(self):
        if self.path != "/events":
            return self.send_json(404, {"error": "Ruta no encontrada"})
        try:
            event = self.read_json()
            if not isinstance(event, dict) or not event.get("ticket_id") or not event.get("tipo"):
                raise ValueError("Evento invalido")
        except ValueError as exc:
            return self.send_json(400, {"error": str(exc)})
        event["recibido_en"] = utc_now()
        with self.server.lock:
            self.server.events.append(event)
        return self.send_json(201, {"registrado": True})


def main():
    p = argparse.ArgumentParser(description="Observador SpawnTech")
    p.add_argument("--port", type=int, default=8200)
    args = p.parse_args()
    server = EventServer(("127.0.0.1", args.port), EventHandler)
    print(f"[Observador] http://127.0.0.1:{args.port}", flush=True)
    try:
        server.serve_forever(poll_interval=0.2)
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
