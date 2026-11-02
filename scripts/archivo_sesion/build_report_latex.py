"""Generate a reviewable LaTeX report directly from observed CSV data."""
from pathlib import Path
import json,csv,statistics,collections
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'informe/latex';OUT.mkdir(parents=True,exist_ok=True)
def esc(v):
 s=str(v)
 for a,b in [('\\',r'\textbackslash{}'),('&',r'\&'),('%',r'\%'),('$',r'\$'),('#',r'\#'),('_',r'\_'),('{',r'\{'),('}',r'\}')]:s=s.replace(a,b)
 return s

def fmt(v):return f'{float(v):.2f}' if v not in ['',None] else '--'
meta=json.loads((ROOT/'config/datos_portada.json').read_text())
rows=list(csv.DictReader((ROOT/'resultados/mediciones.csv').open()))
counts=collections.Counter(r['status'] for r in rows)
validation=json.loads((ROOT/'evidencias/validacion/comparabilidad.json').read_text())
parts=[r'''\documentclass[11pt,letterpaper]{article}
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage[spanish,es-tabla]{babel}
\usepackage{lmodern,microtype,geometry,graphicx,booktabs,longtable,array,xcolor,hyperref,fancyhdr,float}
\geometry{margin=2.5cm,headheight=15pt}
\definecolor{navy}{HTML}{14364D}
\hypersetup{hypertexnames=false,colorlinks=true,linkcolor=navy,urlcolor=navy,pdftitle={EVA02 - MongoDB y PostgreSQL JSONB},pdfauthor={Luis Alberto Nafate Hernandez}}
\pagestyle{fancy}\fancyhf{}\fancyhead[L]{\small Bases de Datos en la Nube}\fancyhead[R]{\small EVA02}\fancyfoot[C]{\thepage}
\setlength{\parskip}{5pt}\setlength{\parindent}{0pt}\setlength{\emergencystretch}{2em}
\begin{document}
\begin{titlepage}\centering
{\Large\bfseries Universidad Politécnica de Chiapas\par}\vspace{.5cm}
{\large Ingeniería en Tecnologías de la Información\\e Innovación Digital\par}
\vspace{2cm}
{\Huge\bfseries\color{navy} Medición de métricas\\en bases documentales\par}\vspace{.7cm}
{\Large MongoDB frente a PostgreSQL JSONB\\bajo contención de CPU y memoria\par}
\vspace{1.1cm}{\large Evaluación 2026.C3.EVA02\par}
\vspace{1.4cm}
\begin{tabular}{rl}
\textbf{Alumno:}&Luis Alberto Nafate Hernandez\\[5pt]
\textbf{Matrícula:}&243728\\[5pt]
\textbf{Profesor:}&Horacio Irán Solís Cisneros\\[5pt]
\textbf{Materia:}&Bases de Datos en la Nube\\[5pt]
\textbf{Grupo y periodo:}&7B -- 2026.C3
\end{tabular}
\vfill
{\large\bfseries BORRADOR EN REVISIÓN\par}\vspace{.3cm}
{\small Matriz original completa. Repeticiones de verificación pendientes.\\No corresponde todavía a la entrega final validada.\par}
\vspace{.5cm}{1 de noviembre de 2026\par}
\end{titlepage}
\pagenumbering{roman}\tableofcontents\clearpage\pagenumbering{arabic}
\section{Especificaciones del host y del entorno Docker}
\subsection{Plataforma de ejecución}
El experimento compara agregaciones sobre el mismo conjunto documental, alojado en MongoDB y en una tabla PostgreSQL con JSONB. El cliente de carga corre en Windows; los servicios se ejecutan en la máquina virtual Linux de Docker Desktop. Las métricas del host Linux corresponden a esa máquina virtual, no a todos los procesos de Windows.
\begin{table}[H]\centering\small
\begin{tabular}{p{4.4cm}p{10cm}}\toprule
Elemento & Especificación observada\\\midrule
CPU & AMD Ryzen 5 7640HS; 6 núcleos y 12 procesadores lógicos; frecuencia máxima reportada por WMI: 4301 MHz. No se verificó por separado la frecuencia boost de fabricante.\\
RAM física & 40 GiB, módulos de 8 y 32 GiB, tipo SMBIOS 34 (DDR5). Las velocidades reportadas de los módulos no prueban la velocidad efectiva conjunta.\\
Almacenamiento & Unidades SSD NVMe Predator GM7 de 1 TB y Kioxia de 512 GB. No se verificó en este informe la ubicación física del VHDX de Docker.\\
Sistema & Windows 11 Home Single Language, versión 10.0.26300.\\
Virtualización & WSL 2.7.12.0; kernel 6.18.33.2 de WSL2; cgroups v2.\\
Docker & Desktop 4.87.0; Engine 29.7.2; Compose 5.4.0.\\
Recursos VM & 12 CPU lógicas y aproximadamente 19.1 GiB disponibles al diagnóstico inicial.\\\bottomrule
\end{tabular}\caption{Entorno medido; fuente: registros locales de hardware y Docker.}\end{table}
''']
parts.append('MongoDB verificado: '+esc(validation['mongodb_version'])+'. PostgreSQL verificado: '+esc(validation['postgres_version'])+'. Los digests y la configuración efectiva están conservados en las evidencias del proyecto. Las versiones se fijaron para reproducibilidad; no se afirma que sean la versión estable más reciente a la fecha de entrega.\n')
parts.append(r'''\subsection{Configuración y límites}
Se definieron tres perfiles: A con 4 CPU y 4096 MiB; B con 2 CPU y 2048 MiB; C con 1 CPU y 1024 MiB. El límite combinado de RAM y swap se igualó al de RAM para impedir swap por contenedor. No se utilizó \texttt{mem\_swappiness}, propiedad sin equivalencia directa por cgroup v2. Sólo se ejecuta un motor bajo prueba a la vez.
PostgreSQL se ejecuta con registro de archivos temporales y \texttt{work\_mem} de 4 o 64 MB según variante. Tras detectar el límite auxiliar de 64 MiB de memoria compartida de Docker, se configuró \texttt{shm\_size=1gb}; no es una reserva y el consumo sigue sometido al límite del perfil. Los resultados anteriores a ese cambio están identificados para repetición. MongoDB utiliza WiredTiger, sin sharding.
\section{Método de medición y verificación del baseline}
\subsection{Datos, consultas y comparabilidad}
Se generaron 500\,000 órdenes deterministas con semilla 2026 y tres ítems por orden. Incluyen UUID, fecha UTC canónica, cliente y geografía, ítems, pago y metadatos. Se cargó el mismo lote lógico en ambos motores. Se verificó el conteo completo y un hash canónico ordenado por identificador, excluyendo el identificador interno de MongoDB.
''')
parts.append(r'\textbf{SHA-256 canónico de comparación:} \par{\footnotesize\ttfamily '+validation['canonical_sha256'][:32]+r'\ '+validation['canonical_sha256'][32:]+r'}\par'+'\n')
parts.append(r'''Q1 desanida ítems, filtra precios mayores de 50 y agrupa por país y categoría, calculando suma, promedio y conteo. Se verificaron doce grupos equivalentes, con tolerancia relativa de $10^{-9}$ en valores numéricos. Q2 filtra pagos completados desde el 1 de enero de 2026 y obtiene los mil mayores totales; se verificaron los mil valores ordenados. Los identificadores del borde pueden variar ante empates.
MongoDB tiene índices simples en fecha e identificador. PostgreSQL tiene clave primaria UUID e índice de texto sobre la fecha extraída. El cast directo a \texttt{timestamptz} propuesto en el material no es una expresión inmutable para indexación; se empleó texto ISO UTC canónico de longitud fija en índice y predicado. La equivalencia es específica de ese formato, no se generaliza a husos u otras representaciones.
\subsection{Matriz y ciclo de vida}
La matriz explícita del playbook es $2\times3\times2\times3\times3=108$ corridas. Se amplió Q2 para medir ambas variantes en los tres perfiles, añadiendo 54 y llegando a 162. Esta ampliación es una decisión metodológica documentada, no un total expresamente escrito en el playbook.
Cada corrida contempla limpieza de caché del kernel Docker Desktop, calentamiento de 60 segundos, observación de 300 segundos y enfriamiento de 60 segundos. Los clientes consumen el resultado completo. Una barrera coordina el inicio tras preparar las conexiones. El generador usa hilos con conexiones independientes para carga de entrada/salida; esto es una adaptación al cliente Python y no una implementación multiproceso por cliente.
Las consultas tienen límite de 300 segundos. Para no bloquear la matriz se añadieron fases en procesos aislados y un máximo de 900 segundos por ejecutor. Los cambios del cliente se registran porque modifican la recuperación ante fallos. El tiempo total real puede superar siete minutos por drenado, preparación y recuperación. Se realizaron pausas solicitadas por el usuario y hubo una hibernación; los intentos afectados se conservan y revisan aparte.
\subsection{Definición de las métricas y sesgos}
QPS divide las consultas exitosas completadas dentro de la ventana entre 300 segundos. P50, P95 y P99 se calculan por interpolación lineal sobre latencias individuales exitosas. Las consultas que terminan fuera de la ventana están censuradas; por ello estos percentiles no describen todos los trabajos iniciados ni incluyen tiempos de fallos. Un promedio de P99 por corrida tampoco equivale al P99 combinado de todas las muestras.
Prometheus consulta cada segundo. Se extrae el delta del contador CFS y el máximo RSS. Si faltan muestras suficientes o el contador se reinicia, la fila no se considera válida. El contador CFS puede sumar espera de varios hilos y superar los 300 segundos: no es tiempo de pared ni porcentaje de CPU.
El nombre baseline no demuestra ausencia de contención. El perfil A también tiene cuota y presentó throttling con concurrencia; por tanto se informa como referencia con cuota, no como baseline empíricamente libre de estrangulamiento.
\section{Resultados consolidados}
\subsection{Estado del conjunto original}
''')
parts.append(f'La matriz original reúne {len(rows)} filas: {counts["ok"]} con estado ok, {counts["spill"]} con spill, {counts["error"]} con error y {counts["oom"]} con OOM. Este borrador utiliza exclusivamente esas filas originales; las diez repeticiones predeclaradas se integrarán por regla fija al finalizar, conservando los originales en el CSV completo.\n')
parts.append(r'''Los errores de memoria compartida y de telemetría no se presentan como resultados intrínsecos del motor. Las filas error/OOM se conservan para estabilidad, pero se excluyen de promedios de rendimiento. Por tanto una celda con menos de tres repeticiones válidas no permite la misma inferencia que una completa. La tabla incluye el número válido para evitar ocultarlo.
\subsection{Tablas por motor}
Se reportan medias de las métricas por corrida; los archivos de resumen incluyen además mediana y desviación estándar. CFS está expresado en segundos, RSS en MB decimales y latencias en milisegundos. Un guion significa dato no disponible, no cero.
''')
for engine in ['mongodb','postgresql']:
 if engine=='postgresql':parts.append(r'\clearpage'+'\n')
 parts.append('\n\\subsubsection{'+('MongoDB' if engine=='mongodb' else 'PostgreSQL JSONB')+'}\n')
 parts.append(r'''{\fontsize{7.5}{9}\selectfont\setlength{\tabcolsep}{3pt}
\begin{longtable}{llrrrrrrrr}
\toprule Perfil & Consulta & Cli. & $n$ & QPS & P50 & P95 & P99 & CFS & RSS\\\midrule\endfirsthead
\toprule Perfil & Consulta & Cli. & $n$ & QPS & P50 & P95 & P99 & CFS & RSS\\\midrule\endhead
\bottomrule\endfoot
''')
 groups=collections.defaultdict(list)
 for r in rows:
  if r['engine']==engine:groups[(r['profile'],r['query_id'],int(r['concurrency']))].append(r)
 for (profile,q,c),items in sorted(groups.items()):
  valid=[r for r in items if r['status'] in ['ok','spill']]
  values=[]
  for metric in ['throughput_qps','latency_p50_ms','latency_p95_ms','latency_p99_ms','cpu_throttled_seconds','max_rss_mb']:
   data=[float(r[metric]) for r in valid if r[metric]];values.append(fmt(statistics.mean(data)) if data else '--')
  parts.append(' & '.join([profile.split('_')[1],esc(q),str(c),str(len(valid)),*values])+r'\\'+'\n')
 parts.append(r'\end{longtable}}'+'\n')
