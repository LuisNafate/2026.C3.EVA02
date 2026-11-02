import json,csv
from pathlib import Path
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
root=Path(__file__).resolve().parents[1]
out=root/'informe';out.mkdir(exist_ok=True)
f=root/'resultados/mediciones.csv'
if not f.exists():raise SystemExit('Sin mediciones reales: no se generan figuras ficticias')
df=pd.read_csv(f);good=df[df.status.isin(['ok','spill'])]
metrics=['throughput_qps','latency_p50_ms','latency_p95_ms','latency_p99_ms','cpu_throttled_seconds','max_rss_mb']
summary=good.groupby(['engine','profile','query_id','concurrency'])[metrics].agg(['count','mean','median','std'])
summary.to_csv(out/'resumen.csv')
plt.rcParams.update({'figure.figsize':(11,7),'font.size':10,'axes.grid':True})
fig,axes=plt.subplots(2,2,figsize=(13,9))
for ax,(engine,q) in zip(axes.flat,[(e,q) for e in ['mongodb','postgresql'] for q in ['Q1','Q2']]):
 sub=good[(good.engine==engine)&good.query_id.str.startswith(q)]
 for (profile,query),g in sub.groupby(['profile','query_id']):
  means=g.groupby('concurrency').latency_p99_ms.mean();ax.plot(means.index,means.values,marker='o',label=profile.replace('PROFILE_','')+' '+query)
 ax.set(title=f'{engine} {q}',xlabel='Clientes',ylabel='P99 (ms)');ax.legend(fontsize=6)
fig.suptitle('P99 de cada corrida, promediado entre repeticiones');fig.tight_layout();fig.savefig(out/'p99_concurrencia.png',dpi=150);plt.close(fig)
fig,ax=plt.subplots()
for engine,g in good.groupby('engine'):ax.scatter(g.cpu_throttled_seconds,g.throughput_qps,label=engine,alpha=.7)
ax.set(xlabel='Tiempo de throttling (s)',ylabel='Consultas exitosas/s',title='Contención y rendimiento; asociación, no prueba causal aislada');ax.legend();fig.tight_layout();fig.savefig(out/'throttling_qps.png',dpi=150);plt.close(fig)
fig,ax=plt.subplots();seen=set()
for path in sorted((root/'evidencias').glob('*Q2*/telemetry.json')):
 name=path.parent.name;parts=name.split('_');label=parts[0]+' '+('disk' if '_disk_' in name else 'nodisk' if '_nodisk_' in name else '64MB' if '_64MB_' in name else '4MB')
 if label in seen:continue
 data=json.loads(path.read_text());series=data.get('rss',{}).get('data',{}).get('result',[])
 if not series:continue
 values=series[0]['values'];t0=float(values[0][0]);ax.plot([float(t)-t0 for t,v in values],[float(v)/1e6 for t,v in values],label=name,linewidth=1);seen.add(label)
