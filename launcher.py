"""Arranque persistente de la demostración: Ctrl+C detiene los nodos."""
import argparse
import time
from cluster import Cluster
from common import call_json


def main():
    p = argparse.ArgumentParser(description="Iniciar demo de SpawnTech Nexus")
    p.add_argument("--workers", type=int, choices=(1, 2), default=2)
    p.add_argument("--port", type=int, default=8000)
    p.add_argument("--delay", type=float, default=0.12)
    args = p.parse_args()
    with Cluster(n_workers=args.workers, base=args.port, delay=args.delay, keep_db=True) as cluster:
        print("SpawnTech Nexus en funcionamiento")
        print("API:", cluster.gateway_url)
        print("Observador:", cluster.observer_url + "/events")
        print("Datos guardados en spawntech.db (SQLite)")
        print("Prueba POST con el ejemplo del README. Ctrl+C para detener.")
        try:
            while True:
                # Estado simple que permite advertir si el gateway se cae.
                time.sleep(1)
                if not call_json(cluster.gateway_url + "/health", timeout=1).get("ok"):
                    break
        except KeyboardInterrupt:
            print("Deteniendo servicios...")


if __name__ == "__main__":
    main()
