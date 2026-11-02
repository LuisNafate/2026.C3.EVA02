from pathlib import Path
p=Path('scripts/run_suite.py');s=p.read_text(encoding='utf-8-sig')
s=s.replace("  if latest['status']=='error':raise RuntimeError('Corrida con error: revisar evidencias antes de continuar')", "  if latest['status']=='error':\n   # Query timeouts are experimental outcomes; retain the row and continue.\n   # Missing telemetry prevents valid resource comparisons and still stops the suite.\n   if not latest['cpu_throttled_seconds'] or not latest['max_rss_mb']:\n    raise RuntimeError('Telemetria incompleta: revisar antes de continuar')")
p.write_text(s,encoding='utf8')
Path('evidencias/INCIDENTE_048.md').write_text('''# Incidente de la corrida 48

MongoDB, perfil B, Q2_disk, 10 clientes, repetición 3: se registraron 366 consultas exitosas y errores de timeout/cancelación. Se conserva la fila status=error y toda su evidencia; se excluye de los resúmenes de rendimiento. No se ha determinado la causa raíz: los timeouts no prueban OOM ni spill. La ventana de Prometheus contiene 301 muestras. Los logs incluyen el drenado posterior a la ventana de medición.

Se ajustó el orquestador para conservar errores de consulta y continuar la matriz, como requiere la tolerancia a fallos del experimento. La falta de telemetría sigue siendo bloqueante. No se cambió el límite de consulta ni se sobrescribió o reemplazó esta observación. Esta celda necesita revisión y posible repetición adicional identificada por separado al finalizar.
''',encoding='utf8')
