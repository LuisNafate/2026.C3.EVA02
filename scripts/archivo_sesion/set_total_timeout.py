from pathlib import Path
p=Path('scripts/run_suite.py');s=p.read_text(encoding='utf-8-sig')
s=s.replace('from pathlib import Path','from pathlib import Path\nfrom bounded_process import call_bounded')
s=s.replace('def run(*args,**kw):return subprocess.run(list(args),check=True,**kw)','def run(*args,**kw):return subprocess.run(list(args),check=True,timeout=120,**kw)')
old="  run(sys.executable,'benchmark_runner.py','--engine',engine,'--profile',profile,'--query',q,'--concurrency',str(c),'--run',str(r),'--variant',v)"
new='''  attempt_started=int(time.time());hard_timeout=False
  args=[sys.executable,'benchmark_runner.py','--engine',engine,'--profile',profile,'--query',q,'--concurrency',str(c),'--run',str(r),'--variant',v]
  try:
   call_bounded(args,timeout=900)
  except subprocess.TimeoutExpired:
   hard_timeout=True
   evidence=Path('evidencias')/f'{engine}_{profile}_{q}_{v}_{c}_{r}'
   evidence.mkdir(exist_ok=True)
   (evidence/'hard_timeout.json').write_text(json.dumps(dict(reason='Whole runner exceeded 900 seconds',attempt_started_epoch=attempt_started,measurement_valid=False,spill_known=False,process_tree_terminated=True),indent=2))
   path=Path('resultados/mediciones.csv')
   rows=list(csv.DictReader(path.open())) if path.exists() else []
   exists=any((x['engine'],x['profile'],x['query_id'],x['concurrency'],x['run_number'])==key for x in rows)
   if not exists:
    header='timestamp_epoch,engine,profile,query_id,concurrency,run_number,throughput_qps,latency_p50_ms,latency_p95_ms,latency_p99_ms,cpu_throttled_seconds,max_rss_mb,disk_spill,status'.split(',')
    with path.open('a',newline='') as f:
     writer=csv.writer(f)
     if f.tell()==0:writer.writerow(header)
     writer.writerow([attempt_started,engine,profile,key[2],c,r,'','','','','','','false','error'])
   # Stop server-side work too, then retain the standard cooldown before the next cell.
   run('docker','compose','stop','-t','10',service)
   time.sleep(60)'''
assert old in s;s=s.replace(old,new)
s=s.replace("   if not latest['cpu_throttled_seconds'] or not latest['max_rss_mb']:","   if not hard_timeout and (not latest['cpu_throttled_seconds'] or not latest['max_rss_mb']):")
p.write_text(s,encoding='utf8')
Path('evidencias/POLITICA_TIEMPOS.md').write_text('''# Límites de espera

Aplicable desde la próxima reanudación; el proyecto sigue pausado.

- Consultas: se mantiene el límite existente de 300 segundos.
- Ejecutor completo por corrida: máximo 900 segundos (15 minutos), incluyendo calentamiento, medición, esperas y cierre del cliente.
- Al excederlo se termina todo el árbol de procesos del cliente, se guarda hard_timeout.json, se detiene el servicio del motor para cancelar trabajo residual y se conserva un enfriamiento de 60 segundos antes de continuar.
- Operaciones externas de preparación/análisis: límite de 120 segundos por comando. Si fallan, el proyecto se detiene con diagnóstico; no se encadena otra medición con infraestructura incierta.
- El límite de 15 minutos corresponde al ejecutor; la recuperación, preparación y enfriamiento adicional pueden añadir tiempo. No es un límite total de toda la matriz ni un mecanismo de tiempo real frente a hibernación.

Si no hubo medición válida, la fila se marca error y las métricas quedan vacías. Su timestamp representa el inicio del intento; hard_timeout.json explicita que no es el inicio de una ventana válida. El booleano disk_spill=false de estas filas no demuestra ausencia de spill: el evento es desconocido y solo se conserva ese valor para respetar el esquema fijo. No se usan estas filas en el análisis de rendimiento ni de ausencia de spill. Si ya se escribió una fila completa antes de atascarse en el cierre, se conserva sin duplicarla y se añade la incidencia.

No se cambian las ventanas nominales 60/300/60, los perfiles, las consultas ni los resultados anteriores. El nuevo control puede cancelar consultas que excedan el presupuesto global y debe declararse en el método.
''',encoding='utf8')
