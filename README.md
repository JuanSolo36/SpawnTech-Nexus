# SpawnTech Nexus — Mini proyecto Arquitectura de Software (Unidad 2)

**Emprendimiento:** SpawnTech. **Contexto:** desarrollo de software y soporte técnico. **Modalidad:** trabajo individual (sujeto a autorización del docente, dado que la guía solicita 4–5 personas).

## Alcance real

Es un **prototipo educativo de arquitectura distribuida lógica**. Crea procesos HTTP independientes en `127.0.0.1`, pero **todos se ejecutan en una sola máquina**, no en proveedores cloud. Las peticiones representan registro, clasificación y encolamiento simulado; **no reparan equipos ni desarrollan software automáticamente**. `http.server` no está recomendado para producción y la API no trae autenticación, cifrado TLS, cola durable ni auditoría persistente.

## Arquitectura y patrones

- **Gateway / Mediator / Proxy:** `gateway.py`, puerto 8000, valida peticiones, round-robin, reintento en otro nodo, persiste tickets en SQLite.
- **Nodo A:** `worker.py`, puerto 8011, procesamiento simulado concurrente (máximo 2 tareas activas).
- **Nodo B:** `worker.py`, puerto 8012, igual al anterior.
- **Observer:** `events.py`, puerto 8020, registra eventos HTTP en memoria. Es una implementación simplificada de publicación-notificación: un observador conocido, **no un bus publish/subscribe completo**.
- **Persistencia:** SQLite local, compartida únicamente a través del Gateway (no es una base de datos distribuida).

Los puertos cambian si se usa `--port` en `launcher.py` (base + 11, base + 12, base + 20).

## Requisitos

Python 3.10 o superior. No requiere `pip install`.

## Iniciar

Desde la carpeta del proyecto:

```bash
python launcher.py --workers 2
```

En otra consola, registrar un ticket:

```bash
curl -X POST http://127.0.0.1:8000/tickets \
  -H "Content-Type: application/json" \
  -d '{"titulo":"Mi PC no inicia","categoria":"soporte","descripcion":"Cliente solicita diagnóstico"}'
```

Otro ejemplo para desarrollo de software:

```bash
curl -X POST http://127.0.0.1:8000/tickets \
  -H "Content-Type: application/json" \
  -d '{"titulo":"Sitio web empresarial","categoria":"desarrollo","descripcion":"Cliente solicita cotización"}'
```

Consultar resultados:

```bash
curl http://127.0.0.1:8000/tickets
curl http://127.0.0.1:8000/stats
curl http://127.0.0.1:8020/events
```

Pulsar `Ctrl+C` para detener los servicios.

## Reproducir pruebas

```bash
python -m unittest discover -s pruebas -p 'test_*.py' -v
python benchmark.py
```

El segundo comando **mide de nuevo** en tu equipo y reemplaza `pruebas/resultados_reales.json`. Cada ambiente producirá cifras distintas; el informe se basó en la ejecución registrada al generarse estos archivos.

El benchmark compara 48 peticiones con 12 clientes simultáneos en escenarios de 1 y 2 nodos. Además, detiene el nodo A y verifica reintentos; después detiene el observador y comprueba que los tickets aún puedan confirmarse, aunque el evento se pierde.

## Demo para el video

1. Mostrar `arquitectura/componentes.puml`, `secuencia.puml` y `despliegue.puml` junto a los PNG del informe.
2. Ejecutar `python launcher.py --workers 2`.
3. Enviar ambos ejemplos `curl` y consultar `/tickets`, `/stats` y `/events`.
4. Detener la demo y ejecutar `python benchmark.py` para exhibir métricas reales.
5. Explicar la diferencia entre nodos lógicos en localhost y un despliegue cloud real.

## Repositorio y entrega

1. Crear un repositorio **propio** en GitHub o GitLab y subir los archivos de este paquete. No existe enlace al repositorio hasta que tú lo publiques.
2. Grabar video de 12–15 minutos usando `docs/guion_video.md` y `SpawnTech_Nexus_Presentacion.pptx`.
3. Subir a YouTube con visibilidad **No listado** (no confundir con "Privado", que requiere permisos a cada espectador).
4. Completar los campos de portada y los enlaces de video y repositorio en el PDF antes de entregar por LMS.

## Límites y mejoras antes de un uso comercial

El sistema no tiene autenticación/autorización, API TLS, idempotencia persistente, observador con entrega durable, colas reales, monitorización profesional, recuperación de SQLite ni despliegue multinodo real. Para producción se recomienda FastAPI con Uvicorn/Gunicorn, PostgreSQL, un broker de mensajes (p. ej. RabbitMQ), tracing, IAM, HTTPS, contenedores y pruebas en diferentes máquinas.

### Alternativa sin curl (Windows, macOS y Linux)

Con los servicios activos, ejecuta `python demo_client.py`. El script crea dos solicitudes, consulta estadísticas y lista eventos usando únicamente Python.
