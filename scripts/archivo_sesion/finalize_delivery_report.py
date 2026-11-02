from pathlib import Path
import csv,json,collections,statistics
ROOT=Path(__file__).resolve().parents[1]
base=list(csv.DictReader((ROOT/'resultados/mediciones.csv').open()));extra=list(csv.DictReader((ROOT/'resultados/repeticiones.csv').open()))
counts=collections.Counter(r['status'] for r in base)
# Fixed publication rule: original matrix is the primary analysis; supplements never erase failures.
manifest=dict(publication_rule='Original 162-row matrix is primary; 3 completed reruns are supplementary and do not replace original failures',original_count=len(base),completed_supplements=len(extra),planned_supplements=10,remaining_supplements_cancelled_by_user=True,original_statuses=dict(counts),limitations=['Host hibernation affected an attempt','PostgreSQL shm_size adjusted during experiment','Incomplete cAdvisor window retained as error','Client timeout recovery evolved','M3 exact CPU cost per 1000 scanned documents not established'])
(ROOT/'resultados/cierre_experimental.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf8')
# Final report generated from the reviewable source; never overwrite original data.
p=ROOT/'informe/latex/reporte_eva02.tex';s=p.read_text(encoding='utf8')
s=s.replace('BORRADOR EN REVISIÓN','REPORTE TÉCNICO EXPERIMENTAL')
s=s.replace('Matriz original completa. Repeticiones de verificación pendientes.\\\\No corresponde todavía a la entrega final validada.','162 corridas originales y 3 verificaciones complementarias.\\\\Resultados, incidentes y limitaciones documentados.')
s=s.replace('El análisis final debe identificar los nodos y métodos efectivos, no deducir external merge sólo a partir de que se usaron 4 MB.','Los operadores efectivos se detallan a continuación; no se deduce external merge sólo a partir de que se usaron 4 MB.')
s=s.replace('Los archivos de resumen incluyen además mediana y desviación estándar.','Los archivos de resumen incluyen además mediana y desviación estándar.')
s=s.replace('las diez repeticiones predeclaradas se integrarán por regla fija al finalizar, conservando los originales en el CSV completo.','se completaron tres verificaciones complementarias y se cancelaron las siete restantes por instrucción del usuario. La matriz original se mantiene como análisis principal: los suplementos no borran fallos ni sustituyen resultados para mejorar la comparación. El CSV completo reúne 165 observaciones y conserva los 14 campos oficiales.')
s=s.replace('Se actualizarán tras integrar las verificaciones.','Las tres verificaciones se presentan como suplemento separado, sin modificar estas figuras.')
s=s.replace('El desglose de planes y buffers se incorporará a la versión final con sus identificadores de archivo.','El desglose siguiente identifica archivos y operadores realmente observados.')
s=s.replace('se revisará la cobertura de telemetría y planes antes de cerrar esa conclusión.','no se establece una conclusión cuantitativa de M3 con la información reunida. Esta limitación no se subsana usando throttling como si fuera CPU consumida.')
s=s.replace('La comparación definitiva utilizará el manifiesto de selección y mostrará también proporción de fallos y cobertura por celda.','La comparación publicada utiliza la matriz original, declara los cambios del entorno y muestra la cobertura válida por celda. Los suplementos se identifican por archivo y no se combinan silenciosamente con el bloque primario.')
old=r'\textbf{Pendientes de cierre:} finalizar las verificaciones, integrar resultados por regla predeclarada, comprobar métricas contra muestras, detallar planes, revisar las figuras finales y ejecutar la lista de entregables del playbook. Esta versión es revisable, no una declaración de cumplimiento completo.'
s=s.replace(old,r'\textbf{Criterio de cierre:} por instrucción del alumno se conserva el resultado completo, incluidos fallos de ejecución y de laboratorio. No se repiten indefinidamente las celdas hasta obtener éxito. El informe declara las limitaciones que impiden atribuir todos los errores a los motores o afirmar una comparación perfectamente controlada.')
plantext=r'''
\subsection{Operadores y evidencia efectiva}
En \texttt{Q1\_mongo\_nodisk\_plan.json}, MongoDB examinó 500\,000 documentos con COLLSCAN, expandió 1\,500\,000 ítems y dejó 1\,254\,674 tras el filtro. El agrupamiento devolvió doce grupos con \texttt{usedDisk=false} y cero spills. El tiempo registrado en executionStats fue 1502 ms (1522 ms en la variante con disco permitido); el campo no debe confundirse con la latencia completa del cliente.
En \texttt{Q1\_postgres\_4MB\_plan.json} se observaron Aggregate, Incremental Sort, Nested Loop, Gather Merge, Seq Scan y Function Scan. El ordenamiento anterior a la expansión empleó external merge, con espacios de disco de 173248, 214864 y 196584 kB entre procesos. El tiempo total del plan fue 3122.06 ms. Con 64 MB también hubo external merge (3175.71 ms); elevar work\_mem no eliminó este volcado.
Q2 MongoDB utilizó IXSCAN, FETCH y SORT: examinó 247\,702 documentos, el filtro dejó 61\,738 y se devolvieron mil. No hubo spill en los dos planes; sus tiempos fueron 571 y 534 ms. Q2 PostgreSQL utilizó Seq Scan, Sort, Gather Merge y Limit; los Sort mostraron top-N heapsort en memoria con aproximadamente 271--275 kB por proceso. Los tiempos fueron 103.987 y 113.471 ms para 4 y 64 MB. Estos planes explican por qué Q2 no produjo el spill que se podría haber esperado sólo por su título de ordenamiento masivo.
La comparación tiene diferencias reales de estrategia: el plan MongoDB Q2 examinó menos documentos por el índice temporal, mientras PostgreSQL eligió lectura secuencial. Ningún resultado se atribuye exclusivamente al formato BSON o JSONB sin considerar esos planes.
'''
s=s.replace(r'\section{Interpretación: memoria, disco y throttling de cgroups}',plantext+r'\section{Interpretación: memoria, disco y throttling de cgroups}')
# Numeric comparisons computed from the original data, limited to cells with 3 successful runs.
def group(engine,profile,q,c):return [r for r in base if r['engine']==engine and r['profile']==profile and r['query_id']==q and r['concurrency']==str(c) and r['status'] in ['ok','spill']]
comparison=[]
for engine in ['mongodb','postgresql']:
 a=group(engine,'PROFILE_A_BASELINE','Q1',1);b=group(engine,'PROFILE_C_SEVERE','Q1',1)
 if len(a)==len(b)==3:
  qa=statistics.mean(float(r['throughput_qps']) for r in a);qb=statistics.mean(float(r['throughput_qps']) for r in b)
  comparison.append(f"Para {engine}, Q1 con un cliente pasó de {qa:.3f} QPS en A a {qb:.3f} en C, una reducción de {(1-qb/qa)*100:.1f}\\%. Es una comparación descriptiva de los perfiles, que cambian CPU y RAM conjuntamente.")
