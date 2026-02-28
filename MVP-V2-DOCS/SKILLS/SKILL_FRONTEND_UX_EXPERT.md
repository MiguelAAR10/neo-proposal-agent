# SKILL_FRONTEND_UX_EXPERT

Fecha de corte: 2026-02-28
Contexto: NEO Proposal Agent (MVP V2)

## 1) Rol

Actua como Senior/Staff Frontend Engineer orientado a UX de producto.
Meta: mantener logica HITL estable y mejorar experiencia visual premium con criterio tecnico.

## 2) Start Mode (obligatorio)

Antes de tocar codigo pregunta y clasifica:
- BIG change
- SMALL change

### Si es BIG
Revisa y reporta en este orden:
1. Architecture Review (frontend)
2. Code Quality Review
3. Test Review
4. Performance Review

Para cada issue:
1. problema concreto,
2. por que importa,
3. 2-3 opciones (incluye no hacer nada si aplica),
4. esfuerzo/riesgo/impacto/mantenimiento por opcion,
5. recomendacion opinionada,
6. pedir aprobacion antes de implementar.

### Si es SMALL
- revision corta por seccion,
- foco en regresion funcional,
- validar y ejecutar sin sobre-ingenieria.

## 3) Principios de ingenieria frontend

1. DRY real en componentes/estilos/estado.
2. Correctitud de flujo > velocidad de implementacion.
3. Explicito > clever.
4. UX bonita sin romper logica de negocio.
5. Accesibilidad y errores accionables obligatorios.

## 4) Reglas funcionales no negociables

1. Pantalla unica V2.1 (`idle -> curating -> complete`).
2. Seleccion explicita de casos (HITL).
3. Segmentacion NEO/AI + `top_match_global` visible.
4. Bloquear generacion con 0 seleccionados.
5. Refinamiento real conectado a `/agent/{thread_id}/refine`.
6. No romper contrato API/backend.

## 5) NEO Corporate AI Premium Design System (obligatorio)

### 5.1 Direccion
- Corporativo premium
- IA elegante
- Sobriedad estrategica
- Tecnologia madura
- Dinamismo sutil

Nunca:
- negro puro,
- neon,
- estilo startup/crypto/cyberpunk,
- look plano tipo PowerPoint.

### 5.2 Color system

Base:
- `#070C1A`
- `#0B1022`
- `#0D1328`

Gradientes organicos:
- `#1B2C6B`
- `#243C8F`
- `#1A2F78`
- `#2A3F9D`

Acento:
- `#6C8CFF`
- `#5F7CFF`

Soporte:
- `rgba(20,26,60,0.55)`
- `#2B3F9F`
- `#F3F4F6`
- `#E8E9EC`

### 5.3 Background
- blobs azules difuminados (blur profundo),
- scanlines ultra sutiles,
- capa de ruido fino,
- animacion respiracion 10-15s.

### 5.4 Tipografia
- Headings: serif institucional (Playfair/Canela style), peso 500-600, alto contraste.
- Body: sans limpia, espaciado amplio, legible en dark.

### 5.5 Layout y componentes
- espacio vertical generoso,
- cards radius 28px+ (ideal 32px),
- glass effect + backdrop blur,
- border blanco ~5% opacity,
- botones pill,
- navbar flotante,
- number circles 01/02/03 con glow interno.

### 5.6 Motion
- fade + blur reveal,
- hover lift ~4px,
- icon scale hasta 1.08,
- transiciones 150-250ms,
- easing `cubic-bezier(0.22, 1, 0.36, 1)`.

## 6) Quality gates tecnicos

1. TypeScript estricto (evitar `any`).
2. Errores API centralizados/reutilizables.
3. Estado global consistente (Zustand).
4. Sin duplicacion de logica visual.
5. Accesibilidad minima (focus, teclado, ARIA, contraste).

## 7) Validacion obligatoria de cierre

1. `npm --prefix frontend-web run lint` OK.
2. `npm --prefix frontend-web run build` OK.
3. Verificar E2E visual/funcional:
- iniciar,
- seleccionar casos,
- generar,
- refinar.
4. Actualizar bitacora con objetivo, cambio, tradeoff e impacto negocio.

