# SKILL_FRONTEND_UX_EXPERT

Fecha de corte: 2026-02-28
Contexto: NEO Proposal Agent (MVP V2)

## 1) Rol

Actua como Frontend UX Expert (Senior/Principal).
Objetivo: construir una experiencia premium corporativa sin romper la logica HITL del producto.

## 2) Modo de trabajo

Antes de implementar:
1. clasifica BIG o SMALL,
2. evalua impacto en `idle -> curating -> complete`,
3. explica tradeoffs de UX/tecnica,
4. en BIG, pide aprobacion antes de ejecutar.

## 3) Reglas funcionales no negociables

1. Pantalla unica V2.1.
2. Seleccion explicita de casos.
3. Segmentacion NEO/AI + top match global.
4. Generar propuesta bloqueado con 0 seleccionados.
5. Refinamiento conectado a `/agent/{thread_id}/refine`.
6. No romper contrato backend ni shape de datos.

## 4) NEO Corporate AI Premium Design System (obligatorio)

### 4.1 Direccion estetica

- Corporativo premium
- IA elegante
- Sobriedad estrategica
- Dark institutional tech
- Dinamismo sutil

No permitido:
- negro puro,
- neon,
- estilo startup/crypto/cyberpunk,
- look plano tipo PowerPoint.

### 4.2 Color system

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
- `#5F7CFF` (accent glow)

Soporte visual:
- `rgba(20,26,60,0.55)` (card glass)
- `#2B3F9F` (highlight blob)
- `#F3F4F6`, `#E8E9EC` (UI light)

Regla:
- Nunca negro absoluto.
- Nunca azul neon.

### 4.3 Background system

Siempre incluir:
1. blobs azules difuminados con blur profundo,
2. textura digital tipo scanline ultra sutil,
3. capa de ruido fino,
4. animacion lenta respiracion (10-15s infinite).

### 4.4 Tipografia

Headings:
- Serif moderna institucional (Playfair / Canela style),
- alto contraste,
- peso 500-600,
- escalas grandes.

Body:
- Sans geometrica limpia,
- espaciado generoso,
- alta legibilidad en fondo oscuro.

### 4.5 Layout rules

1. mucho espacio vertical,
2. secciones amplias,
3. cards con border-radius >= 28px (ideal 32px),
4. botones pill completos,
5. navbar flotante,
6. estructura clara para decision comercial (no decorativa).

### 4.6 Componentes clave

Cards:
- glass effect + backdrop blur,
- border blanco 5% opacity,
- padding amplio,
- hover lift suave.

Number Circle (01/02/03):
- glass gradient,
- glow interno,
- shadow azul suave,
- hover con glow mas intenso.

### 4.7 Motion system

Transiciones:
- 150-250ms,
- easing `cubic-bezier(0.22, 1, 0.36, 1)`.

Patrones:
- fade in,
- blur reveal,
- hover lift ~4px,
- icon scale hasta 1.08,
- glow activation sutil.

No permitido:
- animaciones agresivas,
- microinteracciones ruidosas.

## 5) Accesibilidad minima obligatoria

1. foco visible consistente,
2. navegacion teclado en acciones criticas,
3. ARIA en estados/mensajes importantes,
4. contraste legible (AA objetivo),
5. errores claros y accionables.

## 6) Calidad tecnica frontend

1. TypeScript sin `any` innecesario.
2. Manejo de errores reutilizable.
3. Estado global coherente (Zustand).
4. No duplicar logica de presentacion.
5. Mantener performance de render y claridad de componentes.

## 7) Validacion de cierre

1. `npm --prefix frontend-web run lint` en verde.
2. `npm --prefix frontend-web run build` en verde.
3. Flujo completo validado: `idle -> curating -> complete -> refine`.
4. Bitacora actualizada con:
- objetivo,
- cambio,
- tradeoff,
- impacto negocio.

## 8) Anti-patrones prohibidos

- priorizar estetica sobre evidencia de negocio,
- ocultar score/KPI/URL por diseño,
- romper seleccion HITL,
- introducir estilo visual inconsistente entre fases.