extra_text=r'\subsection{Contrastes cuantitativos y estabilidad}'+'\n'+'\n\n'.join(comparison)+r'''

En la matriz primaria hubo 145 corridas completadas sin error terminal (127 ok y 18 spill), 15 error y dos OOM. La frecuencia agregada de error/OOM fue $17/162=10.49\%$; mezcla incidentes experimentales y del entorno, por lo que no representa una tasa intrínseca de fallo del motor. Los 18 spills ocurrieron en Q1 de PostgreSQL y constituyen resultados terminados, no errores. La serie original contiene 54 celdas al desagregar las variantes Q2; no son 54 consultas distintas.
Las medias de la tabla están condicionadas al éxito. En especial, una celda con cero repeticiones válidas se muestra sin percentiles: no se informa latencia cero ni superioridad por ausencia de muestras. Medianas y desviaciones estándar por celda se incluyen en el archivo de resumen para examinar variabilidad, sin sustituir la evidencia individual.
'''
s=s.replace(r'\section{Análisis gráfico}',extra_text+r'\section{Análisis gráfico}')
# Appendix of every original terminal failure and a separately labelled supplement.
annex=r'''\clearpage\appendix
\section{Registro de fallos y problemas del experimento}
Las filas se numeran desde uno, excluyendo la cabecera del CSV original. Un timeout es un resultado de la configuración y del límite aplicado; no se equipara automáticamente con OOM. Las filas de fallos del entorno siguen visibles, pero no sustentan superioridad del motor.
{\small\begin{longtable}{rp{3cm}p{2.7cm}p{6.5cm}}
\toprule Fila & Motor y perfil & Carga & Evidencia y clasificación\\\midrule\endfirsthead
\toprule Fila & Motor y perfil & Carga & Evidencia y clasificación\\\midrule\endhead\bottomrule\endfoot
'''
def tex(x):return str(x).replace('_',r'\_').replace('%',r'\%').replace('&',r'\&')
for i,r in enumerate(base,1):
 if r['status'] not in ['error','oom']:continue
 q=r['query_id'].split('_')[0];variant=r['query_id'].split('_',1)[1] if q=='Q2' else 'nodisk'
 folder=ROOT/'evidencias'/f"{r['engine']}_{r['profile']}_{q}_{variant}_{r['concurrency']}_{r['run_number']}"
 errors=json.loads((folder/'samples.json').read_text()).get('errors',[]) if (folder/'samples.json').exists() else []
 cause='Timeout/cancelación de consulta; se conserva como resultado y no se afirma OOM.'
 if r['status']=='oom':cause='Docker inspect registró OOMKilled; evidencia de agotamiento bajo el límite aplicado.'
 elif any('shared memory' in e for e in errors):cause='Memoria compartida auxiliar de Docker agotada; problema de configuración, no prueba de OOM.'
 elif any('Muestras insuficientes' in e for e in errors):cause='cAdvisor terminó; ventana incompleta. Se conservan las métricas vacías sin interpolación.'
 elif i==48:cause='Timeout/cancelación; el usuario informó hibernación. No atribuir exclusivamente al motor.'
 elif any('WATCHDOG' in e for e in errors):cause='Control externo del cliente activado; muestras o fase incompletas. No tratar como throughput cero medido.'
 annex+=f"{i} & {tex(r['engine'])} {r['profile'].split('_')[1]} & {tex(r['query_id'])}, c={r['concurrency']}, r={r['run_number']} & {cause}"+r'\\'+'\n'
