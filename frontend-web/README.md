# Frontend Web (NEO Proposal Agent V2)

UI principal del MVP V2 construida con Next.js.

## Requisitos

- Node.js 20+
- npm 10+
- Backend V2 corriendo en `http://127.0.0.1:8000`

## Configuración

Este frontend usa `NEXT_PUBLIC_API_URL` y por defecto apunta a `http://localhost:8000`.

Si quieres fijarlo explícitamente, crea `frontend-web/.env.local`:

```env
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
```

## Ejecutar en desarrollo

Desde la raíz del repo:

```bash
npm --prefix frontend-web install
npm --prefix frontend-web run dev -- -H 127.0.0.1 -p 3000
```

O desde `frontend-web/`:

```bash
npm install
npm run dev -- -H 127.0.0.1 -p 3000
```

Abrir `http://127.0.0.1:3000`.

## Scripts útiles

```bash
npm run dev
npm run build
npm run start
npm run lint
```

## Pantallas/flujo V2

- Formulario inicial (empresa/rubro/área/problema/switch).
- Curación de casos sugeridos con selección HITL.
- Generación de propuesta final.
- Chat contextual y refinamiento.
- Panel operativo en `/ops`.

## Troubleshooting rápido

- Si el frontend abre pero no carga datos, valida `NEXT_PUBLIC_API_URL`.
- Si el backend responde `degraded` en `/health`, revisa Qdrant/Redis.
- Si puerto `3000` está ocupado, usa otro: `npm run dev -- -p 3001`.
