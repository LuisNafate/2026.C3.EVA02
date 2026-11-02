# Práctica Guiada: Medición de Métricas en Bases Documentales
## Contención de CPU y Memoria en Agregaciones JSON: MongoDB vs. PostgreSQL JSONB

---

> **Documento de Contexto y Especificación Oficial del Proyecto**  
> **Institución:** Universidad Politécnica de Chiapas (UPChiapas)  
> **Programa:** Ingeniería en Tecnologías de la Información e Innovación Digital (IT2iD)  
> **Materia:** Bases de Datos en la Nube · 2026  
> **Evaluación:** `2026.C3.EVA02`  
> **Fuentes Originales:** `playbook.pdf` y `playbook_sesion.pdf`  
> **Ubicación:** `contexto/INSTRUCCIONES_Y_CONTEXTO.md`  
> *Nota de consulta:* Este documento es el contrato oficial de especificación y requerimientos técnicos. Debe consultarse ante cualquier modificación arquitectural, de código, de scripts o de análisis de datos.

---

## 1. Objetivo General de la Práctica

Medir latencia, rendimiento (*throughput*) y huella de recursos al ejecutar agregaciones JSON anidadas bajo límites estrictos de CPU (*CFS throttling*) y memoria con Docker cgroups v2, comparando un motor puramente documental (**MongoDB**) con un motor relacional que almacena y procesa documentos anidados en JSONB (**PostgreSQL**).

> **Enfoque clave:** No se trata simplemente de "ver si arranca". Cada corrida produce métricas cuantificables y reproducibles (latencia P50/P95/P99, QPS, tiempos de throttling, consumo RSS, eventos de spill a disco y estabilidad OOM) consolidadas en un esquema de CSV homogéneo e inalterable.

---

## 2. Preguntas de Investigación / Métricas Clave

El experimento está formulado para responder de manera empírica a tres preguntas fundamentales:

| ID | Pregunta Guía | Foco de Evaluación |
|---|---|---|
| **M1** | ¿Cómo cambian la latencia P95 y P99 de las agregaciones sobre documentos anidados cuando se limita de forma estricta la CPU y la memoria? | Impacto de contención de hardware en colas de latencia de cola (*tail latency*). |
| **M2** | ¿Qué motor usa de forma más eficiente los buffers de ordenamiento y agrupamiento antes de volcar a disco temporal (*disk spill*) o fallar por falta de memoria (*OOM*)? | Comportamiento bajo saturación de memoria RAM y eficiencia de ordenamiento masivo / agregación. |
| **M3** | ¿Cuál es la huella de CPU y memoria por cada 1 000 documentos procesados en el motor documental frente al motor con JSONB? | Costo de procesamiento computacional y memoria por volumen normalizado de documentos. |

---

## 3. Motores Objetivo y Configuración de Datos

### 3.1. MongoDB
- **Versión:** `latest-stable`
- **Motor de almacenamiento:** `WiredTiger`
- **Modelo de datos:** Colección `orders` sin sharding.
- **Indexación obligatoria:**
  - Índice simple en `timestamp`
  - Índice simple en `order_id`

### 3.2. PostgreSQL
- **Versión:** `latest-stable`
- **Modelo de datos:** Tabla relacional `orders` con estructura:
  ```sql
  CREATE TABLE orders (
      id UUID PRIMARY KEY,
      data JSONB NOT NULL
  );
  ```
- **Indexación obligatoria:**
  - Llave primaria (PK) B-Tree implícita sobre `id`.
  - Índice B-Tree secundario sobre el campo `timestamp` extraído del objeto JSONB:
    ```sql
    CREATE INDEX idx_orders_timestamp ON orders (((data->>'timestamp')::timestamptz));
    ```

---

## 4. Perfiles de Recursos (Docker / cgroups v2)

Se definen tres perfiles de contención gestionados mediante cgroups v2 en Docker Compose:

| ID del Perfil | Nombre descriptivo | Límite de CPUs | Límite Memoria RAM | `mem_swappiness` | Propósito |
|---|---|---|---|---|---|
| `PROFILE_A_BASELINE` | Sin contención (Baseline) | `4.0` | `4096m` (4 GB) | `0` | Establecer línea base de rendimiento óptimo sin estrés de recursos. |
| `PROFILE_B_MEDIUM` | Contención media | `2.0` | `2048m` (2 GB) | `0` | Evaluar degradación intermedia de recursos. |
| `PROFILE_C_SEVERE` | Contención severa | `1.0` | `1024m` (1 GB) | `0` | Forzar CFS CPU throttling activo y presión severa sobre buffers de memoria. |

