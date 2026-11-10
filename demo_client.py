"""Cliente de demostración portátil (Windows/macOS/Linux) sin curl."""
import json
from common import call_json


def show(title, data):
    print("\n=== " + title + " ===")
    print(json.dumps(data, ensure_ascii=False, indent=2))


def main():
    url = "http://127.0.0.1:8000"
    examples = [
        {"titulo": "Mi computador no enciende", "categoria": "soporte", "descripcion": "Solicitud de diagnóstico técnico"},
        {"titulo": "Página web para un negocio", "categoria": "desarrollo", "descripcion": "Cotización de desarrollo de software"},
    ]
    try:
        for item in examples:
            show("Nuevo ticket", call_json(url + "/tickets", item))
        show("Estadísticas", call_json(url + "/stats"))
        show("Eventos", call_json("http://127.0.0.1:8020/events"))
    except OSError:
        print("No fue posible conectar. Primero ejecuta: python launcher.py --workers 2")


if __name__ == "__main__":
    main()
