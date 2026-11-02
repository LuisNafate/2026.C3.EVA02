from pathlib import Path
p=Path('scripts/run_suite.py');s=p.read_text(encoding='utf-8-sig');s=s.replace("run(sys.executable,'scripts/analyze.py')", "run(sys.executable,'scripts/analyze.py')\n  with open('resultados/mediciones.csv') as f:latest=list(csv.DictReader(f))[-1]\n  if latest['status']=='error':raise RuntimeError('Corrida con error: revisar evidencias antes de continuar')")
p.write_text(s,encoding='utf8')
p=Path('scripts/check_local.py');s=p.read_text(encoding='utf-8-sig');s="import sys\nfrom pathlib import Path\nsys.path.insert(0,str(Path(__file__).resolve().parents[1]))\n"+s;p.write_text(s,encoding='utf8')
