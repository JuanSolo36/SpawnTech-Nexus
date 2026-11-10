"""Utilidades HTTP/JSON reutilizadas por los nodos de SpawnTech Nexus."""
import json
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler
from urllib.request import Request, urlopen


def utc_now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def call_json(url, payload=None, timeout=5):
    """Petición HTTP JSON. Lanza URLError/HTTPError si hay un problema."""
    body = None if payload is None else json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = Request(url, data=body, headers={"Content-Type": "application/json"},
                      method="POST" if payload is not None else "GET")
    with urlopen(request, timeout=timeout) as response:
        raw = response.read()
        return json.loads(raw.decode("utf-8")) if raw else {}


class JsonHandler(BaseHTTPRequestHandler):
    server_version = "SpawnTechNexus/1.0"

    def log_message(self, fmt, *args):
        # Reducir ruido en pruebas de carga, dejando errores estructurados a nivel de servicio.
        pass

    def send_json(self, status, data):
        raw = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        try:
            self.wfile.write(raw)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def read_json(self, max_size=16384):
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError as exc:
            raise ValueError("Content-Length invalido") from exc
        if length <= 0 or length > max_size:
            raise ValueError("Cuerpo vacio o mayor a 16 KiB")
        try:
            return json.loads(self.rfile.read(length).decode("utf-8"))
        except (UnicodeError, json.JSONDecodeError) as exc:
            raise ValueError("JSON invalido") from exc
