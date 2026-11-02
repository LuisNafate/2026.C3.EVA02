import argparse,csv,json,time,statistics,threading,concurrent.futures,subprocess
from pathlib import Path
import requests
HEADER='timestamp_epoch,engine,profile,query_id,concurrency,run_number,throughput_qps,latency_p50_ms,latency_p95_ms,latency_p99_ms,cpu_throttled_seconds,max_rss_mb,disk_spill,status'.split(',')
def percentile(x,p):
 if not x:return ''
 x=sorted(x);k=(len(x)-1)*p;lo=int(k);return x[lo]+(x[min(lo+1,len(x)-1)]-x[lo])*(k-lo)
def client(engine,q,variant):
 if engine=='mongodb':
  from pymongo import MongoClient
  conn=MongoClient('mongodb://127.0.0.1:27018',serverSelectionTimeoutMS=10000,socketTimeoutMS=310000)
  pipeline=json.loads(Path(f'queries/{q.lower()}_mongodb.js').read_text())
  return conn,lambda:list(conn.eva02.orders.aggregate(pipeline,allowDiskUse=variant!='nodisk',maxTimeMS=300000))
 import psycopg
 conn=psycopg.connect('postgresql://postgres:eva02_local@127.0.0.1/eva02',autocommit=True,connect_timeout=15,options='-c statement_timeout=300000 -c work_mem='+('64MB' if variant=='64MB' else '4MB'))

 sql=Path(f'queries/{q.lower()}_postgres.sql').read_text()
 return conn,lambda:conn.execute(sql).fetchall()
def _thread_phase(engine,q,variant,n,seconds,notify=None):
 bounds={}
 def begin():
  bounds.update(end=time.monotonic()+seconds,epoch=time.time())
  if notify:notify(('started',bounds['epoch']))
 barrier=threading.Barrier(n+1,action=begin);lat=[];errors=[];lock=threading.Lock()
 def worker():
  conn=None
  try:conn,execute=client(engine,q,variant)
  except Exception as e:errors.append(str(e));barrier.abort();return
  try:
   try:barrier.wait(timeout=30)
   except threading.BrokenBarrierError:
    with lock:errors.append("Inicio concurrente abortado: conexiones no disponibles")
    return
   while time.monotonic()<bounds['end']:
    start=time.monotonic()
    try:
     execute();end=time.monotonic()
     if end<=bounds['end']:
      with lock:lat.append((end-start)*1000)
    except Exception as e:
     with lock:errors.append(str(e))
     break
  finally:conn.close()
 with concurrent.futures.ThreadPoolExecutor(max_workers=n) as pool:
  jobs=[pool.submit(worker) for _ in range(n)]
  epoch=time.time()
  try:barrier.wait(timeout=30)
  except threading.BrokenBarrierError:pass
  for job in jobs:job.result()
 # Preserve a full observation window even when every connection fails.
 deadline=bounds.get('end',time.monotonic()+max(0,seconds-(time.time()-epoch)))
 remaining=deadline-time.monotonic()
 if remaining>0:time.sleep(remaining)
 return bounds.get('epoch',epoch),lat,errors


def _phase_process(pipe,engine,q,variant,n,seconds):
 try:
  result=_thread_phase(engine,q,variant,n,seconds,notify=pipe.send)
  pipe.send(('result',result))
 except BaseException as exc:
  pipe.send(('failure',repr(exc)))
 finally:pipe.close()

def phase(engine,q,variant,n,seconds,grace=375):
 # Isolate clients so a stalled native driver cannot hold the suite indefinitely.
 import multiprocessing
 ctx=multiprocessing.get_context('spawn')
 parent,child=ctx.Pipe(duplex=False)
 process=ctx.Process(target=_phase_process,args=(child,engine,q,variant,n,seconds))
 process.start();child.close()
 epoch=None;deadline=time.monotonic()+seconds+grace
 try:
  while time.monotonic()<deadline:
   if parent.poll(min(1,max(0,deadline-time.monotonic()))):
    try:kind,value=parent.recv()
    except EOFError:break
    if kind=='started':epoch=value
    elif kind=='result':
     process.join(timeout=5)
     return value
    elif kind=='failure':return epoch or time.time(),[],['WATCHDOG: worker failure '+value]
   elif not process.is_alive():break
  return epoch or time.time(),[],['WATCHDOG: phase did not finish within bounded execution; latency samples unavailable; not a measured zero-throughput result']
 finally:
  if process.is_alive():process.terminate()
  process.join(timeout=10);parent.close()

