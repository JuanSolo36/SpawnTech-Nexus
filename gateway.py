"""Gateway, mediador y proxy para los nodos de SpawnTech Nexus."""
import argparse
import sqlite3
import threading
import uuid
from http.server import ThreadingHTTPServer
from urllib.error import HTTPError, URLError
from common import JsonHandler, call_json, utc_now


class TicketStore:
    def __init__(self, path):
        self.path = path
        self.lock = threading.Lock()
        with sqlite3.connect(self.path) as db:
            db.execute("""CREATE TABLE IF NOT EXISTS tickets (
                id TEXT PRIMARY KEY, titulo TEXT NOT NULL, categoria TEXT NOT NULL,
                descripcion TEXT NOT NULL, estado TEXT NOT NULL, cola TEXT NOT NULL,
                nodo TEXT NOT NULL, creado_en TEXT NOT NULL)""")

    def add(self, ticket):
        with self.lock, sqlite3.connect(self.path, timeout=15) as db:
            db.execute("INSERT INTO tickets VALUES (?,?,?,?,?,?,?,?)",
                       (ticket["id"], ticket["titulo"], ticket["categoria"],
                        ticket["descripcion"], ticket["estado"], ticket["cola"],
                        ticket["nodo"], ticket["creado_en"]))

    def list(self, ticket_id=None):
        with self.lock, sqlite3.connect(self.path, timeout=15) as db:
            db.row_factory = sqlite3.Row
            sql = "SELECT * FROM tickets"
            if ticket_id:
                rows = db.execute(sql + " WHERE id = ?", (ticket_id,)).fetchall()
            else:
                rows = db.execute(sql + " ORDER BY creado_en DESC LIMIT 100").fetchall()
            return [dict(row) for row in rows]

    def stats(self):
        with self.lock, sqlite3.connect(self.path, timeout=15) as db:
            total = db.execute("SELECT COUNT(*) FROM tickets").fetchone()[0]
            nodes = db.execute("SELECT nodo, COUNT(*) FROM tickets GROUP BY nodo").fetchall()
            return {"total_tickets": total, "por_nodo": dict(nodes)}


class GatewayServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, address, handler, workers, observer_url, db_path):
        super().__init__(address, handler)
        self.workers = workers
        self.observer_url = observer_url
        self.store = TicketStore(db_path)
        self.position = 0
        self.lock = threading.Lock()
        self.observer_errors = 0

    def next_workers(self):
        with self.lock:
            start = self.position % len(self.workers)
            self.position += 1
        return self.workers[start:] + self.workers[:start]


class GatewayHandler(JsonHandler):
    def do_GET(self):
        if self.path == "/health":
            return self.send_json(200, {"ok": True, "servicio": "gateway", "nodos_configurados": len(self.server.workers)})
        if self.path == "/tickets":
            return self.send_json(200, {"tickets": self.server.store.list()})
        if self.path.startswith("/tickets/"):
            ticket_id = self.path.partition("/tickets/")[2]
            items = self.server.store.list(ticket_id)
            return self.send_json(200, items[0]) if items else self.send_json(404, {"error": "Ticket inexistente"})
        if self.path == "/stats":
            data = self.server.store.stats()
            data["fallos_observador"] = self.server.observer_errors
            return self.send_json(200, data)
        return self.send_json(404, {"error": "Ruta no encontrada"})

    def do_POST(self):
        if self.path != "/tickets":
            return self.send_json(404, {"error": "Ruta no encontrada"})
        try:
            data = self.read_json()
            if not isinstance(data, dict):
                raise ValueError("Se requiere un objeto JSON")
            title = data.get("titulo", "")
            category = data.get("categoria", "")
            description = data.get("descripcion", "")
            if not isinstance(title, str) or not title.strip() or len(title) > 120:
                raise ValueError("Titulo requerido (maximo 120 caracteres)")
            if category not in ("soporte", "desarrollo"):
                raise ValueError("Categoria: soporte o desarrollo")
            if not isinstance(description, str) or len(description) > 1000:
                raise ValueError("Descripcion invalida (maximo 1000 caracteres)")
        except ValueError as exc:
            return self.send_json(400, {"error": str(exc)})
        ticket = {
            "id": str(uuid.uuid4()), "titulo": title.strip(), "categoria": category,
            "descripcion": description, "creado_en": utc_now(),
        }
        result = None
        failures = []
        for worker in self.server.next_workers():
            try:
                # Estrategia de reintento sobre otro nodo, acotada a N nodos.
                result = call_json(worker + "/process", ticket, timeout=8)
                break
            except (HTTPError, URLError, TimeoutError, OSError, ValueError) as exc:
                failures.append(f"{worker}: {type(exc).__name__}")
        if result is None:
            return self.send_json(503, {"error": "Todos los nodos estan indisponibles", "intentos": failures})
        ticket.update({"estado": result["estado"], "cola": result["cola"], "nodo": result["nodo"]})
        try:
            self.server.store.add(ticket)
        except sqlite3.Error:
            return self.send_json(500, {"error": "Error de persistencia"})
        event = {"tipo": "ticket_creado", "ticket_id": ticket["id"],
                 "categoria": ticket["categoria"], "nodo": ticket["nodo"], "creado_en": ticket["creado_en"]}
        # Observer: si falla el receptor, la petición se confirma igualmente.
        try:
            call_json(self.server.observer_url + "/events", event, timeout=0.8)
        except (HTTPError, URLError, TimeoutError, OSError, ValueError):
            with self.server.lock:
                self.server.observer_errors += 1
        return self.send_json(201, ticket)


def main():
    p = argparse.ArgumentParser(description="Gateway SpawnTech")
    p.add_argument("--port", type=int, default=8000)
    p.add_argument("--workers", default="http://127.0.0.1:8101,http://127.0.0.1:8102")
    p.add_argument("--observer", default="http://127.0.0.1:8200")
    p.add_argument("--db", default="spawntech.db")
    args = p.parse_args()
    workers = [x.strip().rstrip("/") for x in args.workers.split(",") if x.strip()]
    if not workers:
        p.error("Se requiere al menos un worker")
    server = GatewayServer(("127.0.0.1", args.port), GatewayHandler, workers, args.observer, args.db)
    print(f"[Gateway] http://127.0.0.1:{args.port} --> {workers}", flush=True)
    try:
        server.serve_forever(poll_interval=0.2)
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
