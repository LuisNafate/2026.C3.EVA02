# Entregables Oficiales de la Práctica EVA02
## Catálogo de Artefactos de Código, Datos, Evidencias y Reporte Técnico

---

> **Referencia Académica:** Bases de Datos en la Nube (IT2iD) · Evaluación `2026.C3.EVA02`  
> **Contrato de Calificación:** La entrega se compone de cuatro ejes indivisibles: (1) Repositorio de código y scripts reproducibles, (2) Dataset de mediciones en CSV homogéneo, (3) Evidencias de fallos y contención (logs/capturas), y (4) Reporte técnico estructurado en 7 secciones.

---

## 1. Repositorio de Código y Scripts

Todos los scripts deben estar parametrizados, documentados y ser completamente reproducibles por cualquier evaluador en un entorno con Docker.

### 1.1. `docker-compose.yml`
* **Propósito:** Orquestar los motores de bases de datos y la pila de observabilidad bajo los perfiles de contención cgroups v2.
* **Servicios requeridos:**
  1. `mongodb`: Imagen oficial `latest-stable` (WiredTiger, sin sharding).
  2. `postgres`: Imagen oficial `latest-stable` (PostgreSQL con JSONB).
  3. `prometheus`: Imagen `prom/prometheus`, con `scrape_interval: 1s` para capturar picos y micro-ráfagas.
  4. `cadvisor`: Imagen `gcr.io/cadvisor/cadvisor`, montando `/sys/fs/cgroup` para extraer métricas de cgroups v2 por contenedor.
  5. `node-exporter`: Imagen `prom/node-exporter`, para monitorear métricas del host (I/O, disco, swap).
* **Parámetros cgroups v2 a implementar:**
  - `PROFILE_A_BASELINE`: `cpus: 4.0`, `memory: 4096m`, `mem_swappiness: 0`.
  - `PROFILE_B_MEDIUM`: `cpus: 2.0`, `memory: 2048m`, `mem_swappiness: 0`.
  - `PROFILE_C_SEVERE`: `cpus: 1.0`, `memory: 1024m`, `mem_swappiness: 0` (fuerza throttling activo de CFS).

---

### 1.2. `synthetic_data_generator.py`
* **Propósito:** Generar e insertar masivamente el conjunto de datos de 500 000 órdenes de compra JSON anidadas.
* **Requerimientos de datos:**
  - **Volumen:** Exactamente 500 000 documentos.
  - **Estructura:** ~3 niveles de anidamiento, promedio 3 items por orden.
  - **Campos indispensables:**
    - `order_id`: Identificador UUID válido.
    - `timestamp`: Formato ISO-8601 UTC (con rango que cubra fechas previas y posteriores a `2026-01-01T00:00:00Z`).
    - `customer`: Objeto con `id`, `tier`, `segment`, `geo` (`country`, `state`, `city`, `zip`, `coordinates`).
    - `items`: Arreglo de objetos con `sku`, `category`, `brand`, `qty`, `price`, `tax_pct`, `discounts`.
    - `payment`: Objeto con `method`, `status` (`completed`, `pending`, `failed`, `refunded`), `transaction_id`, `gateway_latency_ms`, `totals`, `final_total`.
    - `metadata`: Objeto con `channel`, `user_agent`, `session_id`, `flags`.
* **Indexación que el script debe aplicar tras la carga:**
  - **MongoDB:**
    ```javascript
    db.orders.createIndex({ "timestamp": 1 });
    db.orders.createIndex({ "order_id": 1 });
    ```
  - **PostgreSQL:**
    ```sql
    ALTER TABLE orders ADD PRIMARY KEY (id);
    CREATE INDEX idx_orders_timestamp ON orders (((data->>'timestamp')::timestamptz));
    ```

---

