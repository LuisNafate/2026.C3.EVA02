# Interrupción de telemetría en la corrida 95

PostgreSQL A/Q2_4MB/1 cliente/repetición 3: cAdvisor terminó con un error interno en destroyContainer. Prometheus conservó solo 222/224 puntos para CPU/RSS en la ventana. El runner rechazó esa cobertura y guardó métricas vacías, status=error; no se rellenan ni interpolan como si fueran observaciones.

Se reinicia cAdvisor con política restart: unless-stopped. Se conserva la fila y evidencia original. La corrida requiere repetición adicional identificada al revisar la matriz. El proceso continúa desde la siguiente clave una vez restablecida la recolección.
