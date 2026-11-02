# Incidente de la corrida 48

MongoDB, perfil B, Q2_disk, 10 clientes, repetición 3: se registraron 366 consultas exitosas y errores de timeout/cancelación. Se conserva la fila status=error y toda su evidencia; se excluye de los resúmenes de rendimiento. No se ha determinado la causa raíz: los timeouts no prueban OOM ni spill. La ventana de Prometheus contiene 301 muestras. Los logs incluyen el drenado posterior a la ventana de medición.

Se ajustó el orquestador para conservar errores de consulta y continuar la matriz, como requiere la tolerancia a fallos del experimento. La falta de telemetría sigue siendo bloqueante. No se cambió el límite de consulta ni se sobrescribió o reemplazó esta observación. Esta celda necesita revisión y posible repetición adicional identificada por separado al finalizar.

## Aclaración del usuario
El usuario informó que el equipo hibernó durante la ejecución anterior y autorizó continuar con la corrida 49. La hibernación es una causa plausible de los timeouts de la corrida 48, pero no se atribuye exclusivamente a ella sin corroborar los tiempos del sistema. La corrida 48 se mantiene como error de ejecución y no como prueba de degradación propia del motor. La corrida 49 ya estaba activa tras la reanudación; no se lanzó un proceso duplicado.