> **Regla de registro:** En cada corrida es obligatorio anotar el `profile`, los límites reales de Docker aplicados, la versión exacta del motor y el resultado de spill/OOM.

---

## 5. Especificación del Dataset Sintético (500 000 registros)

- **Volumen total:** 500 000 (500k) órdenes de compra en formato JSON.
- **Estructura y niveles:** ~3 niveles de anidamiento.
- **Items por registro:** Promedio de 3 ítems por orden.

### Esquema del Documento JSON
```json
{
  "order_id": "UUID (ej. 550e8400-e29b-41d4-a716-446655440000)",
  "timestamp": "ISO-8601 (ej. 2026-03-15T14:22:10Z)",
  "customer": {
    "id": "cust_123456",
    "tier": "gold | silver | regular",
    "segment": "enterprise | retail | smb",
    "geo": {
      "country": "MX | US | CA | ...",
      "state": "Chiapas",
      "city": "Tuxtla Gutiérrez",
      "zip": "29000",
      "coordinates": [ -93.1167, 16.75 ]
    }
  },
  "items": [
    {
      "sku": "SKU-98765",
      "category": "Electronics | Home | Sports | Books",
      "brand": "TechCorp",
      "qty": 2,
      "price": 120.50,
      "tax_pct": 0.16,
      "discounts": 10.00
    }
  ],
  "payment": {
    "method": "credit_card | debit_card | paypal | transfer",
    "status": "completed | pending | failed | refunded",
    "transaction_id": "tx_abcdef123456",
    "gateway_latency_ms": 145,
    "totals": {
      "subtotal": 241.00,
      "tax": 38.56,
      "discount": 10.00
    },
    "final_total": 269.56
  },
  "metadata": {
    "channel": "web | mobile_app | pos | api",
    "user_agent": "Mozilla/5.0 ...",
    "session_id": "sess_0987654321",
    "flags": ["loyalty_program", "priority_shipping"]
  }
}
```

---

## 6. Cargas de Trabajo (Consultas Analíticas)

### 6.1. Q1 — Unwind, Filter & Grouping (Saturación de CPU)
* **Objetivo de estrés:** Saturación de ciclos de CPU mediante el desanidamiento de arreglos, filtrado numérico y agregación matemática multifactorial.
* **Descripción lógica:** Desanidar el arreglo de `items`, filtrar aquellos donde `price > 50`, calcular el subtotal por ítem (`qty * price`), y agrupar calculando sumatoria de ingresos (`total_revenue`), ingreso promedio (`avg_revenue`) y conteo (`count`), agrupados por país del cliente y categoría del producto.

#### Pipeline MongoDB (Q1)
```json
[
  { "$unwind": "$items" },
  { "$match": { "items.price": { "$gt": 50 } } },
  {
    "$group": {
      "_id": {
        "country": "$customer.geo.country",
        "category": "$items.category"
      },
      "total_revenue": { "$sum": { "$multiply": ["$items.qty", "$items.price"] } },
      "avg_revenue": { "$avg": { "$multiply": ["$items.qty", "$items.price"] } },
      "count": { "$sum": 1 }
    }
  }
]
```

#### Consulta SQL PostgreSQL (Q1)
```sql
SELECT data->'customer'->'geo'->>'country' AS country,
       item->>'category' AS category,
       SUM((item->>'qty')::numeric * (item->>'price')::numeric) AS total_revenue,
       AVG((item->>'qty')::numeric * (item->>'price')::numeric) AS avg_revenue,
       COUNT(*) AS count
FROM orders, jsonb_array_elements(data->'items') AS item
WHERE (item->>'price')::numeric > 50
GROUP BY 1, 2;
```

---

