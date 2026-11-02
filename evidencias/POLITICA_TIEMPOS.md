# Límites de espera

Aplicable desde la próxima reanudación; el proyecto sigue pausado.

- Consultas: se mantiene el límite existente de 300 segundos.
- Ejecutor completo por corrida: máximo 900 segundos (15 minutos), incluyendo calentamiento, medición, esperas y cierre del cliente.
- Al excederlo se termina todo el árbol de procesos del cliente, se guarda hard_timeout.json, se detiene el servicio del motor para cancelar trabajo residual y se conserva un enfriamiento de 60 segundos antes de continuar.
- Operaciones externas de preparación/análisis: límite de 120 segundos por comando. Si fallan, el proyecto se detiene con diagnóstico; no se encadena otra medición con infraestructura incierta.
- El límite de 15 minutos corresponde al ejecutor; la recuperación, preparación y enfriamiento adicional pueden añadir tiempo. No es un límite total de toda la matriz ni un mecanismo de tiempo real frente a hibernación.

Si no hubo medición válida, la fila se marca error y las métricas quedan vacías. Su timestamp representa el inicio del intento; hard_timeout.json explicita que no es el inicio de una ventana válida. El booleano disk_spill=false de estas filas no demuestra ausencia de spill: el evento es desconocido y solo se conserva ese valor para respetar el esquema fijo. No se usan estas filas en el análisis de rendimiento ni de ausencia de spill. Si ya se escribió una fila completa antes de atascarse en el cierre, se conserva sin duplicarla y se añade la incidencia.

No se cambian las ventanas nominales 60/300/60, los perfiles, las consultas ni los resultados anteriores. El nuevo control puede cancelar consultas que excedan el presupuesto global y debe declararse en el método.