parts.append(r'''\subsection{Lectura provisional}
Q1 y Q2 no son cargas intercambiables: una compara expansión y agregado, la otra selección y Top-K. Los casos de alta concurrencia con errores no permiten concluir superioridad por un QPS aparente de cero si no hubo una ventana válida de consultas completadas. La comparación definitiva utilizará el manifiesto de selección y mostrará también proporción de fallos y cobertura por celda.
\section{Análisis gráfico}
Las figuras de esta versión proceden de la matriz original. Se actualizarán tras integrar las verificaciones. No deben interpretarse como comparación controlada entre ejecuciones previas y posteriores a cambios del entorno.
\begin{figure}[H]\centering\includegraphics[width=\linewidth]{../p99_concurrencia.png}\caption{P99 frente a concurrencia. Cada línea resume percentiles por corrida; no es un percentil combinado.}\end{figure}
\begin{figure}[H]\centering\includegraphics[width=\linewidth]{../throttling_qps.png}\caption{CFS y rendimiento. Los perfiles cambian CPU y RAM conjuntamente: una asociación no aísla causalidad.}\end{figure}
\begin{figure}[H]\centering\includegraphics[width=\linewidth]{../rss_temporal.png}\caption{Series RSS de ejemplos Q2 por variante. Permitir disco no demuestra que haya ocurrido spill.}\end{figure}
\section{Planes de ejecución}
Se capturaron planes reales fuera de las ventanas: \texttt{executionStats} para MongoDB y \texttt{EXPLAIN (ANALYZE, BUFFERS, VERBOSE)} para PostgreSQL, con ambas variantes. Están en las evidencias de validación; los planes iniciales son del baseline y no prueban automáticamente los operadores de todos los perfiles.
Q1 permite estudiar el costo de recorrer órdenes, expandir arreglos y agrupar. La cantidad de filas expandidas es mayor que el número de órdenes. Q2 puede emplear una selección Top-K acotada en lugar de materializar un ordenamiento completo. El análisis final debe identificar los nodos y métodos efectivos, no deducir external merge sólo a partir de que se usaron 4 MB.
La evidencia de archivos temporales en PostgreSQL Q1 no se atribuye automáticamente al operador Sort: también puede proceder de otros operadores o materialización. El desglose de planes y buffers se incorporará a la versión final con sus identificadores de archivo.
\section{Interpretación: memoria, disco y throttling de cgroups}
\subsection{Presupuestos y estabilidad}
Las cuotas CPU pueden agotar el presupuesto periódico aunque el equipo tenga otros núcleos libres. La suma de espera entre hilos explica que CFS acumulado exceda la duración de la observación. El RSS de cAdvisor no equivale a toda la memoria imputada al cgroup; tampoco es intercambiable con la caché de páginas del host.
WiredTiger y las etapas de agregación tienen presupuestos distintos. En PostgreSQL, \texttt{work\_mem} es un presupuesto por operación y puede multiplicarse por conexiones y trabajadores. Un límite de contenedor no se convierte automáticamente en un presupuesto seguro para cincuenta clientes.
\subsection{Spill, OOM y errores de laboratorio}
Spill se registra mediante indicadores \texttt{usedDisk} o archivos temporales; OOM mediante estado Docker y sus evidencias. Un timeout o falta de memoria compartida no prueba un OOM. Las filas originales conservaron todos esos estados. En particular, el límite auxiliar de memoria compartida se corrigió y la pérdida de telemetría por cierre de cAdvisor obliga a repetir la observación.
El perfil severo PostgreSQL Q1 con 50 clientes produjo estados OOM en dos intentos registrados. Esto constituye evidencia de inestabilidad bajo esa configuración, no una afirmación de que el motor falle con cualquier documento o carga. Debe contrastarse con los logs e inspect conservados y con la recuperación aplicada.
\subsection{Alcance de las conclusiones}
Hay limitaciones explícitas: cliente Windows externo a la VM, posible carga del host, pausas y cambios del cliente, censura temporal de consultas lentas y falta de aleatorización de la secuencia. El estudio es descriptivo de esta plataforma; no generaliza directamente a servicios administrados en nube.
La pregunta de costo por mil documentos (M3) requiere CPU realmente consumida y documentos examinados, no sólo tiempo CFS y RSS máximo. Este borrador no inventa ese costo a partir de los indicadores disponibles; se revisará la cobertura de telemetría y planes antes de cerrar esa conclusión.
\section{Recomendaciones técnicas para despliegues documentales en la nube}
Conviene validar el motor contra las consultas, el modelo transaccional y los requisitos operativos reales. Estos resultados no establecen un ganador universal para todo JSON. PostgreSQL JSONB permite combinar documentos y relaciones; MongoDB ofrece un modelo documental nativo. La selección debe apoyarse en la carga y en los índices necesarios, además de la estabilidad observada.
Se recomienda dimensionar límites CPU observando P95/P99 y throttling, no sólo promedio de QPS; limitar concurrencia para evitar colas y presión de memoria; estimar el presupuesto de operaciones simultáneas antes de aumentar \texttt{work\_mem}; y verificar cuotas y memoria compartida en el contenedor antes de comparar motores.
En Kubernetes o ECS se deben comprobar los límites efectivos del despliegue y repetir el protocolo en la infraestructura objetivo. Los números de este equipo no son una recomendación certificada de tamaño de instancia. El siguiente paso es evaluar las mismas consultas en perfiles donde CPU y RAM varíen por separado, para aislar sus efectos.
\clearpage
\section*{Referencias y trazabilidad}\addcontentsline{toc}{section}{Referencias y trazabilidad}
\begin{enumerate}
\item Material académico de la evaluación: \textit{playbook.pdf}, secciones 1--8, y \textit{playbook\_sesion.pdf}. Copias originales conservadas en el proyecto.
\item MongoDB. \textit{Sort aggregation stage}, documentación de versión 8.0. \url{https://www.mongodb.com/docs/v8.0/reference/operator/aggregation/sort/}
\item PostgreSQL. \textit{CREATE INDEX}, documentación de versión 17. \url{https://www.postgresql.org/docs/17/sql-createindex.html}
\item Tectonic. \textit{Installing Tectonic}. Compilador portátil 0.17.0. \url{https://tectonic-typesetting.github.io/book/latest/installation/}
\end{enumerate}
\textbf{Archivos de evidencia:} CSV original, CSV de repeticiones, manifiesto de selección, comparación canónica de datos, planes, logs por corrida, inspect de contenedores, series Prometheus y muestras individuales. Todos los archivos de resultados deben conservar sus nombres y trazabilidad al reorganizar el repositorio.
\textbf{Pendientes de cierre:} finalizar las verificaciones, integrar resultados por regla predeclarada, comprobar métricas contra muestras, detallar planes, revisar las figuras finales y ejecutar la lista de entregables del playbook. Esta versión es revisable, no una declaración de cumplimiento completo.
\end{document}
''')
(OUT/'reporte_eva02.tex').write_text(''.join(parts),encoding='utf8')
print('Fuente LaTeX generado')