### 6.2. Q2 — Massive Sort & Top-K (Estrés de Buffer de Memoria)
* **Objetivo de estrés:** Presión directa sobre buffers de memoria RAM asignados a ordenamientos en memoria versus volcado a disco (*disk spill* / fallo OOM).
* **Descripción lógica:** Filtrar órdenes con `payment.status = 'completed'` a partir de una fecha (`timestamp >= '2026-01-01T00:00:00Z'`), ordenar descendentemente por `payment.final_total` (sin índices previos en el total para forzar el sort en memoria/disco) y extraer las 1 000 órdenes de mayor monto (*Top-1000*).

#### Variantes experimentales de estrés de memoria
- **MongoDB:**
  - Variante A: `allowDiskUse: false` (debe fallar si excede el límite de memoria del buffer de 100MB o del contenedor).
  - Variante B: `allowDiskUse: true` (se permite volcado a disco; registrar impacto en degradación de QPS y aumento de I/O).
- **PostgreSQL:**
  - Variante A: `SET work_mem = '4MB';` (fuerza volcado a disco en sort externo / filesort).
  - Variante B: `SET work_mem = '64MB';` (permite mayor uso de RAM por nodo de ordenamiento).

#### Pipeline MongoDB (Q2)
```json
[
  { 
    "$match": {
      "payment.status": "completed",
      "timestamp": { "$gte": "2026-01-01T00:00:00Z" }
    } 
  },
  { "$sort": { "payment.final_total": -1 } },
  { "$limit": 1000 },
  { 
    "$project": {
      "order_id": 1, 
      "customer.id": 1, 
      "payment.final_total": 1
    } 
  }
]
```

#### Consulta SQL PostgreSQL (Q2)
```sql
SELECT data->>'order_id' AS order_id,
       data->'customer'->>'id' AS customer_id,
       (data->'payment'->>'final_total')::numeric AS final_total
FROM orders
WHERE data->'payment'->>'status' = 'completed'
  AND (data->>'timestamp')::timestamptz >= '2026-01-01 00:00:00Z'
ORDER BY (data->'payment'->>'final_total')::numeric DESC
LIMIT 1000;
```

---

## 7. Protocolo de Ejecución Experimental

### 7.1. Dimensiones de la Matriz de Pruebas
- **Motores:** 2 (`MongoDB`, `PostgreSQL`)
- **Perfiles de Recursos:** 3 (`PROFILE_A_BASELINE`, `PROFILE_B_MEDIUM`, `PROFILE_C_SEVERE`)
- **Queries:** 2 (`Q1`, `Q2`)
- **Niveles de Concurrencia:** 3 (`1`, `10`, `50` clientes concurrentes)
- **Total de celdas en la matriz:** $2 \times 3 \times 2 \times 3 = 36 \text{ celdas}$
- **Repeticiones:** 3 ejecuciones independientes por celda.
- **Total de mediciones:** $36 \times 3 = 108 \text{ corridas experimentales}$.

### 7.2. Ciclo de Vida Obligatorio por Corrida
Cada repetición dentro de una celda debe seguir este ciclo estricto e ininterrumpido:
1. **Flush de Caché del Kernel:**
   ```bash
   sync; echo 3 > /proc/sys/vm/drop_caches
   ```
2. **Warmup (Calentamiento):** 60 segundos con tráfico representativo.
3. **Medición Activa:** 300 segundos (5 minutos continuos) donde se recopila la telemetría y métricas de carga.
4. **Cooldown (Enfriamiento):** 60 segundos sin tráfico para permitir estabilización del motor y drenado de conexiones.

### 7.3. Recomendación de Laboratorio (Fase Piloto)
Antes de lanzar las 108 corridas de la matriz completa, **ejecutar una celda piloto** (1 motor × 1 query × 1 concurrencia, ej. MongoDB + Q1 + Concurrencia 1 en Baseline) para verificar:
1. Conexión y recolección de métricas de Prometheus/cAdvisor/Node Exporter.
2. Generación íntegra y sintácticamente válida de las filas del CSV.
3. Tiempos reales del ciclo de vida.

---

## 8. Stack de Telemetría e Indicadores (KPIs)

### 8.1. Componentes del Stack
- **cAdvisor:** Métricas de rendimiento y contención a nivel contenedor Docker (cgroups v2).
- **Node Exporter:** Métricas globales del host del sistema (I/O, disco, swap, paginación).
- **Prometheus:** Recolector de series temporales configurado con `scrape_interval: 1s` para capturar picos y ráfagas.

