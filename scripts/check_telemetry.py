import requests,subprocess
cid=subprocess.check_output(['docker','compose','ps','-q','mongodb'],text=True).strip()
q='container_cpu_cfs_throttled_seconds_total{id="/docker/'+cid+'"}'
r=requests.get('http://127.0.0.1:9090/api/v1/query',params={'query':q}).json()
print(r)
assert len(r['data']['result'])==1
