from pathlib import Path
p=Path('benchmark_runner.py');s=p.read_text(encoding='utf-8-sig');s=s.replace("barrier=threading.Barrier(n+1);lat=[];errors=[];lock=threading.Lock();bounds={}","bounds={}\n def begin():bounds.update(end=time.monotonic()+seconds,epoch=time.time())\n barrier=threading.Barrier(n+1,action=begin);lat=[];errors=[];lock=threading.Lock()")
s=s.replace("bounds['end']=time.monotonic()+seconds;epoch=time.time()","epoch=time.time()")
s=s.replace("return epoch,lat,errors","return bounds.get('epoch',epoch),lat,errors")
s=s.replace("phase(o.engine,o.query,o.variant,o.concurrency,60)","_,_,warm_errors=phase(o.engine,o.query,o.variant,o.concurrency,60)\n if warm_errors:raise RuntimeError('Warmup fallido: '+str(warm_errors[:3]))")
s=s.replace("else ('spill' if spill else 'ok'))","else ('spill' if spill else 'ok'))")
s=s.replace("'container_memory_rss')","'container_memory_rss')")
p.write_text(s,encoding='utf8')