### 8.2. Catálogo de Indicadores (KPIs)
| KPI | Unidad de Medida | Clasificación | Descripción |
|---|---|---|---|
| `throughput_qps` | queries/segundo | Performance | Rendimiento sostenido del motor. |
| `latency_p50_ms` | milisegundos (ms) | Performance | Mediana de latencia de respuesta. |
| `latency_p95_ms` | milisegundos (ms) | Performance | Percentil 95 de latencia. |
| `latency_p99_ms` | milisegundos (ms) | Performance | Percentil 99 de latencia (cola de latencia). |
| `container_cpu_cfs_throttled_seconds_total` | segundos (s) | OS / Contention | Tiempo acumulado que el kernel estranguló la CPU al contenedor. |
| `container_memory_rss_bytes` | bytes | OS / Memory | Memoria física residente (RSS) utilizada por el contenedor. |
| `disk_spill_detected` | booleano (`true`/`false`) | Engine / Internal | Detección de volcado de datos a disco temporal en ordenamientos o hashes. |
| `oom_killed` | booleano (`true`/`false`) | Stability | Indicador de si el proceso fue terminado por el Out-Of-Memory Killer. |

---

## 9. Especificación de Entregables del Proyecto

El proyecto requiere tanto la suite de código automatizada como las evidencias empíricas y el reporte analítico estructurado:

### 9.1. Repositorio de Código y Scripts
1. `docker-compose.yml`:
   - Configuración parametrizada para MongoDB, PostgreSQL, Prometheus, cAdvisor y Node Exporter.
   - Definición de límites cgroups v2 (`cpus`, `mem_limit`, `mem_swappiness: 0`).
2. `synthetic_data_generator.py`:
   - Generación sintética e inserción masiva y eficiente de los 500 000 documentos con la estructura exacta.
3. `benchmark_runner`:
   - Implementación del ejecutor de pruebas de carga concurrente (mediante scripts k6 o Python multiproceso/asyncio).
4. `queries/`:
   - Directorio conteniendo los scripts y definiciones de consultas:
     - Consultas Q1 y Q2 para MongoDB.
     - Consultas Q1 y Q2 para PostgreSQL.
5. `run_benchmarks.sh`:
   - Script de automatización integral que itere la matriz de 36 celdas $\times$ 3 repeticiones, ejecutando los comandos de flush de caché, warmup (60s), medición (300s), cooldown (60s), consulta a la API de Prometheus y volcado directo al archivo CSV.

---

### 9.2. Esquema CSV de Mediciones (Estricto y Homogéneo)
> **REGLA FUNDAMENTAL:** **Sin columnas inventadas ni renombradas.** El evaluador / estudio posterior concatena automáticamente los CSVs de todos los equipos. Cualquier cambio de nombre, columna faltante o columna adicional invalidará la entrega.

```csv
timestamp_epoch,engine,profile,query_id,concurrency,run_number,throughput_qps,latency_p50_ms,latency_p95_ms,latency_p99_ms,cpu_throttled_seconds,max_rss_mb,disk_spill,status
```

#### Descripción de campos del CSV:
1. `timestamp_epoch`: Timestamp UNIX en segundos al inicio de la corrida.
2. `engine`: `mongodb` o `postgresql`.
3. `profile`: `PROFILE_A_BASELINE`, `PROFILE_B_MEDIUM` o `PROFILE_C_SEVERE`.
4. `query_id`: `Q1` o `Q2` (o variantes documentadas en Q2, ej. `Q2_nodisk`, `Q2_disk`).
5. `concurrency`: `1`, `10` o `50`.
6. `run_number`: Número de repetición (`1`, `2` o `3`).
7. `throughput_qps`: Rendimiento medido en consultas por segundo (float).
8. `latency_p50_ms`: Latencia percentil 50 en ms (float).
9. `latency_p95_ms`: Latencia percentil 95 en ms (float).
10. `latency_p99_ms`: Latencia percentil 99 en ms (float).
11. `cpu_throttled_seconds`: Segundos totales de CPU throttled durante la ventana de 300s (float).
12. `max_rss_mb`: Pico máximo de memoria RSS en megabytes durante la ventana (float).
13. `disk_spill`: `true` o `false`.
14. `status`: Estado final de la corrida (`ok`, `spill`, `oom`, `error`).

---

