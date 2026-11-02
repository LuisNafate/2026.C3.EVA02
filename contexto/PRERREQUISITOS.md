# Prerrequisitos del Proyecto: Funcionales, No Funcionales y Matriz de Prioridad
## Evaluación EVA02: Medición de Métricas en Bases Documentales (MongoDB vs. PostgreSQL JSONB)

---

> **Documento de Especificación y Matriz de Prioridad**  
> **Ubicación:** `contexto/PRERREQUISITOS.md`  
> Este documento clasifica todos los prerrequisitos del proyecto ordenados jerárquicamente por su **Nivel de Importancia (Impacto/Bloqueo)** y etiquetados por su **Nivel de Complejidad Técnica**.

---

## 1. Escala de Clasificación

### Importancia / Jerarquía Operativa
* 🔴 **P1 - Crítico / Bloqueante:** Sin esto el proyecto no puede arrancar ni correr un solo contenedor.
* 🟠 **P2 - Fundacional (Infraestructura y Datos):** Requerido para tener las bases levantadas y el dataset de 500k cargado.
* 🟡 **P3 - Cargas de Trabajo y Medición:** Necesario para inyectar tráfico, concurrencia y medir percentiles.
* 🟢 **P4 - Orquestación y Automatización:** Requerido para ejecutar la matriz completa de 108 corridas de forma desatendida.
* 🔵 **P5 - Evidencias, Análisis y Reporte:** Necesario para el procesamiento de datos, gráficas y aprobación académica.

### Complejidad Técnica
* 🟢 **Baja:** Configuración estándar, comandos únicos o instalación de paquetes.
* 🟡 **Media:** Configuración con parámetros específicos, sintaxis de consultas analíticas o integración de servicios.
* 🔴 **Alta:** Programación concurrente, inserción masiva por lotes, control de memoria y orquestación con control de fallos.
* 🔥 **Muy Alta:** Control fino del kernel (cgroups v2, cuotas CFS, flushing de memoria) y automatización resiliente a OOM.

---

## 2. Matriz de Prerrequisitos Ordenados por Importancia y Complejidad

