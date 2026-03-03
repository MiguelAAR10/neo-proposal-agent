# 06 - GUIA DATOS Y LOGOS DE EMPRESA (MVP2)

Fecha: 2026-02-28

## Objetivo

Estandarizar como se cargan logos de las 12 empresas priorizadas y como esos datos se usan en backend/frontend para mantener consistencia visual y de negocio.

## Ubicacion de logos

Ruta unica:

- `frontend-web/public/logos/companies/`

Archivos esperados:

- `bcp.png`
- `interbank.png`
- `bbva.png`
- `alicorp.png`
- `rimac.png`
- `pacifico.png`
- `scotiabank.png`
- `mibanco.png`
- `credicorp.png`
- `plaza-vea.png`
- `falabella.png`
- `sodimac.png`

## Caracteristicas tecnicas recomendadas

- Formato principal: PNG transparente.
- Alternativa: SVG limpio (sin scripts, sin fuentes embebidas).
- Tamano sugerido: 256x256 o 512x512.
- Peso sugerido: <= 120 KB por logo.
- Color: sRGB.
- Margen interno recomendado: 8-12% para evitar recorte en avatares redondeados.

## Contrato backend

Servicio: `backend/src/services/prioritized_clients.py`

Cada cliente priorizado expone:

- `logo_file`: nombre de archivo canonico.
- `logo_path`: ruta publica para frontend (`/logos/companies/<file>`).
- `brand_color`: color principal de marca para acentos visuales.

Endpoints que lo consumen:

- `GET /api/prioritized-clients`
- `POST /agent/start` (contexto cliente priorizado)

## Contrato frontend

- Formulario inicial (`InitialForm`) muestra preview de logo para la empresa seleccionada.
- Cabecera principal (`page.tsx`) intenta renderizar logo de empresa; si no existe, cae a monograma.
- Las fichas/casos mantienen visuales degradados para continuidad aunque falte logo real.

## Regla de calidad de datos

Si un logo no existe aun:

- No bloquear el flujo.
- Mostrar fallback de iniciales.
- Registrar pendiente en bitacora para completar activos visuales.

## Integracion con backend de propuestas

- El logo no altera scoring semantico ni ranking.
- Solo afecta presentacion y reconocimiento rapido de empresa.
- La generacion de propuesta continua basada en casos, perfil y contexto sectorial.