def main():
 a=argparse.ArgumentParser();a.add_argument('--engine',choices=['mongodb','postgresql'],required=True);a.add_argument('--query',choices=['Q1','Q2'],required=True);a.add_argument('--profile',required=True);a.add_argument('--concurrency',type=int,choices=[1,10,50],default=1);a.add_argument('--run',type=int,default=1);a.add_argument('--variant',default='nodisk');a.add_argument('--csv',default='resultados/mediciones.csv');a.add_argument('--evidence-root',default='evidencias');o=a.parse_args()
 service='postgres' if o.engine=='postgresql' else 'mongodb'
 cid=subprocess.check_output(['docker','compose','ps','-q',service],text=True).strip()
 if not cid:raise RuntimeError('Contenedor ausente')
 out=Path(o.evidence_root)/f'{o.engine}_{o.profile}_{o.query}_{o.variant}_{o.concurrency}_{o.run}';out.mkdir(parents=True,exist_ok=False)
 _,_,warm_errors=phase(o.engine,o.query,o.variant,o.concurrency,60)
 (out/'warmup_errors.json').write_text(json.dumps(warm_errors,indent=2),encoding='utf8')
 # Keep load-related warmup failures as evidence; still attempt the measurement window.
 epoch,lat,errors=phase(o.engine,o.query,o.variant,o.concurrency,300);end=epoch+300
 measured_samples_unavailable=any('WATCHDOG:' in e for e in errors)
 errors=['Warmup: '+e for e in warm_errors]+errors
 selector='{id=~".*'+cid+'.*"}'
 telemetry={};metrics={};bad=False
 for key,metric in [('cpu','container_cpu_cfs_throttled_seconds_total'),('rss','container_memory_rss')]:
  try:
   data=requests.get('http://127.0.0.1:9090/api/v1/query_range',params=dict(query=metric+selector,start=epoch,end=end,step=1),timeout=30).json();telemetry[key]=data
   series=data['data']['result'];assert len(series)==1,'Telemetria ausente o ambigua'
   vals=[float(v) for _,v in series[0]['values']];assert len(vals)>=290,'Muestras insuficientes'
   if key=='cpu':
    assert all(b>=a for a,b in zip(vals,vals[1:])),'Contador reiniciado';metrics[key]=vals[-1]-vals[0]
   else:metrics[key]=max(vals)/1e6
  except Exception as e:errors.append(str(e));bad=True;metrics[key]=''
 Path(out/'window.json').write_text(json.dumps({'start':epoch,'end':end}))
 logs=subprocess.check_output(['docker','compose','logs','--since',str(int(epoch)),service],text=True,errors='replace')
 state=json.loads(subprocess.check_output(['docker','inspect',cid],text=True))[0]
 oom=state['State']['OOMKilled'];spill=('temporary file:' in logs) if o.engine=='postgresql' else ('"usedDisk":true' in logs.replace(' ',''))
 status='oom' if oom else ('error' if errors or bad or not lat else ('spill' if spill else 'ok'))
 (out/'logs.txt').write_text(logs,encoding='utf8');(out/'inspect.json').write_text(json.dumps(state,indent=2));(out/'telemetry.json').write_text(json.dumps(telemetry));(out/'samples.json').write_text(json.dumps(dict(latency_ms=lat,errors=errors,start=epoch,end=end)))
 path=Path(o.csv);path.parent.mkdir(exist_ok=True)
 row=[int(epoch),o.engine,o.profile,o.query+('_'+o.variant if o.query=='Q2' else ''),o.concurrency,o.run,('' if measured_samples_unavailable else len(lat)/300),*[percentile(lat,p) for p in [.5,.95,.99]],metrics['cpu'],metrics['rss'],str(spill).lower(),status]
 with path.open('a',newline='') as f:
  w=csv.writer(f)
  if f.tell()==0:w.writerow(HEADER)
  w.writerow(row)
 time.sleep(60)
if __name__=='__main__':main()


