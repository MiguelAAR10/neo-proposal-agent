# 03 - JOURNEY MAPS: USUARIO Y VALOR

Fecha de corte: 2026-02-28
Estado: ALINEADO A FLUJO IMPLEMENTADO

## Objetivo del journey

Guiar al consultor junior desde oportunidad comercial hasta propuesta ejecutiva lista, con control humano sobre evidencia.

## Journey operativo (estado real)

### Fase 1 - Intake (IMPLEMENTADO)
Acciones:
1. Empresa, rubro, area, problema, switch.
2. Inicio de sesion y contexto.

### Fase 2 - Busqueda (IMPLEMENTADO)
Sistema:
1. Embedding + Qdrant.
2. Resultado segmentado NEO/AI.
3. Top match global cuando aplica.

### Fase 3 - Curacion HITL (IMPLEMENTADO)
Usuario:
1. Selecciona 1..N casos.
2. Revisa evidencia desde tarjetas.
Regla:
- Sin seleccion no se genera propuesta.

### Fase 4 - Generacion (IMPLEMENTADO)
Sistema:
1. Usa casos seleccionados + contexto de sesion.
2. Entrega propuesta v1.

### Fase 5 - Refinamiento (IMPLEMENTADO)
Usuario:
1. Ajusta tono, foco, ROI, extension.
Sistema:
1. `POST /agent/{thread_id}/refine`.
2. Actualiza propuesta actual.

### Fase 6 - Exportacion (PARCIAL)
IMPLEMENTADO:
- Exportacion via impresion/PDF.
BACKLOG:
- Trazabilidad y push directo a CRM.

## Valor por fase

| Fase | Valor consultor | Valor NEO |
|---|---|---|
| Intake | estructura rapida | entrada estandar |
| Busqueda | evidencia en segundos | reutilizacion de conocimiento |
| Curacion | control de calidad | reduce alucinacion narrativa |
| Generacion | velocidad comercial | consistencia de propuestas |
| Refinamiento | ajuste fino | mejor narrativa ejecutiva |
| Exportacion | salida lista | trazabilidad comercial |

## Prioridades de journey

P0:
1. Mantener seleccion/generacion/refinamiento sin regresion.
2. Mantener claridad de score/evidencia en cards.

P1:
1. Mejorar ruta de exportacion formal.
2. Unificar feedback post-propuesta para memoria institucional.

P2:
1. Integracion CRM completa.

## Nota de limpieza documental

No crear un "journey alterno" fuera de este archivo.
Actualizar este mismo documento cuando cambie el flujo.

