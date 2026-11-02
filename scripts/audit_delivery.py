from pathlib import Path
import csv,json,collections,math,statistics
root=Path('.')
header='timestamp_epoch,engine,profile,query_id,concurrency,run_number,throughput_qps,latency_p50_ms,latency_p95_ms,latency_p99_ms,cpu_throttled_seconds,max_rss_mb,disk_spill,status'.split(',')
results=[];checked=0
for filename,folder in [('mediciones.csv',Path('evidencias')),('repeticiones.csv',Path('evidencias/repeticiones'))]:
 with open(root/'resultados'/filename,newline='') as f:
  reader=csv.DictReader(f);assert reader.fieldnames==header;rows=list(reader)
 assert len({tuple(r[k] for k in ['engine','profile','query_id','concurrency','run_number']) for r in rows})==len(rows)
 for i,r in enumerate(rows,1):
  assert r['status'] in ['ok','spill','error','oom']
  q=r['query_id'].split('_')[0];v=r['query_id'].split('_',1)[1] if q=='Q2' else 'nodisk'
  p=folder/f"{r['engine']}_{r['profile']}_{q}_{v}_{r['concurrency']}_{r['run_number']}"/'samples.json'
  if not p.exists():continue
  samples=json.loads(p.read_text(encoding='utf8'));lat=sorted(samples['latency_ms'])
  if lat:
   for name,frac in [('latency_p50_ms',.5),('latency_p95_ms',.95),('latency_p99_ms',.99)]:
    k=(len(lat)-1)*frac;lo=int(k);expected=lat[lo]+(lat[min(lo+1,len(lat)-1)]-lat[lo])*(k-lo)
    assert math.isclose(float(r[name]),expected,rel_tol=1e-10),(filename,i,name)
   assert math.isclose(float(r['throughput_qps']),len(lat)/300,rel_tol=1e-10)
   checked+=1
 results.append(dict(file=filename,rows=len(rows),status_counts=dict(collections.Counter(r['status'] for r in rows))))
assert results[0]['rows']==162 and results[1]['rows']==3
(root/'resultados/auditoria_entrega.json').write_text(json.dumps(dict(schema_columns=14,percentiles_and_qps_recomputed_rows=checked,files=results,primary_analysis='mediciones.csv',supplements='repeticiones.csv',failure_retention=True),indent=2),encoding='utf8')
print('Auditoria OK; filas con percentiles recalculados:',checked)
