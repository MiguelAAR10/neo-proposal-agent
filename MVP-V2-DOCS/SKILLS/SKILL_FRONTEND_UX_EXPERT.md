# SKILL_FRONTEND_UX_EXPERT - NEO PROPOSAL AGENT

Fecha de corte: 2026-02-28
Estado: ACTIVA

## 1) Cuando activar

Activar para cualquier cambio en:
- `frontend-web/src/*`
- UI/UX de fases `idle`, `curating`, `complete`
- estilos globales, motion, accesibilidad
- integracion visual con contratos backend

## 2) Objetivo del rol

Construir una experiencia frontend que sea:
1. clara para operacion HITL,
2. premium corporativa,
3. consistente con evidencia de negocio,
4. robusta (sin romper contrato API).

## 3) Reglas funcionales obligatorias

1. Mantener pantalla unica V2.1.
2. Mantener seleccion explicita de casos.
3. Mantener segmentacion NEO/AI + top match global.
4. Mantener bloqueo de generar con 0 seleccionados.
5. Mantener refinamiento conectado a `/agent/{thread_id}/refine`.

## 4) Design system obligatorio (NEO Corporate AI Premium)

Direccion:
- corporativo premium,
- AI elegante,
- sobriedad estrategica,
- dark institutional tech.

Tokens principales:
- base: `#070C1A`, `#0B1022`, `#0D1328`
- gradientes: `#1B2C6B`, `#243C8F`, `#1A2F78`, `#2A3F9D`
- acento: `#6C8CFF` / `#5F7CFF`
- surface: `rgba(20,26,60,0.55)`

Background:
- blobs difuminados,
- scanlines sutiles,
- ruido fino,
- respiracion lenta 10-15s.

Layout:
- espacios amplios,
- cards radius >= 28px,
- botones pill,
- navbar flotante.

Motion:
- 150-250ms,
- easing `cubic-bezier(0.22, 1, 0.36, 1)`,
- hover lift sutil,
- sin animacion agresiva.

## 5) Accesibilidad minima obligatoria

1. foco visible en elementos interactivos,
2. navegacion por teclado,
3. ARIA en estados/mensajes criticos,
4. contraste legible en dark mode institucional,
5. errores accionables para usuario.

## 6) Checklist de cierre frontend

1. Flujo completo E2E sin regresion (`idle -> curating -> complete`).
2. `npm --prefix frontend-web run lint` en verde.
3. `npm --prefix frontend-web run build` en verde.
4. Bitacora actualizada con objetivo, cambio, tradeoff e impacto negocio.

## 7) Anti-patrones prohibidos

- UI plana tipo slide genérica.
- romper logica de negocio por estetica.
- esconder score/KPI/URL por decoracion.
- dejar componentes mock sin indicarlo.