### 9.3. Evidencias Complementarias Requeridas
- Archivo CSV con los datos de todas las corridas.
- Capturas de pantalla o logs del sistema que evidencien:
  - Eventos de volcado a disco (*disk spill*) en Q2.
  - Eventos de terminación forzada por memoria (*OOM Killer*) o fallos por falta de buffer.
  - Evidencia de CPU CFS throttling en `cgroups`.

---

### 9.4. Estructura Obligatoria del Reporte de Métricas (7 Secciones)
El reporte técnico final debe redactarse cubriendo estrictamente las siguientes 7 secciones:

1. **Especificaciones del host y del entorno Docker:**
   - Hardware físico del anfitrión (CPU, núcleos, RAM, tipo de almacenamiento NVMe/SSD/HDD).
   - Sistema operativo host, versión del kernel Linux / subsistema WSL2 / Docker Engine.
   - Versiones exactas de MongoDB y PostgreSQL utilizadas.
2. **Método de medición y verificación del baseline:**
   - Explicación del protocolo (flush, warmup 60s, test 300s, cooldown 60s).
   - Verificación de condiciones idénticas y consistencia del dataset de 500k registros.
3. **Resultados consolidados (throughput, P95/P99, tiempo de throttling):**
   - Tablas comparativas consolidadas resumiendo la matriz de 36 celdas (usando medias y medianas de las 3 repeticiones).
4. **Análisis gráfico:**
   - Curvas de Latencia P99 vs. Concurrencia (1, 10, 50).
   - Gráfica de Throttling CFS (segundos) vs. Throughput (QPS).
   - Curva temporal de consumo de Memoria RSS a lo largo del tiempo.
5. **Planes de ejecución:**
   - Comparativa detallada entre `explain("executionStats")` de MongoDB y `EXPLAIN (ANALYZE, BUFFERS)` de PostgreSQL para Q1 y Q2.
   - Identificación precisa de cuellos de botella (escaneos secuenciales, costo de desanidamiento JSONB, nodos de Sort vs Top-K en memoria/disco).
6. **Interpretación: límites de memoria, volcado a disco y throttling de cgroups:**
   - Discusión profunda sobre el comportamiento del planificador CFS y la degradación bajo contención severa.
   - Comparativa de la gestión de memoria interna: buffers de ordenamiento de WiredTiger frente a `work_mem` de PostgreSQL.
7. **Recomendaciones técnicas para despliegues documentales en la nube:**
   - Directrices prácticas de ingeniería para arquitectos de datos: cuándo conviene un motor documental nativo, cuándo PostgreSQL con JSONB, cómo dimensionar vCPUs y RAM para evitar *throttling cliff* y evitar colapso de latencia de cola.

---

## 10. Checklist de Preguntas del Revisor (Criterio de Aprobación)

El trabajo será evaluado bajo un estándar riguroso de reproducibilidad científica. Toda afirmación debe sustentarse en los datos del CSV y los planes de ejecución:

- [ ] **1. ¿El baseline es comparable?** Mismo hardware, idéntico dataset sintético de 500 000 documentos, mismas estructuras y condiciones de red/host.
- [ ] **2. ¿Las latencias reportan P50, P95 y P99 o solo promedios?** Prohibido presentar únicamente promedios; el análisis debe centrarse en los percentiles de cola.
- [ ] **3. ¿Hubo throttling CFS real y cuántos segundos acumuló?** Verificado mediante las métricas de cAdvisor / cgroups v2 (`container_cpu_cfs_throttled_seconds_total`).
- [ ] **4. ¿Ocurrió spill a disco o OOM?** Especificar exactamente bajo qué perfil y nivel de concurrencia sucedió, con logs de soporte.
- [ ] **5. ¿Se ejecutaron las 3 repeticiones por celda y cómo se resumieron?** Métodos estadísticos claros (media/mediana) para mitigar anomalías.
- [ ] **6. ¿El plan de ejecución respalda el cuello de botella detectado?** La evidencia teórica del plan (`explain`) debe coincidir con el síntoma de telemetría (CPU bound en Q1, Memory bound en Q2).

---

> **Criterio de Utilidad del Estudio:**  
> *"Si otro equipo no puede reejecutar el benchmark o un revisor no puede cuestionar P99/throttling con sus datos, la entrega está incompleta."*
