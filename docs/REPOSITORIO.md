# Publicar el repositorio

El repositorio está publicado en https://github.com/LuisNafate/2026.C3.EVA02 con visibilidad pública. La rama principal y las etiquetas están subidas. El siguiente procedimiento sirve como referencia para otro destino:

1. Revisar README, informe, CSV y limitaciones antes de publicar.
2. Crear un repositorio GitHub con la visibilidad elegida.
3. En esta carpeta, configurar el remoto con la URL real: `git remote add origin URL_DEL_REPOSITORIO`.
4. Subir rama y etiquetas: `git push -u origin main` y `git push origin --tags`.

Las etiquetas documentan la instantánea de datos y la entrega del reporte. No significan que todos los experimentos terminaran exitosamente.

La carpeta `.venv`, el compilador `.tools`, el JSONL masivo, temporales y los archivos de trabajo de LaTeX no se versionan. El generador y el manifiesto permiten reproducir los datos. La evidencia completa se incluye comprimida en `entrega/evidencias_completas.zip`; los planes de validación y las notas de incidentes también quedan legibles en el repositorio. Verificar el tamaño por archivo antes de subir nuevos resultados; no agregar el dataset completo con un `git add` indiscriminado.

La publicación pública de matrícula y datos personales queda a criterio del alumno. El PDF los incluye porque así se solicitó para la entrega académica.
