# Revisión de requisitos - 30 de octubre de 2026

## Ya disponible y reutilizable
- Windows 11; Ryzen 5 7640HS: 6 núcleos, 12 hilos.
- 40 GiB de RAM física; unidades SSD NVMe.
- Python 3.13.14 y pip 26.1.2.
- Docker Desktop 4.87.0, Engine 29.7.2, Compose 5.4.0.
- WSL 2.7.12.0 y kernel 6.18.33.2-2.
- Docker responde y usa cgroups v2; tiene 12 CPU y aproximadamente 19.1 GiB de RAM disponibles.
- Imagen postgres:17 ya descargada: se reutiliza.

## Faltantes comprobados en el Python activo
pymongo, psycopg/psycopg2, requests, pandas, matplotlib y seaborn no están disponibles en este intérprete. Esto no demuestra su ausencia en otros entornos Python.

Para el código actual se requieren pymongo, psycopg[binary], requests, pandas y matplotlib. Seaborn no es necesario. Se propone un entorno .venv dentro del proyecto para evitar modificar otros proyectos. Aún no se ha instalado ninguna dependencia.

## Imágenes que aún no aparecen en Docker
MongoDB, Prometheus, cAdvisor y Node Exporter. Serían descargadas como imágenes de contenedor; no se necesita instalar servidores de bases de datos directamente en Windows.

## Pendiente de validación funcional
- Disponibilidad de los puertos, salud de cada servicio y métricas cAdvisor en Docker Desktop.
- Limpieza de caché en el kernel que realmente ejecuta Docker; una distribución WSL distinta no prueba equivalencia.
- Verificación de swap efectivo, cuotas CPU y memoria mediante inspect y cgroups.
- Identidad del dataset, equivalencia de resultados de consultas, planes y eventos spill/OOM.
- Las versiones de imágenes propuestas están fijadas por reproducibilidad, pero NO se han verificado como latest-stable actual.

## Revisión adversaria
- 108 corridas x 420 segundos = 12 h 36 min como mínimo. Al repetir ambas variantes Q2 son 162 corridas = 18 h 54 min, más preparación.
- El índice directo de PostgreSQL que convierte texto a timestamptz puede ser rechazado por volatilidad. El código usa B-tree de texto ISO UTC canónico y Q2 compara ese mismo texto; debe documentarse como adaptación.
- Top-1000 puede usar un ordenamiento acotado y no producir spill con 4 MB. Ausencia de spill es un resultado válido; no se debe inventar ni cambiar silenciosamente Q2.
- Perfil A también tiene cuota CPU: ausencia de throttling debe demostrarse.
- No confundir errores de buffer con OOM del contenedor.
- Scripts iniciales creados; todavía no están validados de extremo a extremo ni constituyen una entrega terminada.

## Evidencia
host.json contiene los datos de hardware obtenidos del equipo. No se ha ejecutado aún el experimento ni generado mediciones académicas.