### 1.3. `benchmark_runner` (k6 o Python multiproceso)
* **Propósito:** Generador de carga y cliente de benchmarking que simula las sesiones concurrentes y calcula las métricas de rendimiento por consulta.
* **Requerimientos operativos:**
  - Soportar niveles de concurrencia: **1, 10 y 50 clientes simultáneos**.
  - Control de ventanas temporales:
    - Warm-up de **60 segundos** (no se registran métricas).
    - Medición de **300 segundos** (recolección activa de latencias individuales).
    - Cooldown de **60 segundos** (estabilización).
  - Cálculo estadístico al término de la ventana:
    - `throughput_qps`: Consultas totales exitosas divididas entre 300 segundos.
    - `latency_p50_ms`: Mediana exacta de los tiempos de respuesta.
    - `latency_p95_ms`: Percentil 95 de tiempo de respuesta.
    - `latency_p99_ms`: Percentil 99 de tiempo de respuesta (*tail latency*).

---

### 1.4. Directorio `queries/`
Contiene los archivos de consulta desacoplados para ambos motores:
* `queries/q1_mongodb.js`: Pipeline de desanidamiento (`$unwind`), filtrado (`$match: price > 50`) y agrupamiento (`$group: country, category`).
* `queries/q1_postgres.sql`: Consulta SQL con `jsonb_array_elements`, filtro numérico y `GROUP BY 1, 2`.
* `queries/q2_mongodb.js`: Pipeline de filtrado por estado y fecha, ordenamiento masivo (`$sort: payment.final_total: -1`) y `$limit: 1000`.
* `queries/q2_postgres.sql`: Consulta SQL con filtro, `ORDER BY (data->'payment'->>'final_total')::numeric DESC LIMIT 1000`.

---

### 1.5. `run_benchmarks.sh`
* **Propósito:** Script orquestador maestro en Bash que automatiza la ejecución desatendida de la matriz completa.
* **Funciones que debe cumplir:**
  1. Iterar a través de las combinaciones: Motor $\times$ Perfil $\times$ Consulta $\times$ Concurrencia (36 celdas).
  2. Ejecutar 3 repeticiones independientes por celda (108 corridas en total).
  3. Ejecutar el vaciado de caché del kernel del host antes de cada corrida:
     ```bash
     sync; echo 3 > /proc/sys/vm/drop_caches
     ```
  4. Iniciar el runner de benchmarking (warmup 60s + test 300s + cooldown 60s).
  5. Consultar las APIs de Prometheus al finalizar cada corrida para extraer:
     - Segundos acumulados de `container_cpu_cfs_throttled_seconds_total`.
     - Pico máximo de memoria `container_memory_rss_bytes` (convertido a MB).
  6. Detectar eventos de `disk_spill` y `oom_killed`.
  7. Formatear y anexar inmediatamente la fila al archivo CSV de resultados.

---

## 2. Esquema CSV de Mediciones (Estricto)

> [!CAUTION]
> **PROHIBICIÓN ESTRICTA:** No renombrar, no eliminar, no reordenar ni agregar columnas adicionales. El esquema CSV es un estándar inalterable que permite la concatenación masiva de resultados entre diferentes equipos evaluados.

### 2.1. Cabecera Oficial
```csv
timestamp_epoch,engine,profile,query_id,concurrency,run_number,throughput_qps,latency_p50_ms,latency_p95_ms,latency_p99_ms,cpu_throttled_seconds,max_rss_mb,disk_spill,status
```

