# 01 - VISION Y CONTEXTO DEL NEGOCIO

Fecha de corte: 2026-03-02
Estado: ALINEADO A IMPLEMENTACION V2.1 + pipeline backend formal aprobado

## Proposito del producto

NEO Proposal Agent acelera propuestas comerciales de consultoria:
- de 4-6 horas a 20-30 minutos,
- con evidencia verificable,
- y personalizacion por cliente/sector.

## Problema que resuelve

Para el consultor junior:
- baja velocidad inicial,
- dificultad para encontrar casos comparables,
- alto riesgo de propuesta generica.

Para NEO:
- conocimiento disperso,
- calidad inconsistente,
- menor conversion por baja personalizacion.

## Valor de negocio esperado

| Dimension | Objetivo | Impacto |
|---|---|---|
| Velocidad | 20-30 min por propuesta | 12x-18x mas rapido |
| Calidad | Evidencia + KPI + URL | mayor credibilidad |
| Conversion | Propuesta contextual | +15% a +25% |
| Escala | Junior con marco senior | mayor capacidad |

## Estado de capacidades contra objetivo

IMPLEMENTADO:
- Busqueda semantica de casos.
- Curacion explicita por consultor.
- Generacion y refinamiento de propuesta.
- Segmentacion NEO/AI con transparencia de relevancia.

PARCIAL:
- Uso sistematico de inteligencia sector en todos los flujos.
- Persistencia operativa de metricas SLA.
- Captura estructurada de conocimiento tacito comercial (reuniones, objeciones, presupuesto, decisores).

BACKLOG:
- Integracion CRM end-to-end.
- Analitica de conversion por tipo de caso.

## Principios de producto vigentes

1. HITL real: el consultor decide seleccion final.
2. Evidencia antes que narrativa: caso sin respaldo pierde prioridad.
3. Tecnologia transversal: importa el patron del problema.
4. Output slide-ready: breve, ejecutivo, usable.
5. Memoria institucional: cada ciclo debe dejar aprendizaje.

## Prioridades inmediatas de negocio

P0:
1. Mantener estabilidad E2E del flujo completo.
2. Evitar regresiones de evidencia (URL/KPI/score claro).
3. Activar `Sales Insight Collector` HITL desde Fase 1 del pipeline formal.

P1:
1. Mejorar visibilidad de calidad de datos por caso.
2. Fortalecer telemetria operativa persistente.
3. Consolidar perfil empresa con fusion de data web + insights de ventas.

P2:
1. Integrar salida a CRM y trazabilidad comercial.
