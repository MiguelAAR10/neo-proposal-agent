# Logos Empresariales

Este directorio está reservado para logos de empresas objetivo usados por el dashboard.

Ruta base:
- `frontend-web/public/logos/`

Convención de nombres:
- Formato: `nombreempresa.png`
- Todo en minúsculas
- Sin espacios
- Sin tildes ni caracteres especiales

Ejemplos:
- `bcp.png`
- `pacifico.png`
- `interbank.png`
- `scotiabank.png`

Comportamiento en UI:
- El header intentará cargar dinámicamente `/logos/{empresa}.png` según la empresa seleccionada.
- Si el archivo no existe, se mostrará automáticamente un ícono de fallback (`Building`) para mantener consistencia visual.
