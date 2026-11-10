"""Prueba empírica: un nodo frente a dos, y tolerancia a fallos."""
import argparse
import json
import math
import platform
import statistics
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from cluster import Cluster
from common import call_json

ROOT = Path(__file__).resolve().parent


def percentile(items, p):
    items = sorted(items)
    idx = (len(items) - 1) * p / 100
    low = math.floor(idx)
    high = math.ceil(idx)
    return items[low] + (items[high] - items[low]) * (idx - low)


def submit(url, idx):
    payload = {"titulo": f"Solicitud de prueba {idx}",
               "categoria": "soporte" if idx % 2 == 0 else "desarrollo",
               "descripcion": "Clasificacion y enrutamiento de solicitud de ejemplo"}
    started = time.perf_counter()
    try:
        result = call_json(url + "/tickets", payload, timeout=15)
        return {"ok": result.get("estado") == "en_cola_de_atencion",
                "nodo": result.get("nodo"), "tiempo_ms": (time.perf_counter() - started) * 1000,
                "ticket_id": result.get("id")}
    except Exception as exc:
        return {"ok": False, "error": str(exc), "tiempo_ms": (time.perf_counter() - started) * 1000}


def load(url, n, concurrency):
    started = time.perf_counter()
    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = [executor.submit(submit, url, i) for i in range(n)]
        results = [f.result() for f in as_completed(futures)]
    seconds = time.perf_counter() - started
    times = [x["tiempo_ms"] for x in results]
    passed = sum(x["ok"] for x in results)
    distribution = {}
    for result in results:
        if result.get("nodo"):
            distribution[result["nodo"]] = distribution.get(result["nodo"], 0) + 1
    return {"solicitudes": n, "concurrencia_clientes": concurrency, "exitos": passed,
            "errores": n - passed, "duracion_seg": round(seconds, 3),
            "throughput_solicitudes_seg": round(passed / seconds, 2),
            "latencia_p50_ms": round(statistics.median(times), 2),
            "latencia_p95_ms": round(percentile(times, 95), 2),
            "por_nodo": distribution}


def evaluate(n=48, concurrency=12):
    result = {"proyecto": "SpawnTech Nexus", "fecha_utc": datetime.now(timezone.utc).isoformat(),
              "entorno": {"python": sys.version.split()[0], "so": platform.platform(),
                          "red": "localhost/loopback (mismo equipo)",
                          "tiempo_simulado_por_tarea_ms": 120,
                          "hilos_activos_max_por_worker": 2},
              "metodologia": "Pruebas secuenciales con 48 peticiones, 12 clientes concurrentes, una pasada por escenario. No generalizable a producción."}
    for n_workers, base, tag in [(1, 18600, "un_nodo"), (2, 18700, "dos_nodos")]:
        with Cluster(n_workers=n_workers, base=base) as cluster:
            for i in range(4):
                submit(cluster.gateway_url, 1000+i)
            result[tag] = load(cluster.gateway_url, n, concurrency)
            events = call_json(cluster.observer_url + "/events")
            result[tag]["eventos_registrados_incluido_calentamiento"] = events["cantidad"]
    with Cluster(n_workers=2, base=18800) as cluster:
        # Intentos al primer nodo deben reenrutarse si este deja de responder.
        cluster.stop_service("nodo-1")
        failover = load(cluster.gateway_url, 12, 6)
        result["fallo_nodo_A"] = failover
        cluster.stop_service("observador")
        test = submit(cluster.gateway_url, 2000)
        result["fallo_observador"] = {"ticket_creado": test["ok"],
                                       "fallos_observador_contabilizados": call_json(cluster.gateway_url + "/stats")["fallos_observador"]}
        result["validacion"] = {"ticket_valido": test["ok"],
                                 "persistido": bool(call_json(cluster.gateway_url + "/tickets/" + test["ticket_id"]).get("id")) if test.get("ticket_id") else False}
    before = result["un_nodo"]["throughput_solicitudes_seg"]
    after = result["dos_nodos"]["throughput_solicitudes_seg"]
    result["mejora_throughput_pct"] = round(100 * (after - before) / before, 1) if before else None
    return result


def main():
    p = argparse.ArgumentParser(description="Evaluacion reproducible del prototipo")
    p.add_argument("--requests", type=int, default=48)
    p.add_argument("--concurrency", type=int, default=12)
    p.add_argument("--output", default="pruebas/resultados_reales.json")
    args = p.parse_args()
    out = evaluate(args.requests, args.concurrency)
    output_path = ROOT / args.output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(out, indent=2, ensure_ascii=False))
    print(f"\nResultados guardados en {output_path}")


if __name__ == "__main__":
    main()
