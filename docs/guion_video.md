# SpawnTech Nexus — Guion para video de 12 a 15 minutos

**Duración prevista:** 14 minutos. **Presenta:** [Tu nombre completo]. **Trabajo individual sujeto a autorización del docente.**

**Preparación para grabar:** abre la presentación `SpawnTech_Nexus_Presentacion.pptx` y dos terminales en la carpeta del proyecto. Prueba antes `python launcher.py --workers 2` y `python demo_client.py`. Detén la demo y graba desde el comienzo. No muestres información privada de clientes. Si el computador está lento, el benchmark puede tomar más tiempo; ajusta la duración de otras secciones.

## 00:00–00:55 | Diapositiva 1: Portada

«Buen día. Presento el mini proyecto de la Unidad 2 de Arquitectura de Software, titulado SpawnTech Nexus: arquitectura distribuida para gestionar solicitudes de soporte técnico y desarrollo de software. SpawnTech es mi emprendimiento de tecnología, en el cual trabajo de manera individual. Por esa razón, yo asumí las responsabilidades de planificación, diseño arquitectónico, desarrollo de código, pruebas y presentación. Este trabajo tiene enfoque académico y busca mostrar cómo distribuir la atención de solicitudes en varios procesos independientes, medir el comportamiento y analizar decisiones arquitectónicas. La ejecución se realiza en un solo computador usando localhost, lo cual sirve para estudiar los nodos lógicos, pero no debe confundirse con un despliegue físico en la nube».

## 00:55–02:00 | Diapositiva 2: Problema empresarial

«SpawnTech presta servicios de soporte técnico y desarrollo de software. Si cada solicitud llega a una sola aplicación sin una arquitectura definida, con el crecimiento pueden aparecer problemas de organización, saturación y disponibilidad. Por ejemplo, mientras un cliente solicita ayuda con su computador, otro puede necesitar una página web, un sistema de ventas o mantenimiento de una aplicación. Mi solución no automatiza esas tareas especializadas, sino que organiza y clasifica las solicitudes en dos tipos: soporte y desarrollo. Me interesaba que el sistema fuera capaz de recibir varias peticiones, asignarlas entre nodos de procesamiento y dejar evidencia consultable. La pregunta principal fue: ¿cómo separar las responsabilidades de los componentes y qué sucede con el rendimiento cuando aumento el número de procesadores?»

## 02:00–02:55 | Diapositiva 3: Objetivos y alcance

«El objetivo general es diseñar, implementar y evaluar una arquitectura distribuida lógica para SpawnTech, usando UML y patrones de diseño. Los objetivos específicos fueron levantar requisitos, elaborar diagramas de componentes, secuencia y despliegue, programar un prototipo concurrente y verificar su respuesta ante cargas y fallos. El alcance es deliberadamente pequeño para poder defender todas las decisiones y el código como único participante. Utilicé Python, comunicación HTTP y JSON, almacenamiento SQLite y herramientas de prueba automatizada. No he implementado cuentas de usuario, facturación, gestión real de proyectos ni reparación de equipos: esas funcionalidades corresponderían a una versión comercial futura».

## 02:55–04:15 | Diapositiva 4: Arquitectura general

«En la arquitectura hay cinco responsabilidades. El cliente envía su solicitud; el Gateway recibe y valida; los procesadores A y B clasifican la petición y definen una cola lógica de trabajo; SQLite guarda el registro; y un observador almacena un evento de que el ticket fue creado. El Gateway realiza la selección de procesador por turnos, conocida como round-robin. Los procesadores son servicios HTTP que se ejecutan de manera separada y escuchan en puertos diferentes. La aplicación conserva el mismo identificador cuando debe intentar otro nodo. Esta separación facilita la incorporación de nuevos componentes, aunque también deja claro un compromiso: el Gateway y la base SQLite siguen siendo puntos centrales en esta versión».

## 04:15–05:10 | Diapositiva 5: UML de componentes

«El diagrama de componentes representa las dependencias funcionales. El actor Cliente SpawnTech conoce únicamente el Gateway. No tiene que saber en qué puerto funciona el procesador A o el B. El Gateway es un punto de entrada y de coordinación, se conecta con cada procesador, guarda información en el repositorio y notifica al observador. El diseño hace visible la separación de responsabilidades y permite argumentar cómo reducir el acoplamiento entre el cliente y los servicios internos. Este diagrama está incluido como imagen en el PDF y también como código PlantUML para editarlo».

## 05:10–06:20 | Diapositiva 6: UML de secuencia

«El diagrama de secuencia explica el orden de interacción en el tiempo. Primero el cliente envía un POST con título y categoría. El Gateway valida el contenido y genera un UUID. Luego intenta delegar la petición. Si el primer procesador responde, recibe el resultado; si no responde, el Gateway intenta otro nodo disponible con el mismo identificador. Cuando se obtiene un resultado, la solicitud se guarda en SQLite. Finalmente se envía un evento y se confirma al cliente con un código HTTP 201. El proceso de notificación es de mejor esfuerzo: si el observador está apagado, el Gateway aumenta un contador de error y el ticket permanece guardado. Esta limitación se describe explícitamente en el informe».

## 06:20–07:10 | Diapositiva 7: UML de despliegue

