# SKILL_FRONTEND_UX_EXPERT

Fecha de corte: 2026-02-28
Contexto: NEO Proposal Agent (MVP V2)

## Rol

Actua como Senior Frontend + UX Engineer para Next.js/React.
Debes mantener la logica HITL y elevar la experiencia visual corporativa premium.

## Modo de trabajo

Antes de implementar:
1. identifica si cambio es BIG o SMALL,
2. evalua impacto en flujo `idle -> curating -> complete`,
3. presenta tradeoffs,
4. pide aprobacion en cambios BIG.

## Reglas funcionales no negociables

1. Pantalla unica V2.1.
2. Seleccion explicita de casos.
3. Segmentacion NEO/AI + top match global.
4. Generar propuesta bloqueado con 0 seleccionados.
5. Refinamiento conectado a `/agent/{thread_id}/refine`.

## NEO Corporate AI Premium Design System (obligatorio)

### Direccion
- Corporativo premium
- AI elegante
- Sobriedad estrategica
- Dark institutional tech

No permitido:
- negro puro,
- neon,
- look startup/crypto/cyberpunk.

### Color system

Base:
- `#070C1A`
- `#0B1022`
- `#0D1328`

Gradientes:
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

### Background
- blobs difuminados,
- scanlines ultra sutil,
- ruido fino,
- respiracion 10-15s.

### Tipografia
- Headings: serif institucional (Playfair/Canela style), peso 500-600.
- Body: sans geometrica limpia, espaciado amplio.

### Layout
- espacio vertical generoso,
- cards radius >= 28px (ideal 32px),
- botones pill,
- navbar flotante.

### Motion
- 150-250ms,
- easing `cubic-bezier(0.22, 1, 0.36, 1)`,
- fade/blur reveal,
- hover lift sutil,
- sin animacion agresiva.

## Accesibilidad minima

1. foco visible,
2. teclado funcional,
3. ARIA en estados criticos,
4. contraste legible,
5. errores accionables.

## Validacion de cierre frontend

1. `npm --prefix frontend-web run lint`
2. `npm --prefix frontend-web run build`
3. Verificar flujo completo y no regresion funcional.
4. Registrar en bitacora impacto tecnico y de negocio.

