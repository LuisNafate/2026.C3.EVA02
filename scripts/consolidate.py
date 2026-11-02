"""Consolidate without discarding original observations or selecting by success."""
import csv,json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
KEY=['engine','profile','query_id','concurrency','run_number']
def read(path):
 if not path.exists():return [],None
 with path.open(newline='',encoding='utf-8-sig') as f:
  reader=csv.DictReader(f);return list(reader),reader.fieldnames

def main():
 base,header=read(ROOT/'resultados/mediciones.csv');repeat,rheader=read(ROOT/'resultados/repeticiones.csv')
 assert len(header)==14
 if repeat:assert rheader==header
 selected={tuple(r[k] for k in KEY):r for r in base};assert len(selected)==len(base)
 manifest=[]
 plan=json.loads((ROOT/'resultados/repeticiones_plan.json').read_text()) if (ROOT/'resultados/repeticiones_plan.json').exists() else []
 repeat_keys={tuple(r[k] for k in KEY) for r in plan}
 for r in repeat:
  key=tuple(r[k] for k in KEY);assert key in repeat_keys
  # Supplements are retained separately; the final report uses the original matrix.
  pass
 for r in base:
  key=tuple(r[k] for k in KEY)
  manifest.append(dict(key=dict(zip(KEY,key)),source='mediciones.csv',selected_status=selected[key]['status']))
 for filename,rows in [('todas_las_pruebas.csv',base+repeat),('mediciones_seleccionadas.csv',list(selected.values()))]:
  p=ROOT/'resultados'/filename
  with p.open('w',newline='',encoding='utf8') as f:
   writer=csv.DictWriter(f,fieldnames=header);writer.writeheader();writer.writerows(rows)
 selection=dict(original_count=len(base),rerun_count=len(repeat),planned_reruns=len(plan),reruns_complete=len(repeat)==len(plan),selection_rule='Original matrix is primary; all completed reruns are separate supplements; all failures retained',rows=manifest)
 (ROOT/'resultados/seleccion_manifiesto.json').write_text(json.dumps(selection,ensure_ascii=False,indent=2),encoding='utf8')
 print(json.dumps({k:v for k,v in selection.items() if k!='rows'}))
if __name__=='__main__':main()