### 2.2. Diccionario de Datos del CSV
| # | Columna | Tipo | Valores Válidos / Ejemplo | Descripción |
|---|---|---|---|---|
| 1 | `timestamp_epoch` | Entero (int64) | `1774880400` | Timestamp UNIX en segundos al inicio de la corrida de medición. |
| 2 | `engine` | Cadena | `mongodb` \| `postgresql` | Motor de base de datos evaluado. |
| 3 | `profile` | Cadena | `PROFILE_A_BASELINE` \| `PROFILE_B_MEDIUM` \| `PROFILE_C_SEVERE` | Perfil de recursos cgroups v2 asignado al contenedor. |
| 4 | `query_id` | Cadena | `Q1` \| `Q2` (o variantes `Q2_allowDiskUse_false`, etc.) | Identificador de la consulta evaluada. |
| 5 | `concurrency` | Entero | `1` \| `10` \| `50` | Número de clientes / hilos simultáneos generando carga. |
| 6 | `run_number` | Entero | `1` \| `2` \| `3` | Número secuencial de la repetición dentro de la misma celda. |
| 7 | `throughput_qps` | Flotante | `142.35` | Consultas exitosas por segundo durante los 300 segundos. |
| 8 | `latency_p50_ms` | Flotante | `6.82` | Latencia percentil 50 (mediana) en milisegundos. |
| 9 | `latency_p95_ms` | Flotante | `18.45` | Latencia percentil 95 en milisegundos. |
| 10 | `latency_p99_ms` | Flotante | `45.12` | Latencia percentil 99 (latencia de cola) en milisegundos. |
| 11 | `cpu_throttled_seconds` | Flotante | `12.40` | Segundos totales que el kernel estranguló la CPU durante la prueba. |
| 12 | `max_rss_mb` | Flotante | `845.20` | Pico máximo de memoria física residente (RSS) en megabytes. |
| 13 | `disk_spill` | Booleano | `true` \| `false` | Indica si el motor volcó datos a disco temporal (sort/hash). |
| 14 | `status` | Cadena | `ok` \| `spill` \| `oom` \| `error` | Estado final de la prueba. |

---

## 3. Evidencias Complementarias Requeridas

Para respaldar la validez científica de los datos del CSV se deben adjuntar:
1. **Evidencias de Disk Spill:**
   - En MongoDB: Logs del servidor donde WiredTiger o la etapa `$sort` reporte volcado a archivos temporales, o error si `allowDiskUse: false`.
   - En PostgreSQL: Salida del log o de `EXPLAIN (ANALYZE, BUFFERS)` indicando `Sort Method: external merge  Disk: xxxkB`.
2. **Evidencias de Out-Of-Memory (OOM):**
   - Logs de Docker o de `dmesg` mostrando la invocación del `oom-killer` al exceder el límite de memoria asignado.
3. **Evidencias de CPU Throttling:**
   - Gráfica o captura de Prometheus mostrando el crecimiento de `container_cpu_cfs_throttled_seconds_total` en `PROFILE_C_SEVERE`.

---

## 4. Reporte Técnico de Métricas (7 Secciones Obligatorias)

El documento final debe desarrollarse en formato Markdown o PDF estructurado rigurosamente en las 7 secciones siguientes:

### Sección 1: Especificaciones del Host y del Entorno Docker
- Detalle del procesador (modelo, número de núcleos físicos y lógicos, frecuencia base y boost).
- Memoria RAM física total y tecnología (DDR4/DDR5).
- Tipo de almacenamiento utilizado para los datos de Docker (NVMe PCIe, SSD SATA o HDD).
- Sistema operativo base, versión de WSL2 / kernel Linux y versión de Docker Engine.
- Versiones exactas y parámetros de configuración por defecto de MongoDB y PostgreSQL.

### Sección 2: Método de Medición y Verificación del Baseline
- Justificación del diseño experimental y del protocolo de ciclo de vida (flush de caché, 60s warmup, 300s test, 60s cooldown).
- Verificación empírica de que el baseline (`PROFILE_A_BASELINE`) opera sin contención de CPU y sin estrangulamiento.
- Demostración de que ambos motores procesaron exactamente los mismos 500 000 documentos sintéticos.

### Sección 3: Resultados Consolidados (Throughput, P95/P99, Tiempo de Throttling)
- Tablas consolidadas que resuman las 36 celdas utilizando la media y mediana de las 3 repeticiones.
- Comparativa lado a lado: MongoDB vs PostgreSQL para Q1 y Q2 en los tres perfiles (A, B y C) y en las tres concurrencias (1, 10 y 50).
- Análisis de la variabilidad entre las repeticiones (desviación estándar / estabilidad de la medición).