| Prioridad | ID | Prerrequisito | Tipo | Complejidad | Justificación de Importancia y Complejidad |
|:---:|---|---|:---:|:---:|---|
| **P1** | **PR-01** | **Docker Desktop con WSL 2 y soporte cgroups v2** | No Funcional | 🟡 Media | **Bloqueante primario.** Si Docker corre en cgroups v1 o está apagado, no se puede medir `cpu_cfs_throttled_seconds` ni aplicar límites estrictos de memoria. |
| **P1** | **PR-02** | **Capacidad de Hardware del Host (CPU, RAM, Disco)** | No Funcional | 🟢 Baja | **Bloqueante primario.** Se requieren al menos 4 CPUs lógicos, 6-8 GB RAM asignados a WSL2 y 20 GB en SSD. Sin esto, el perfil baseline congelará Windows. |
| **P1** | **PR-03** | **Privilegios de Kernel para `drop_caches`** | No Funcional | 🔴 Alta | **Bloqueante experimental.** El ciclo de vida exige `sync; echo 3 > /proc/sys/vm/drop_caches`. En Windows/WSL2 requiere permisos de root para garantizar independencia de pruebas. |
| **P2** | **PR-04** | **`docker-compose.yml` con perfiles cgroups v2 y stack** | Funcional / NF | 🟡 Media | **Fundacional.** Debe levantar MongoDB, PostgreSQL, cAdvisor, Node Exporter y Prometheus con `scrape_interval: 1s` y `mem_swappiness: 0`. |
| **P2** | **PR-05** | **Generador e Ingestor Masivo (`synthetic_data_generator.py`)** | Funcional | 🔴 Alta | **Fundacional de datos.** Generar 500 000 documentos anidados e insertarlos eficientemente (en batches/paralelo) en MongoDB y PostgreSQL sin colapsar memoria ni tardar horas. |
| **P2** | **PR-06** | **Indexación Obligatoria en Motores** | Funcional | 🟢 Baja | **Fundacional.** Crear índices en `timestamp` y `order_id` en Mongo, y PK en `id` más B-Tree en `(data->>'timestamp')::timestamptz` en Postgres. |
| **P2** | **PR-07** | **Entorno Python con librerías cliente** | Funcional | 🟢 Baja | **Fundacional.** Entorno virtual `.venv` con `pymongo`, `psycopg2-binary`, `requests`, `pandas`, `matplotlib`, `seaborn`. |
| **P3** | **PR-08** | **Definición de Consultas Analíticas (Q1 y Q2)** | Funcional | 🟡 Media | **Núcleo de estrés.** Pipelines correctos de desanidamiento (`$unwind` / `jsonb_array_elements`), agrupación (Q1) y ordenamiento Top-1000 sin índice (Q2). |
| **P3** | **PR-09** | **Control de Variantes de Buffer en Q2 (Spill vs No Spill)** | Funcional | 🟡 Media | **Núcleo de estrés.** Soportar `allowDiskUse: false/true` en Mongo y `SET work_mem = '4MB'/'64MB'` en Postgres para responder la pregunta M2. |
| **P3** | **PR-10** | **Benchmark Runner Concurrente (1, 10, 50 clientes)** | Funcional / NF | 🔴 Alta | **Medición.** Script en Python multiproceso o k6 capaz de inyectar concurrencia sostenida y calcular matemáticamente latencias P50, P95, P99 y QPS. |
| **P4** | **PR-11** | **Orquestador Automatizado (`run_benchmarks.sh`)** | Funcional | 🔥 Muy Alta | **Automatización.** Debe coordinar las 36 celdas $\times$ 3 repeticiones (108 corridas), respetando warm-up (60s), test (300s), cooldown (60s) y tolerar caídas por OOM sin detenerse. |
| **P4** | **PR-12** | **Extracción de Telemetría desde Prometheus** | Funcional / NF | 🟡 Media | **Datos.** Consultar métricas de cgroups v2 (`cpu_throttled_seconds_total`, `memory_rss_bytes`) por ventana de tiempo y calcular deltas. |
| **P4** | **PR-13** | **Generación Estricta del CSV de Mediciones** | Funcional / NF | 🟢 Baja | **Estándar de entrega.** Escribir las 14 columnas oficiales de forma homogénea con formato inmutable. |
| **P5** | **PR-14** | **Planes de Ejecución (`executionStats` vs `BUFFERS`)** | Funcional | 🟡 Media | **Análisis científico.** Extraer y comparar los planes `explain` de ambos motores para sustentar teóricamente los cuellos de botella de CPU y memoria. |
| **P5** | **PR-15** | **Generación de Gráficas Obligatorias** | Funcional | 🟡 Media | **Visualización.** Crear las 3 gráficas exigidas: P99 vs concurrencia, Throttling vs QPS, y Curvas temporales de RSS. |
| **P5** | **PR-16** | **Redacción del Reporte Técnico (7 Secciones)** | Documental | 🔴 Alta | **Evaluación final.** Síntesis científica que responda a las 6 preguntas del revisor basándose exclusivamente en los datos del CSV. |

---

## 3. Plan de Acción Secuencial para Mitigar Riesgos

Para garantizar un progreso ordenado sin bloqueos:

```
[PASO 1] Verificar Hardware y Encender Docker con cgroups v2 (PR-01, PR-02)
   │
   ▼
[PASO 2] Configurar Entorno Python e Instalar Dependencias (PR-07)
   │
   ▼
[PASO 3] Crear docker-compose.yml con los 3 Perfiles y Telemetría (PR-04)
   │
   ▼
[PASO 4] Programar y Ejecutar synthetic_data_generator.py (PR-05, PR-06)
   │
   ▼
[PASO 5] Probar Consultas Q1 y Q2 + Variantes de Memoria en frío (PR-08, PR-09)
   │
   ▼
[PASO 6] Desarrollar Benchmark Runner y Probar Celda Piloto (PR-10, PR-12, PR-13)
   │
   ▼
[PASO 7] Automatizar Matriz Completa de 108 Corridas con run_benchmarks.sh (PR-03, PR-11)
   │
   ▼
[PASO 8] Extracción de Planes Explain, Gráficas y Redacción del Reporte (PR-14, PR-15, PR-16)
```
