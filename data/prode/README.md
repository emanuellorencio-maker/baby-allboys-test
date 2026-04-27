# Carga manual del Prode Mundial

Este proyecto es estático en Vercel. El panel `admin-prode.html` no escribe en el servidor: genera JSON para copiar o descargar.

## Pasos

1. Abrir `admin-prode.html` en el sitio local o publicado.
2. Presionar `Cargar JSON actuales`.
3. Agregar participante con padre/madre/tutor, hijo, categoría y zona/equipo.
4. Cargar los pronósticos del participante para los partidos del Mundial.
5. Cuando se jueguen partidos, cargar el resultado real.
6. Presionar `Recalcular puntajes`.
7. Copiar o descargar el JSON generado.
8. Reemplazar el archivo correspondiente dentro de `data/prode/`.
9. Revisar la web localmente.
10. Hacer commit y push.

## Archivos principales

- `data/prode/participantes.json`: participantes y pronósticos.
- `data/prode/partidos.json`: fixture del Mundial y resultados reales.
- `data/prode/ranking.json`: export opcional del ranking calculado.
- `data/prode/pronosticos.json`: export opcional separado de pronósticos.
- `data/prode/resultados_mundial.json`: export opcional separado de resultados reales.

Para la web pública actual, `prode-mundial.html` lee principalmente `participantes.json` y `partidos.json`.
