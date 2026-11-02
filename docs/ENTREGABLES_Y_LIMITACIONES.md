# Entregables y límites de la entrega

| Elemento del playbook | Archivo o evidencia | Estado y alcance |
|---|---|---|
| Docker Compose parametrizado | `docker-compose.yml`, `config/prometheus.yml` | Implementado con los cinco servicios y límites A/B/C. Swap se limita mediante memoria+swap igual a memoria; no se usa swappiness en v2. |
| Generador 500 k | `synthetic_data_generator.py`, `resultados/dataset_manifest.json` | 500000 documentos cargados y comparados entre motores. |
| Carga concurrente | `benchmark_runner.py` | 1/10/50 conexiones; hilos de cliente y fases aisladas por proceso. Adaptación declarada respecto a multiproceso por cliente. |
| Consultas | `queries/` | Q1 y Q2; índice/predicado PostgreSQL en texto UTC canónico, adaptación declarada. |
| Automatización | `run_benchmarks.sh`, `scripts/run_suite.py` | 108 corridas base ampliadas a162 por variantesQ2; entrada específica de Windows/Docker Desktop. |
| CSV14 columnas | `resultados/todas_las_pruebas.csv` | 165 observaciones completas en archivo; métricas ausentes siguen vacías en fallos. |
| Planes | `evidencias/validacion/*plan.json` | Planes reales iniciales con ambas variantes. No son planes de todos los perfiles. |
| Spill | Logs, inspect, muestras y planes PostgreSQL Q1 | 18 filas spill en matriz; Top-K Q2 no garantizó spill. No se fuerza un resultado ficticio. |
| OOM | `evidencias/postgresql_PROFILE_C_SEVERE_Q1_nodisk_50_1/inspect.json` y repetición2 | Dos filas OOM originales. Se conservan también errores diferentes de OOM. |
| CFS | Series por corrida, CSV y figura | Deltas de contador; baseline con cuota también tuvo throttling. |
| Reporte7 secciones | `informe/latex/reporte_eva02.tex` y `.pdf` | Portada, tablas, tres figuras, planes, fallos y recomendaciones. |
| M3 CPU/1000 documentos | Sección6 del reporte | No establecido con rigor por los datos reunidos; no se sustituye por CFS ni por RSS. |
| Baseline sin contención | Secciones2 y6 | No demostrado; el perfil A se trata como referencia con cuota. |
| Versioneslatest-stable | Manifiestos Docker y reporte | Versiones fijadas para reproducibilidad; no se afirma latestestable actual. |

La entrega académica es un informe experimental con evidencia y limitaciones explícitas, no una garantía de que cada hipótesis del material haya ocurrido. Los cambios de entorno, pausas e hibernación están registrados. Tres verificaciones se conservan como suplementos; no se completaron las otras siete por decisión del usuario. No se mezclan configuraciones ni se seleccionan exclusivamente éxitos para declarar un ganador.
