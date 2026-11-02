# Presentación en clase: 8–10 minutos

1. **Objetivo (1 min):** medir QPS, percentiles y recursos en agregaciones JSON al limitar CPU y RAM.
2. **Comparabilidad (1 min):** mostrar `evidencias/validacion/comparabilidad.json`: 500000 documentos, hash canónico completo, doce grupos Q1 y mil valores Q2 equivalentes.
3. **Método (1 min):** explicar 108 corridas base más54 por segunda varianteQ2; perfiles A/B/C y clientes1/10/50; ventanas60/300/60. Declarar adaptaciones y censura de consultas.
4. **Resultados (2 min):** usar las tablas y figuras del PDF. En la matriz hubo127 ok,18 spill,15 error,2 oom. Spill terminó; no es un error. No ocultar celdas sin tres repeticiones válidas.
5. **Planes (1 min):** Q1 MongoCOLLSCAN desanida1.5 millonesdeítems y agrupa12 resultados; PostgreSQLQ1 muestra externalmerge. PostgreSQLQ2 utilizó top-Nheapsort, por eso 4 MBno garantizó spill.
6. **Fallos (2 min):** abrir anexoA y una carpeta de evidencia. Separar OOM del contenedor, timeout de consulta, hibernación, memoria compartida y pérdida de cAdvisor. Explicar que se conservaron todos los resultados y no se repitió hasta obtener éxito.
7. **Cierre (1 min):** aumentar concurrencia puede elevar P99 y presión de memoria; dimensionar límites y operaciones. CPUyRAM cambiaron juntas: no se aísla causalidad. El costo exacto M3 no está establecido; reconocerlo con claridad.

## Respuestas para el profesor

- **¿Son los mismos datos?** Conteos y hash por todos los documentos, excluyendo `_id` de Mongo.
- **¿Dónde están percentiles?** CSV14 columnas y muestras; interpolación lineal, sin atribuir latencia cero a errores.
- **¿Por qué CFSsupera300 s?** Puede acumular espera entre hilos; no es tiempo de pared.
- **¿Hubo spill/OOM?** Sí; planes/logs/inspect, diferenciados del resto de problemas.
- **¿Tres repeticiones?** Matriz162 con tres por celda; las tablas reportan cuántas fueron válidas. Los errores se analizan como estabilidad.
- **¿Por qué no ganó siempre un motor?** Las consultas y planes son distintos; la conclusión se limita a la carga y al entorno medidos.

Para entregar: PDF y CSV completo. Para defender: README, fuenteLaTeX y paquete de evidencia. El documento final incluye las limitaciones; no presentarlo como un estudio perfectamente controlado.
