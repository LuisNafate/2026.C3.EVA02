import json, pathlib
p=pathlib.Path('.')
def put(n,s):
 q=p/n;q.parent.mkdir(parents=True,exist_ok=True);q.write_text(s.strip()+'\n',encoding='utf-8')
put('requirements.txt','pymongo>=4.10,<5\npsycopg[binary]>=3.2,<4\nrequests>=2.32,<3\npandas>=2.2,<4\nmatplotlib>=3.9,<4')
put('queries/q1_mongodb.js',json.dumps([{'$unwind':'$items'},{'$match':{'items.price':{'$gt':50}}},{'$group':{'_id':{'country':'$customer.geo.country','category':'$items.category'},'total_revenue':{'$sum':{'$multiply':['$items.qty','$items.price']}},'avg_revenue':{'$avg':{'$multiply':['$items.qty','$items.price']}},'count':{'$sum':1}}}],indent=2))
put('queries/q2_mongodb.js',json.dumps([{'$match':{'payment.status':'completed','timestamp':{'$gte':'2026-01-01T00:00:00Z'}}},{'$sort':{'payment.final_total':-1}},{'$limit':1000},{'$project':{'order_id':1,'customer.id':1,'payment.final_total':1}}],indent=2))
put('queries/q1_postgres.sql',"""SELECT data->'customer'->'geo'->>'country' AS country, item->>'category' AS category,
SUM((item->>'qty')::numeric*(item->>'price')::numeric) AS total_revenue,
AVG((item->>'qty')::numeric*(item->>'price')::numeric) AS avg_revenue, COUNT(*) AS count
FROM orders CROSS JOIN LATERAL jsonb_array_elements(data->'items') AS item
WHERE (item->>'price')::numeric>50 GROUP BY 1,2;""")
put('queries/q2_postgres.sql',"""SELECT data->>'order_id' AS order_id,data->'customer'->>'id' AS customer_id,
(data->'payment'->>'final_total')::numeric AS final_total FROM orders
WHERE data->'payment'->>'status'='completed' AND data->>'timestamp'>='2026-01-01T00:00:00Z'
ORDER BY (data->'payment'->>'final_total')::numeric DESC LIMIT 1000;""")
put('docker-compose.yml','''name: eva02
services:
  mongodb:
    image: mongo:8.0
    ports: ["127.0.0.1:27017:27017"]
    cpus: ${DB_CPUS:-4}
    mem_limit: ${DB_MEMORY:-4096m}
    memswap_limit: ${DB_MEMORY:-4096m}
    volumes: ["mongo_data:/data/db"]
  postgres:
    image: postgres:17
    environment:
      POSTGRES_PASSWORD: eva02_local
      POSTGRES_DB: eva02
    command: ["postgres", "-c", "log_temp_files=0"]
    ports: ["127.0.0.1:5432:5432"]
    cpus: ${DB_CPUS:-4}
    mem_limit: ${DB_MEMORY:-4096m}
    memswap_limit: ${DB_MEMORY:-4096m}
    volumes: ["pg_data:/var/lib/postgresql/data"]
  prometheus:
    image: prom/prometheus:v3.2.1
    ports: ["127.0.0.1:9090:9090"]
    volumes: ["./config/prometheus.yml:/etc/prometheus/prometheus.yml:ro"]
  cadvisor:
    image: gcr.io/cadvisor/cadvisor:v0.49.2
    privileged: true
    volumes:
      - /:/rootfs:ro
      - /var/run:/var/run:ro
      - /sys:/sys:ro
      - /var/lib/docker:/var/lib/docker:ro
      - /sys/fs/cgroup:/sys/fs/cgroup:ro
  node-exporter:
    image: prom/node-exporter:v1.9.0
    command: ["--path.rootfs=/host"]
    volumes: ["/:/host:ro,rslave"]
volumes:
  mongo_data:
  pg_data:
''')
put('config/prometheus.yml','''global:
  scrape_interval: 1s
scrape_configs:
  - job_name: containers
    static_configs:
      - targets: ["cadvisor:8080"]
  - job_name: host
    static_configs:
      - targets: ["node-exporter:9100"]''')