ax.set(xlabel='Segundos desde inicio',ylabel='RSS (MB decimales)',title='Q2: RSS observado por variante; consultar logs para confirmar spill');ax.legend(fontsize=5);fig.tight_layout();fig.savefig(out/'rss_temporal.png',dpi=150);plt.close(fig)
counts=df.status.value_counts().to_dict();complete=len(df)==162
report=f'''# EVA02: MongoDB frente a PostgreSQL JSONB

Estado: {'mediciones reunidas; requiere revisión final' if complete else 'PARCIAL: experimento en ejecución'}. Corridas registradas: {len(df)}/162. Estados: {counts}.

## 1. Especificaciones del host y entorno Docker
Ryzen 5 7640HS, 6 núcleos/12 hilos; 40 GiB de RAM, módulos DDR5; SSD NVMe. Windows 11, Docker Desktop y WSL2. Detalles medidos en `../evidencias/host.json`; versiones exactas de motores en `../evidencias/validacion/comparabilidad.json`. Los digests de imágenes y configuración deben acompañar la entrega. El cliente corre en Windows y los motores dentro de la VM Linux.

## 2. Método de medición y verificación del baseline
Dataset determinista: semilla 2026, 500000 documentos, tres ítems por orden. Conteo y hash canónico completo entre motores, y equivalencia de Q1/Q2, se validan antes de medir. Q1 compara valores numéricos con tolerancia relativa 1e-9; Q2 compara valores ordenados, porque hay empates.

Perfiles A/B/C: 4/2/1 CPU y 4096/2048/1024 MiB. Swap se deshabilita igualando memswap_limit a mem_limit. No se emplea mem_swappiness, que no tiene equivalente por cgroup en v2. Se ejecuta un solo motor a la vez. Flush en el kernel Docker Desktop, warmup 60 s, medida 300 s, cooldown 60 s. Las conexiones se preparan antes de la barrera de inicio. Se consume el resultado completo. Solo cuentan consultas completadas dentro de la ventana; quedan latencias censuradas al final, una limitación del protocolo.

La matriz principal contiene 108 corridas. Se añade la segunda variante Q2 de cada motor: total 162, 18 h 54 min mínimas más preparación y drenado. Q1 usa nodisk; Q2 Mongo nodisk/disk y PostgreSQL 4MB/64MB. Los query_id conservan las variantes sin modificar las 14 columnas.

El índice PostgreSQL usa texto ISO UTC de longitud fija; la consulta Q2 usa el mismo predicado textual. Es equivalente para este dataset, no para timestamps arbitrarios con otros husos. Se documenta esta adaptación porque el cast directo a timestamptz no es inmutable para un índice de expresión. No se supone que A esté libre de throttling: debe evaluarse en el CSV.

## 3. Resultados consolidados
`resumen.csv` incluye conteo, media, mediana y desviación estándar por celda y variante. Se excluyen error/oom de los resúmenes de rendimiento y se conservan en el CSV original. Los percentiles usan interpolación lineal; P50 equivale a la mediana. El promedio de P99 por corrida no representa el P99 de todas las muestras combinadas.

Corridas actuales: {len(df)}; válidas para rendimiento: {len(good)}. No se declara un ganador antes de completar las repeticiones. Telemetría ausente produce error y campos vacíos, nunca ceros inventados.

## 4. Análisis gráfico
![P99](p99_concurrencia.png)

![Throttling](throttling_qps.png)

![RSS](rss_temporal.png)

Los gráficos se actualizan tras cada corrida y son parciales hasta completar la matriz. RSS es memoria anónima residente reportada por cAdvisor, no memoria total del contenedor. Correlación CPU/QPS no separa el efecto de RAM porque los perfiles cambian ambas variables.

## 5. Planes de ejecución
Planes reales fuera de la ventana en `../evidencias/validacion/`. Q1 permite contrastar unwind/group con expansión lateral y agregado. Q2 permite identificar top-N frente a ordenamiento externo. Los planes iniciales corresponden al baseline; no prueban por sí solos el plan de cada perfil. Validar nodos y métricas antes de atribuir un cuello de botella.

## 6. Interpretación de límites, spill y throttling
CPU está limitada por cuota periódica del planificador; reducir cuotas puede aumentar espera y cola. El contador acumulado se convierte a delta por ventana, verificando que no se reinicie. WiredTiger y la memoria del pipeline son presupuestos distintos; work_mem es por operación y puede multiplicarse por sesiones y trabajadores.

Top-1000 puede mantener un conjunto acotado, por lo que 4MB o allowDiskUse=true no garantizan spill. Los logs Mongo registran usedDisk y PostgreSQL archivos temporales. Un error por límite de sort no implica OOM; OOM requiere Docker inspect/cgroup. La ausencia de eventos no se transforma en un evento ficticio. La muestra por segundo puede perder picos subsegundo. Para M3 se requiere CPU utilizada y documentos examinados de planes; throttling y pico RSS no sustituyen el costo por 1000 documentos.

## 7. Recomendaciones para despliegues documentales en la nube
Elegir el motor según consultas, transacciones y esquema, y confirmar con la carga real. Ajustar concurrencia y cuotas observando P99 además de QPS. Dimensionar work_mem considerando operaciones y conexiones simultáneas; no multiplicar buffers indiscriminadamente. Definir presupuestos de memoria separados para caché y agregaciones. Estas son pautas de diseño, no una conclusión empírica de superioridad en este equipo.

Fuentes técnicas: [MongoDB sort y Top-K](https://www.mongodb.com/docs/v8.0/reference/operator/aggregation/sort/), [PostgreSQL CREATE INDEX](https://www.postgresql.org/docs/17/sql-createindex.html). Contrato académico: los dos playbooks originales de la raíz.
'''
(out/'REPORTE.md').write_text(report,encoding='utf8')
