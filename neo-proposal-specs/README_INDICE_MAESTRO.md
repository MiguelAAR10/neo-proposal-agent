# NEO Proposal Specs V2 - Indice Maestro

Este directorio es la unica base oficial para reconstruir y desarrollar la V2.

Objetivo operativo:
- Recuperar una base documental estable.
- Evitar duplicados y contradicciones.
- Habilitar desarrollo web end-to-end (frontend + backend) con foco MVP.

## Estructura oficial

```text
neo-proposal-specs/
├── README_INDICE_MAESTRO.md
├── requirements/
│   ├── 01_CONTEXTO_PRODUCTO.md
│   ├── 02_REQUISITOS_FUNCIONALES.md
│   ├── 03_ARQUITECTURA_TECNICA.md
│   └── 04_JOURNEY_MAP_COMPLETO.md
└── skills/
    ├── SKILL_BACKEND_EXPERT.md
    └── SKILL_FRONTEND_UX_EXPERT.md
```

## Orden de lectura recomendado

Ruta corta (kickoff de equipo, 90 min):
1. `requirements/01_CONTEXTO_PRODUCTO.md` (15 min)
2. `requirements/02_REQUISITOS_FUNCIONALES.md` (30 min)
3. `requirements/03_ARQUITECTURA_TECNICA.md` (30 min)
4. `requirements/04_JOURNEY_MAP_COMPLETO.md` (15 min)

Ruta de implementacion por rol:
1. Backend: `03_ARQUITECTURA_TECNICA.md` -> `SKILL_BACKEND_EXPERT.md`
2. Frontend: `04_JOURNEY_MAP_COMPLETO.md` -> `SKILL_FRONTEND_UX_EXPERT.md`
3. PM/QA: `01_CONTEXTO_PRODUCTO.md` -> `02_REQUISITOS_FUNCIONALES.md`

## Reglas de gobernanza documental

1. Esta carpeta es la fuente de verdad para V2.
2. Si un detalle no esta aqui, no se considera requisito oficial.
3. Cambios deben mantener trazabilidad (que cambia, por que cambia, impacto).
4. Evitar documentos duplicados con el mismo objetivo.

## Estado

- Version: `v2-specs-stable-base`
- Fecha de consolidacion: `2026-02-25`
- Estado: `Lista para retomar desarrollo`

## Contexto historico V1

Para preservar los aprendizajes fundacionales de V1, existe una carpeta de referencia:
- `mvp-v1-memoria-fundacional/`

Este contexto ayuda a los agentes a entender decisiones pasadas y evitar errores repetidos.
No reemplaza los requisitos oficiales de V2.

## Nota de preservacion

La documentacion V2 previa (desordenada o redundante) fue movida a:
- `docs/_legacy_v2_caos_2026-02-25/`

Se conserva como historial, pero no es base activa de implementacion.
