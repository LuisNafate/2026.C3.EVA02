"""Deterministic streaming dataset; load identical batches into both engines."""
import argparse, random, uuid, json, hashlib
from datetime import datetime,timedelta,timezone
from pathlib import Path

def documents(n,seed):
 r=random.Random(seed)
 for i in range(n):
  items=[dict(sku=f'SKU-{r.randrange(10000)}',category=r.choice(['Electronics','Home','Sports','Books']),brand='Demo',qty=r.randint(1,5),price=r.randint(100,30000)/100,tax_pct=.16,discounts=0) for _ in range(3)]
  subtotal=round(sum(x['qty']*x['price'] for x in items),2);tax=round(subtotal*.16,2)
  yield dict(order_id=str(uuid.UUID(int=r.getrandbits(128),version=4)),timestamp=(datetime(2025,7,1,tzinfo=timezone.utc)+timedelta(seconds=r.randrange(365*86400))).strftime('%Y-%m-%dT%H:%M:%SZ'),customer=dict(id=f'cust_{i%10000}',tier=r.choice(['gold','silver','regular']),segment='retail',geo=dict(country=r.choice(['MX','US','CA']),state='Chiapas',city='Tuxtla',zip='29000',coordinates=[-93.1167,16.75])),items=items,payment=dict(method='credit_card',status=r.choice(['completed','pending','failed','refunded']),transaction_id=f'tx_{i}',gateway_latency_ms=r.randint(10,500),totals=dict(subtotal=subtotal,tax=tax,discount=0),final_total=round(subtotal+tax,2)),metadata=dict(channel='web',user_agent='EVA02',session_id=f'sess_{i}',flags=[]))

def main():
 a=argparse.ArgumentParser();a.add_argument('--count',type=int,default=500000);a.add_argument('--seed',type=int,default=2026);a.add_argument('--load',action='store_true');o=a.parse_args()
 Path('resultados').mkdir(exist_ok=True);h=hashlib.sha256()
 if o.load:
  from pymongo import MongoClient
  import psycopg
  from psycopg.types.json import Jsonb
  m=MongoClient('mongodb://127.0.0.1:27018').eva02.orders
  c=psycopg.connect('postgresql://postgres:eva02_local@127.0.0.1/eva02',autocommit=True)
  c.execute('CREATE TABLE IF NOT EXISTS orders(id uuid PRIMARY KEY,data jsonb NOT NULL)')
  if m.count_documents({}) or c.execute('SELECT count(*) FROM orders').fetchone()[0]:raise RuntimeError('Carga rechazada: bases no vacias; no se borran datos automaticamente')
 batch=[]
 with open('resultados/orders.jsonl','w',encoding='utf8') as f:
  for d in documents(o.count,o.seed):
   line=json.dumps(d,sort_keys=True,separators=(',',':'));f.write(line+'\n');h.update((line+'\n').encode());batch.append(d)
   if len(batch)==1000:
    if o.load:
     m.insert_many([dict(x) for x in batch]);
     with c.cursor() as cur:cur.executemany('INSERT INTO orders VALUES (%s,%s)',[(x['order_id'],Jsonb(x)) for x in batch])
    batch=[]
  if batch and o.load:
   m.insert_many([dict(x) for x in batch])
   with c.cursor() as cur:cur.executemany('INSERT INTO orders VALUES (%s,%s)',[(x['order_id'],Jsonb(x)) for x in batch])
 if o.load:
  m.create_index('timestamp');m.create_index('order_id')
  c.execute("CREATE INDEX IF NOT EXISTS idx_orders_timestamp ON orders ((data->>'timestamp'))")
  c.execute('ANALYZE orders')
  assert m.count_documents({})==c.execute('SELECT count(*) FROM orders').fetchone()[0]==o.count
 Path('resultados/dataset_manifest.json').write_text(json.dumps(dict(count=o.count,seed=o.seed,sha256=h.hexdigest(),loaded=o.load),indent=2))
if __name__=='__main__':main()