### Sección 4: Análisis Gráfico
Se deben incluir obligatoriamente tres análisis visuales de alto impacto:
1. **P99 vs. Concurrencia:** Gráfica de líneas que muestre cómo la cola de latencia (P99) escala al pasar de 1 a 10 y 50 clientes en cada perfil.
2. **CFS Throttling vs. Throughput (QPS):** Gráfica de dispersión o barras que demuestre la correlación directa entre los segundos de CPU estrangulada y la caída de rendimiento.
3. **Curva de Memoria RSS:** Gráfica temporal mostrando la evolución de `container_memory_rss_bytes` durante la ejecución de Q2, contrastando el comportamiento con y sin volcado a disco.

### Sección 5: Planes de Ejecución
- Desglose y contraste técnico de los planes de consulta:
  - MongoDB: `db.orders.explain("executionStats").aggregate(...)`
  - PostgreSQL: `EXPLAIN (ANALYZE, BUFFERS, VERBOSE) SELECT ...`
- Análisis detallado de los cuellos de botella:
  - En Q1: Costo del desanidamiento (`$unwind` vs `jsonb_array_elements`) y acumulación en memoria para el agrupamiento.
  - En Q2: Comparación entre ordenamiento en memoria (*quicksort/top-N heapsort*) y ordenamiento externo en disco (*external merge disk sort*).

### Sección 6: Interpretación: Límites de Memoria, Volcado a Disco y Throttling de cgroups
- Explicación de cómo actúa el Completely Fair Scheduler (CFS) de Linux al recortar las cuotas de tiempo de CPU.
- Comparativa de la arquitectura de gestión de memoria: WiredTiger Cache (50% de RAM - 1GB) frente al modelo por conexión de PostgreSQL (`work_mem`).
- Discusión sobre qué motor resiste mejor la escasez de recursos antes de degradar o abortar.

### Sección 7: Recomendaciones Técnicas para Despliegues Documentales en la Nube
- Guía para arquitectos de software e ingenieros cloud:
  - ¿Cuándo conviene almacenar JSON en PostgreSQL y cuándo utilizar MongoDB nativo?
  - Recomendaciones sobre la asignación de vCPUs en Kubernetes / AWS ECS / Google Cloud Run para prevenir el "throttling cliff".
  - Buenas prácticas para dimensionamiento de buffers de ordenamiento y mitigación de latencias de cola (P99).

---

## 5. Checklist de Preguntas del Revisor (Criterio de Evaluación)

Antes de considerar terminada la entrega, verifica que el proyecto responda satisfactoriamente a las 6 preguntas clave de revisión:

| # | Pregunta del Revisor | Evidencia Requerida en la Entrega |
|---|---|---|
| **1** | ¿El baseline es comparable (mismo dataset, mismas queries)? | Demostrado en Sección 2 con verificación de conteo de 500k registros y esquemas equivalentes. |
| **2** | ¿Las latencias reportan P50, P95 y P99 o solo promedios? | Demostrado en Sección 3 y en las columnas `latency_p50_ms`, `latency_p95_ms` y `latency_p99_ms` del CSV. |
| **3** | ¿Hubo throttling CFS y cuántos segundos se acumularon? | Demostrado con los datos de Prometheus en la columna `cpu_throttled_seconds` y la gráfica de la Sección 4. |
| **4** | ¿Ocurrió spill a disco o OOM? ¿En qué perfil y concurrencia? | Demostrado con las columnas `disk_spill` y `status`, capturas de logs y análisis en la Sección 6. |
| **5** | ¿Cuántas repeticiones se realizaron y cómo se resumieron? | Demostrado mediante las 3 corridas registradas en el CSV (`run_number: 1, 2, 3`) y tablas con media/mediana en Sección 3. |
| **6** | ¿El plan de ejecución respalda el cuello de botella observado? | Demostrado en la Sección 5 mediante el contraste de `executionStats` y `EXPLAIN ANALYZE BUFFERS`. |
