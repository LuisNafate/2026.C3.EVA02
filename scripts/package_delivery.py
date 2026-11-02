"""Build shareable artifacts without environments, dataset or executable caches."""
from pathlib import Path
import zipfile,shutil,json,hashlib
ROOT=Path(__file__).resolve().parents[1]
out=ROOT/'entrega';out.mkdir(exist_ok=True)
shutil.copy2(ROOT/'informe/latex/reporte_eva02.pdf',out/'Reporte_EVA02.pdf')
shutil.copy2(ROOT/'resultados/todas_las_pruebas.csv',out/'Todas_las_pruebas.csv')
with zipfile.ZipFile(out/'evidencias_completas.zip','w',zipfile.ZIP_DEFLATED) as z:
 for p in sorted((ROOT/'evidencias').rglob('*')):
  if p.is_file():z.write(p,p.relative_to(ROOT))
entries=[]
for p in sorted(out.iterdir()):
 if p.is_file() and p.name not in ['Proyecto_EVA02.zip','MANIFIESTO_SHA256.json']:
  entries.append(dict(file=p.name,bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
(out/'MANIFIESTO_SHA256.json').write_text(json.dumps(entries,indent=2),encoding='utf8')
with zipfile.ZipFile(out/'Proyecto_EVA02.zip','w',zipfile.ZIP_DEFLATED) as z:
 for p in sorted(ROOT.rglob('*')):
  if not p.is_file():continue
  rel=p.relative_to(ROOT)
  if any(x in ['.venv','.tools','.git','tmp','__pycache__'] for x in rel.parts):continue
  if rel.as_posix() in ['resultados/orders.jsonl','entrega/Proyecto_EVA02.zip']:continue
  if rel.parts[0]=='evidencias' and len(rel.parts)>1 and rel.parts[1]!='validacion' and p.suffix!='.md':continue
  if p.suffix in ['.pyc','.log','.aux','.toc','.out']:continue
  z.write(p,rel)
print('Paquete creado: PDF, CSV, fuente, scripts, documentación y evidencia completa comprimida')
