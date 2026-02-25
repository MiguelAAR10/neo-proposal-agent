# SKILL - Frontend UX Expert

## Mision

Construir la experiencia web V2 con foco en claridad, velocidad y control humano (HITL),
consumiendo el backend por API sin acoplar logica de negocio en UI.

## Stack obligatorio

- Next.js 14+
- React 18+
- TypeScript strict
- Tailwind CSS
- Zustand
- TanStack Query
- React Hook Form + Zod
- Testing Library + Playwright

## Responsabilidades

1. Implementar flujo completo del journey MVP.
2. Garantizar estados de carga/error recuperables.
3. Mantener UX de seleccion de casos simple y trazable.
4. Integrar API backend con tipado estricto.

## Arquitectura de UI recomendada

```text
frontend/
  app/
    page.tsx
    search/page.tsx
    proposal/page.tsx
  components/
    forms/
    cards/
    proposal/
    common/
  stores/
    agentStore.ts
  hooks/
    useAgentApi.ts
```

## Reglas de implementacion

1. Estado global:
- Guardar `thread_id`, contexto, casos, seleccion y propuesta.
- No duplicar estado entre store y componentes.

2. Data fetching:
- Todas las llamadas via hooks tipados.
- Control centralizado de errores API.

3. Formularios:
- Validacion con Zod antes de enviar.
- Mensajes de error por campo.

4. Seleccion HITL:
- Tarjetas con seleccion multiple clara.
- Contador de seleccionados visible.

5. Propuesta:
- Mostrar trazabilidad (casos usados).
- Permitir refinamiento y exportacion basica.

## Flujo UX minimo a entregar

1. Pantalla de entrada.
2. Pantalla de resultados (tarjetas + seleccion).
3. Pantalla de propuesta generada.
4. Estado de error y recuperacion en cada pantalla.

## Checklist de calidad

1. Responsive mobile/desktop.
2. Accesibilidad minima (teclado, labels, contraste).
3. Indicadores de loading en acciones lentas.
4. Mensajes de error accionables.
5. Sin bloqueos por estados intermedios.

## Checklist de testing

1. Unit tests de formularios y componentes criticos.
2. Integration tests de flujo start -> search -> select -> proposal.
3. E2E smoke test en entorno web de staging.

## Definition of Done (Frontend)

1. Usuario completa flujo MVP sin asistencia tecnica.
2. Errores recuperables sin recargar toda la app.
3. API integrada con contratos estables.
4. UI lista para demo y pruebas de negocio.
