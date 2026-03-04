# README Logos

Instrucciones de carga para logos corporativos usados por el header del dashboard.

## Formato requerido
- **PNG** con **fondo transparente**.

## Nomenclatura estricta
- Todo en minúsculas.
- Sin espacios.
- Sin tildes ni caracteres especiales.
- Ejemplos válidos:
  - `bcp.png`
  - `pacifico.png`
  - `alicorp.png`

## Ubicación obligatoria
- Guardar los archivos **directamente** en:
  - `frontend-web/public/logos/`

## Comportamiento en UI
- El header intenta cargar automáticamente `/logos/{empresa}.png` según la empresa objetivo.
- Si el archivo no existe, se muestra fallback con icono `Building`.
