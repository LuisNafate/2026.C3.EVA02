# EVA02 · Bases de Datos en la Nube

Comparación reproducible de **MongoDB 8.0.34** y **PostgreSQL 17.11 con JSONB**, bajo límites de CPU y RAM con Docker y cgroups v2.

**Autor:** Luis Alberto Nafate Hernandez · Matrícula 243728  
**Universidad:** Universidad Politécnica de Chiapas · IT2iD · 7B  
**Profesor:** Horacio Irán Solís Cisneros · Periodo 2026.C3

## Entrega

- [Reporte PDF](informe/latex/reporte_eva02.pdf): 14 páginas, siete secciones, figuras, planes y anexos de fallos.
- [Fuente LaTeX](informe/latex/reporte_eva02.tex).
- [Todas las pruebas](resultados/todas_las_pruebas.csv): **165 observaciones**, con las 14 columnas oficiales.
- [Matriz original](resultados/mediciones.csv): 162 corridas, análisis principal.
- [Verificaciones complementarias](resultados/repeticiones.csv): tres observaciones; no sustituyen fallos del original.
- [Auditoría](resultados/auditoria_entrega.json), [cierre experimental](resultados/cierre_experimental.json) y [resumen estadístico](informe/resumen.csv).
- [Guía para exponer](informe/GUIA_CLASE.md) y [revisión de entregables](docs/ENTREGABLES_Y_LIMITACIONES.md).

La matriz original contiene 127 `ok`, 18 `spill`, 15 `error` y 2 `oom`. Con los suplementos, el CSV completo contiene 128 `ok`, 20 `spill`, 15 `error` y 2 `oom`. **Spill es una ejecución completada con uso de disco temporal; los fallos también son evidencia.**

## Alcance y limitaciones

Se completó la matriz y, por decisión del alumno, se cerraron las repeticiones adicionales conservando todos los fallos. El informe diferencia saturación/timeout/OOM de hibernación, pérdida de telemetría y límite auxiliar de memoria compartida. No afirma que los errores sean todos intrínsecos del motor ni que se haya obtenido un baseline libre de throttling.

El índice temporal PostgreSQL compara texto ISO UTC canónico para evitar el cast no inmutable del ejemplo académico. Se utilizaron versiones fijadas y clientes por hilos, con fases aisladas por proceso para recuperación. No se establece un costo exacto de CPU por mil documentos (M3). Estas adaptaciones y limitaciones son parte de la entrega; no se ocultan con repeticiones selectivas.

## Organización

```text
config/                 Compose auxiliar, Prometheus y datos de portada
contexto/               Contexto y requisitos recibidos, conservados
queries/                Q1/Q2 para MongoDB y PostgreSQL
scripts/                Ejecución, auditoría, análisis y compilación
scripts/archivo_sesion/ Historial de ayudantes de preparación; no ejecutar como flujo normal
resultados/             CSV, manifiestos y auditoría
informe/                Tablas, figuras, guía y fuente LaTeX/PDF
evidencias/             Muestras, logs, series, inspect, planes e incidentes
docs/                   Método, entregables y uso del repositorio
entrega/                Paquete final para compartir
```

Los archivos oficiales `docker-compose.yml`, `synthetic_data_generator.py`, `benchmark_runner.py`, `run_benchmarks.sh` y los dos playbooks permanecen en la raíz para facilitar la evaluación. `.venv`, `.tools`, el dataset masivo y temporales no se incluyen en Git.

## Preparación en este equipo (Windows/WSL2)

Requisitos: Docker Desktop con backend Linux y cgroups v2, Python 3.13, permisos root en la distribución `docker-desktop` para limpiar caché y espacio para el dataset. Las pruebas consumen recursos; evitar hibernación y cargas pesadas.

```powershell
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements.lock.txt
docker compose up -d
.venv/Scripts/python.exe synthetic_data_generator.py --load
.venv/Scripts/python.exe scripts/validate.py
.venv/Scripts/python.exe scripts/run_suite.py
```

**No ejecutar la carga sobre los volúmenes de esta entrega:** ya tienen los 500000 documentos. El generador rechaza bases no vacías y no elimina datos automáticamente. Para reproducir desde cero usar un proyecto Compose distinto y bases vacías; nunca borrar los volúmenes sin respaldo.

Puertos locales: MongoDB `27018`, PostgreSQL `5432`, Prometheus `9090`. Las credenciales son exclusivas de este laboratorio y los puertos de base se exponen solo a la interfaz local. No usar esta configuración como despliegue público.

`run_benchmarks.sh` sirve de entrada Bash para este proyecto Windows; llama al orquestador Python, que vacía caché en el kernel real de Docker Desktop. No es un orquestador portable a Linux sin adaptar esa operación.

El perfil A usa 4 CPU/4 GiB; B 2 CPU/2 GiB; C 1 CPU/1 GiB. Las consultas conservan el timeout de 300 s y cada ejecutor tiene un tope de 900 s. La preparación, recuperación y cierre pueden añadir tiempo. Una corrida fallida no se interpreta como latencia cero.

## Auditoría y resultados

```powershell
.venv/Scripts/python.exe scripts/audit_delivery.py
.venv/Scripts/python.exe scripts/consolidate.py
```

La auditoría verificó el esquema, claves únicas por bloque y recalculó percentiles y QPS de **156 observaciones con muestras de latencia**, incluidas algunas con errores parciales. No valida como exitosos los estados error/OOM.

El CSV completo conserva observaciones repetidas con la misma clave lógica porque son intentos distintos. El orden es matriz original y luego suplemento. El manifiesto identifica la procedencia. Las carpetas de intentos interrumpidos no se convierten en filas inventadas.

`analyze.py` reconstruye figuras y resumen de la matriz original. Puede regenerar un antiguo reporte Markdown automático; el documento académico canónico es el `.tex` revisado, no ese resumen de trabajo.

## Compilar el informe

```powershell
.venv/Scripts/python.exe scripts/prepare_latex.py
powershell -ExecutionPolicy Bypass -File scripts/compilar_reporte.ps1
```

Se usa Tectonic portátil 0.17.0 descargado del proyecto oficial. La primera compilación puede descargar paquetes TeX a su caché. No se instala una distribución completa en Windows. El archivo `.tex` se compila directamente; no se regenera la versión final desde el antiguo generador de borradores.

## Versiones y GitHub

Repositorio: https://github.com/LuisNafate/2026.C3.EVA02 (público). La rama `main` y las etiquetas anotadas `datos-v1.0.0` y `v1.0.0` están publicadas. Cualquier persona puede consultar el proyecto y descargar sus archivos. Véase [guía de repositorio](docs/REPOSITORIO.md).
