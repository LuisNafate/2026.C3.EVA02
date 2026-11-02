from pathlib import Path
from datetime import datetime,timezone
import shutil,json
p=Path('benchmark_runner.py');s=p.read_text(encoding='utf-8-sig')
s=s.replace(" if warm_errors:raise RuntimeError('Warmup fallido: '+str(warm_errors[:3]))", " (out/'warmup_errors.json').write_text(json.dumps(warm_errors,indent=2),encoding='utf8')\n # Keep load-related warmup failures as evidence; still attempt the measurement window.")
s=s.replace("epoch,lat,errors=phase(o.engine,o.query,o.variant,o.concurrency,300);end=epoch+300", "epoch,lat,errors=phase(o.engine,o.query,o.variant,o.concurrency,300);end=epoch+300\n errors=['Warmup: '+e for e in warm_errors]+errors")
p.write_text(s,encoding='utf8')
src=Path('evidencias/mongodb_PROFILE_C_SEVERE_Q1_nodisk_50_1')
if src.exists():
 dst=Path('evidencias/interrumpidas')/(src.name+'_warmup_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'));shutil.move(str(src),str(dst));(dst/'INCIDENTE.md').write_text('El proceso abortó en calentamiento por MaxTimeMSExpired, sin producir una fila de medición. Se conserva este intento. El runner se corrigió para registrar errores de calentamiento y continuar a la ventana de medición; el resultado quedará marcado error si hubo fallos de calentamiento. No se incrementaron los timeouts ni los recursos.',encoding='utf8')