annex+=r'''\end{longtable}}
Los intentos interrumpidos por pausas del usuario o por bloqueo, sin ventana completa, se conservan en evidencias/interrumpidas. No se fabricó una fila de medición por cada carpeta vacía o incompleta. El CSV de todas las pruebas contiene sólo las 165 observaciones que llegaron a escribirse; no puede representar latencias no medidas.
\subsection{Problemas del entorno y controles incorporados}
Se documentaron hibernación, memoria compartida inicial de 64 MiB, cierre de cAdvisor y bloqueo del cliente. Las correcciones fueron: memoria compartida máxima de 1 GiB; reinicio de cAdvisor; timeout de conexión de quince segundos; opciones de sesión en conexión; procesos de carga aislados; y corte externo de 900 segundos por ejecutor con terminación del árbol de procesos. El conjunto primario contiene más de una versión del cliente; esta condición limita la comparabilidad de fallos y se declara en lugar de ocultarse.
\section{Verificaciones complementarias y archivos de entrega}
Se completaron tres de diez verificaciones planeadas. Las restantes se cancelaron por instrucción del alumno para cerrar el estudio conservando los fallos como evidencia. No se afirma que todas las incidencias del entorno hayan sido reejecutadas bajo una configuración homogénea.
\begin{center}\small\begin{tabular}{llrrr}\toprule Motor & Carga & Clientes & QPS & P99 (ms)\\\midrule
'''
for r in extra:annex+=' & '.join([tex(r['engine']),tex(r['query_id']),r['concurrency'],f"{float(r['throughput_qps']):.3f}",f"{float(r['latency_p99_ms']):.2f}"])+r'\\'+'\n'
annex+=r'''\bottomrule\end{tabular}\end{center}
Los archivos oficiales son: CSV de todas las observaciones con 14 columnas; matriz primaria original; suplemento de verificaciones; manifiesto de cierre; resumen con media, mediana y desviación; fuentes de consulta y generación; Compose y telemetría; planes; logs y muestras individuales; fuente LaTeX, PDF y guía para exposición. El repositorio conserva etiquetas de versión para esta entrega, sin publicación remota automática.
'''
s=s.replace(r'\end{document}',annex+r'\end{document}')
p.write_text(s,encoding='utf8')
# Persist final source as the canonical report; the draft generator is archived later.
print('Reporte actualizado con resultados y fallos')
