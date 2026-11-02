"""Sequential Windows orchestrator; flushes the actual Docker Desktop kernel."""
import os,sys,subprocess,time,json,csv,itertools,traceback
from pathlib import Path
from bounded_process import call_bounded
ROOT=Path(__file__).resolve().parents[1];os.chdir(ROOT)
def run(*args,**kw):return subprocess.run(list(args),check=True,timeout=120,**kw)
def state(**kw):Path('resultados/estado.json').write_text(json.dumps(kw,indent=2),encoding='utf8')
def main():
 if not Path('evidencias/validacion/comparabilidad.json').exists():run(sys.executable,'scripts/validate.py')
 jobs=[]
 for engine,profile,q,c,r in itertools.product(['mongodb','postgresql'],['PROFILE_A_BASELINE','PROFILE_B_MEDIUM','PROFILE_C_SEVERE'],['Q1','Q2'],[1,10,50],[1,2,3]):
  for v in (['nodisk','disk'] if engine=='mongodb' else ['4MB','64MB']) if q=='Q2' else ['nodisk']:
   jobs.append((engine,profile,q,c,r,v))
 for i,(engine,profile,q,c,r,v) in enumerate(jobs):
  key=(engine,profile,q+('_'+v if q=='Q2' else ''),str(c),str(r))
  done=set()
  if Path('resultados/mediciones.csv').exists():
   with open('resultados/mediciones.csv') as f:
    done={(x['engine'],x['profile'],x['query_id'],x['concurrency'],x['run_number']) for x in csv.DictReader(f)}
  if key in done:continue
  cpu,mem={'PROFILE_A_BASELINE':('4','4096m'),'PROFILE_B_MEDIUM':('2','2048m'),'PROFILE_C_SEVERE':('1','1024m')}[profile]
  env=dict(os.environ,DB_CPUS=cpu,DB_MEMORY=mem)
  service='mongodb' if engine=='mongodb' else 'postgres'
  state(status='running',current=i+1,total=len(jobs),engine=engine,profile=profile,query=q,concurrency=c,repeat=r,variant=v)
  run('docker','compose','stop','mongodb','postgres',stdout=subprocess.DEVNULL)
  run('docker','compose','up','-d',service,env=env)
  time.sleep(15)
  run('wsl','-d','docker-desktop','-u','root','--','sh','-c','sync; echo 3 > /proc/sys/vm/drop_caches')
  attempt_started=int(time.time());hard_timeout=False
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
   time.sleep(60)
  run(sys.executable,'scripts/analyze.py')
  with open('resultados/mediciones.csv') as f:latest=list(csv.DictReader(f))[-1]
  if latest['status']=='error':
   # Query timeouts are experimental outcomes; retain the row and continue.
   # Missing telemetry prevents valid resource comparisons and still stops the suite.
   if not hard_timeout and (not latest['cpu_throttled_seconds'] or not latest['max_rss_mb']):
    raise RuntimeError('Telemetria incompleta: revisar antes de continuar')
 state(status='measurements_finished',total=len(jobs),next='Review report and figures before declaring delivery complete')
if __name__=='__main__':
 try:main()
 except Exception:
  state(status='failed',error=traceback.format_exc());raise
