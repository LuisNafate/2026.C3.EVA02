import sys,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import benchmark_runner as runner
class Connection:
 def close(self):pass
def fake_client(engine,q,variant):
 def execute():time.sleep(20 if variant=='hang' else .005)
 return Connection(),execute
runner.client=fake_client
if __name__=='__main__':
 epoch,lat,errors=runner.phase('fake','Q1','normal',2,.1,grace=3)
 assert lat and not errors,(lat,errors)
 started=time.monotonic()
 epoch,lat,errors=runner.phase('fake','Q1','hang',1,.1,grace=1)
 assert not lat and any('WATCHDOG:' in e for e in errors)
 assert time.monotonic()-started<5
 print('OK: muestras de clientes concurrentes y terminacion de proceso bloqueado')
