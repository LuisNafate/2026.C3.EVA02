import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pathlib import Path
import json
from benchmark_runner import percentile
assert percentile([1,2,3,4],.5)==2.5
assert percentile([], .99)==''
assert percentile([9],.99)==9
for f in Path('queries').glob('*.js'):assert isinstance(json.loads(f.read_text()),list)
print('Percentiles y pipelines: correctos')
