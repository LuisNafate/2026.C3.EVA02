"""Repeat only predeclared invalid attempts; preserve originals and failed outcomes."""
import os,sys,csv,json,time,subprocess,traceback
from pathlib import Path
from bounded_process import call_bounded
os.chdir(Path(__file__).resolve().parents[1])
def state(**kw):Path('resultados/estado.json').write_text(json.dumps(kw,indent=2),encoding='utf8')
def run(*a,**kw):subprocess.run(a,check=True,timeout=120,**kw)
def key(r):return tuple(r[k] for k in ['engine','profile','query_id','concurrency','run_number'])
def main():
 original=list(csv.DictReader(open('resultados/mediciones.csv')))
 # Fixed before observing rerun outcomes: no cherry-picking successes.
 numbers=[48,*range(82,90),95]
 plan=[dict(original[n-1],original_run_position=n,reason='hibernation' if n==48 else 'missing_telemetry' if n==95 else 'pre_shm_adjustment') for n in numbers]
 Path('resultados/repeticiones_plan.json').write_text(json.dumps(plan,indent=2))
 target=Path('resultados/repeticiones.csv')
 header=list(original[0])
 for i,row in enumerate(plan,1):
  done=list(csv.DictReader(target.open())) if target.exists() else []
  if any(key(r)==key(row) for r in done):continue
  engine=row['engine'];profile=row['profile'];q=row['query_id'].split('_')[0]
  variant=row['query_id'].split('_',1)[1] if q=='Q2' else 'nodisk'
  c=row['concurrency'];r=row['run_number'];service='postgres' if engine=='postgresql' else 'mongodb'
  cpu,mem={'PROFILE_A_BASELINE':('4','4096m'),'PROFILE_B_MEDIUM':('2','2048m'),'PROFILE_C_SEVERE':('1','1024m')}[profile]
  state(status='running',phase='validation_reruns',current=i,total=len(plan),original_position=row['original_run_position'],engine=engine,profile=profile,query=q,concurrency=int(c),repeat=int(r),variant=variant)
  run('docker','compose','stop','-t','10','mongodb','postgres')
  run('docker','compose','up','-d',service,env=dict(os.environ,DB_CPUS=cpu,DB_MEMORY=mem));time.sleep(15)
  run('wsl','-d','docker-desktop','-u','root','--','sh','-c','sync; echo 3 > /proc/sys/vm/drop_caches')
  started=int(time.time())
  try:
   call_bounded([sys.executable,'benchmark_runner.py','--engine',engine,'--profile',profile,'--query',q,'--variant',variant,'--concurrency',c,'--run',r,'--csv',str(target),'--evidence-root','evidencias/repeticiones'],timeout=900)
  except subprocess.TimeoutExpired:
   folder=Path('evidencias/repeticiones')/f'{engine}_{profile}_{q}_{variant}_{c}_{r}';folder.mkdir(parents=True,exist_ok=True)
   (folder/'hard_timeout.json').write_text(json.dumps(dict(attempt_started_epoch=started,measurement_valid=False,reason='900s total timeout')))
   done=list(csv.DictReader(target.open())) if target.exists() else []
   if not any(key(x)==key(row) for x in done):
    with target.open('a',newline='') as f:
     w=csv.writer(f)
     if f.tell()==0:w.writerow(header)
     w.writerow([started,engine,profile,row['query_id'],c,r,'','','','','','','false','error'])
   run('docker','compose','stop','-t','10',service);time.sleep(60)
 state(status='reruns_finished',phase='analysis_and_delivery',original_runs=162,reruns=len(plan),next='Audit selection; finalize LaTeX/PDF and Git delivery')
if __name__=='__main__':
 try:main()
 except Exception:state(status='failed',phase='validation_reruns',error=traceback.format_exc());raise