«En el diagrama de despliegue se ven las ubicaciones reales de la prueba. El Gateway funciona en el puerto 8000, los procesadores en 8011 y 8012 y el observador en 8020. Todos son procesos independientes de Python que corren en la misma máquina y se comunican por la interfaz de loopback 127.0.0.1. Esta simulación evidencia interacción de nodos lógicos y llamadas de red entre procesos, pero no constituye tolerancia a la falla de toda la máquina ni balanceo geográfico. Para pasar a producción se necesitarían máquinas o contenedores de red distintos, certificados HTTPS y un almacenamiento apropiado».

## 07:10–08:25 | Diapositiva 8: Patrones seleccionados

«Apliqué el patrón Proxy porque el Gateway actúa como acceso controlado a los procesadores. El patrón Mediator aparece cuando el Gateway decide cómo coordinar los componentes y a cuál de ellos entregar trabajo. Implementé una versión simplificada de Observer: después de crear el ticket, un servicio recibe un evento HTTP separado para su seguimiento. Además agregué una estrategia de reintento sobre otro nodo cuando se pierde la comunicación con el primero. Estos patrones ayudan a razonar sobre mantenibilidad, tolerancia parcial a fallos y desacoplamiento. Pero hay límites importantes: no hay un broker de mensajes y no implementé un circuit breaker completo; sería incorrecto afirmar que el sistema entrega eventos de forma garantizada».

## 08:25–09:05 | Diapositiva 9: Hilos y concurrencia

«Los servidores HTTP usan hilos para atender varias conexiones. Cada procesador tiene un semáforo que limita a dos los trabajos activos simultáneos. En la simulación, un trabajo toma aproximadamente 120 milisegundos. Si llegan más solicitudes, los hilos adicionales esperan por una plaza del semáforo. Así se puede observar de forma controlada cómo la capacidad de un nodo limita la productividad. Para proteger la asignación round-robin y las operaciones sobre la base de datos se usan bloqueos o locks, evitando cambios simultáneos no coordinados en esos elementos compartidos».

## 09:05–11:30 | Diapositiva 10: Demostración práctica (compartir pantalla de terminal)

«Ahora ejecutaré el prototipo. En la primera terminal escribo `python launcher.py --workers 2`. Aparecen las direcciones de la API y el observador. En la segunda terminal escribo `python demo_client.py`. Este programa genera dos solicitudes de ejemplo. La primera solicita soporte para un computador que no enciende; la segunda solicita desarrollo de una página web. En la respuesta observo que cada ticket tiene un identificador, un estado de encolamiento y un nodo que lo procesó. También se muestran las estadísticas y los eventos. La lista confirma que las solicitudes se registraron y que ambos tipos de servicio siguen un flujo similar. Luego detengo los procesos con Ctrl+C. Si quiero consultar directamente la API, puedo usar las rutas GET /tickets y GET /stats. A continuación ejecuto `python -m unittest discover -s pruebas -v` para mostrar las cuatro pruebas automatizadas: categorías y persistencia, recepción de eventos, validación incorrecta y distribución entre nodos. Estas pruebas permiten verificar comportamientos específicos en lugar de depender únicamente de que la aplicación parezca funcionar».

*Acciones en pantalla: iniciar launcher, ejecutar demo_client, mostrar resultados; detener; ejecutar unittest. Si las pruebas se demoran, acelerarlas en edición sin afirmar un tiempo distinto.*

## 11:30–12:45 | Diapositiva 11: Evaluación y resultados

«También realicé una prueba controlada de rendimiento con 48 solicitudes y 12 clientes concurrentes. Con un nodo registré 16,44 solicitudes exitosas por segundo; con dos nodos llegué a 32,36. En este ensayo, el incremento fue de 96,8 %. La mediana de latencia pasó aproximadamente de 722 a 361 milisegundos. Además, detuve el proceso del nodo A y envié doce solicitudes: todas fueron procesadas por B. También detuve el observador y el ticket siguió registrándose, aunque la notificación se perdió. Estas cifras son resultados de una sola ejecución en un único computador y no predicen el comportamiento de una solución alojada en la nube. El archivo de resultados JSON permite repetir la prueba y contrastar los datos».

## 12:45–14:00 | Diapositiva 12: Conclusiones y cierre

«Como conclusión, SpawnTech Nexus me permitió comprender cómo los procesos, los hilos y las llamadas HTTP cooperan dentro de una arquitectura distribuida lógica. Los diagramas UML organizaron la solución antes de programar, y los patrones Proxy, Mediator y Observer simplificado ayudaron a separar responsabilidades. Las pruebas también demostraron que aumentar nodos puede mejorar la capacidad cuando los procesadores están limitados, y que el reintento ofrece cierta recuperación ante fallos parciales. La arquitectura sigue teniendo retos: seguridad, colas de eventos durables, eliminación de puntos únicos de fallo, monitoreo y despliegue en diferentes máquinas. Este proyecto representa un primer paso académico hacia una plataforma de atención más completa para SpawnTech. Muchas gracias».

---

## Checklist antes de publicar en YouTube

- Confirmar que el docente acepte la modalidad individual; si no, solicitar una alternativa de evaluación.
- Insertar nombre, institución, docente y fecha en la presentación y el PDF.
- Grabar pantalla y voz; mostrar al menos la demostración real del código y pruebas.
- Exportar a MP4 y comprobar que dure aproximadamente 12–15 minutos.
- Subir a YouTube con visibilidad **No listado**, copiar la URL, pegarla en el informe y el LMS.
- Crear tu repositorio GitHub o GitLab, subir los archivos, copiar el enlace y añadirlo al PDF/LMS.
