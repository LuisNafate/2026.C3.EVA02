# Bloqueo en corrida 142

El proceso permanecía activo sin completar calentamiento, con PostgreSQL cerca de su límite de 1 GiB. No se obtuvo una medición completa; no se atribuye el bloqueo exclusivamente a memoria sin diagnóstico adicional.

Se elimina el envío de SET después de conectar y se pasan exactamente los mismos valores statement_timeout/work_mem como opciones de conexión. El límite de conexión existente no acotaba esas operaciones posteriores. Cada fase ahora corre en un proceso aislado con vigilancia externa (duración nominal + 375 s para conexión y drenado), sin cambiar consultas, concurrencia, recursos ni timeout de consultas. Si el controlador queda bloqueado, se registra error y las métricas de rendimiento quedan vacías, no se inventa throughput cero. Se conservan todos los intentos previos y se repite la clave 142.

La modificación afecta al mecanismo de recuperación del cliente y debe declararse en el método. El CSV de 14 columnas no cambia. Los errores no entran en el resumen de rendimiento.
