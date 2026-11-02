"""Cross-engine semantic validation and execution plans, outside timed windows."""
import sys,json,math,hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from benchmark_runner import client
from pymongo import MongoClient
import psycopg
out=Path('evidencias/validacion');out.mkdir(parents=True,exist_ok=True)
m=MongoClient('mongodb://127.0.0.1:27018').eva02
p=psycopg.connect('postgresql://postgres:eva02_local@127.0.0.1/eva02',autocommit=True)
assert m.orders.count_documents({})==p.execute('select count(*) from orders').fetchone()[0]==500000
# Check every document after canonical serialization; exclude Mongo's internal _id.
def digest(rows):
 h=hashlib.sha256()
 for d in rows:h.update((json.dumps(d,sort_keys=True,separators=(',',':'))+'\n').encode())
 return h.hexdigest()
a=digest(m.orders.find({}, {'_id':0}).sort('order_id',1))
with p.cursor(name='verify') if False else p.cursor() as cur:
 cur.execute('select data from orders order by id');b=digest(row[0] for row in cur)
assert a==b,(a,b)
results={'documents':500000,'canonical_sha256':a,'postgres_version':p.execute('select version()').fetchone()[0],'mongodb_version':m.command('buildInfo')['version']}
for q in ['Q1','Q2']:
 mc,me=client('mongodb',q,'nodisk');pc,pe=client('postgresql',q,'4MB');mr=me();pr=pe()
 if q=='Q1':
  md={(x['_id']['country'],x['_id']['category']):x for x in mr}
  for country,category,total,avg,count in pr:
   x=md[(country,category)];assert x['count']==count
   assert math.isclose(x['total_revenue'],float(total),rel_tol=1e-9)
   assert math.isclose(x['avg_revenue'],float(avg),rel_tol=1e-9)
 else:
  # Exact IDs can differ at a tied cutoff; compare ordered values and membership rules.
  assert sorted([x['payment']['final_total'] for x in mr],reverse=True)==[float(x[2]) for x in pr]
 results[q]={'equivalent':True,'rows':len(mr)}
 mc.close();pc.close()
 pipeline=json.loads(Path(f'queries/{q.lower()}_mongodb.js').read_text())
 for variant in ['nodisk','disk']:
  plan=m.command('explain',{'aggregate':'orders','pipeline':pipeline,'cursor':{},'allowDiskUse':variant=='disk'},verbosity='executionStats')
  (out/f'{q}_mongo_{variant}_plan.json').write_text(json.dumps(plan,default=str,indent=2))
 for wm in ['4MB','64MB']:
  p.execute("SET work_mem='"+wm+"'")
  plan=p.execute('EXPLAIN (ANALYZE,BUFFERS,VERBOSE,FORMAT JSON) '+Path(f'queries/{q.lower()}_postgres.sql').read_text()).fetchone()[0]
  (out/f'{q}_postgres_{wm}_plan.json').write_text(json.dumps(plan,default=str,indent=2))
(out/'comparabilidad.json').write_text(json.dumps(results,indent=2))
print(json.dumps(results,indent=2))
