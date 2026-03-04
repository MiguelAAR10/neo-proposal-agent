# 08 - UI/UX Guidelines

## Neo-Brutalismo Cibernetico

Este proyecto adopta un sistema visual estricto llamado **Neo-Brutalismo Cibernetico**.
No es opcional ni interpretable. Cualquier implementacion nueva debe respetar estas reglas.

## 1) Paleta Oficial (Exacta)

- Fondo global (`body`): `#0A0A0A`
- Superficies (cards, paneles, drawers): `#121212`
- Borde estructural unico: `border-zinc-800` (1px solido)
- Texto principal: `text-zinc-50`
- Texto secundario: `text-zinc-400`

No usar verdes, azules, naranjas, cian, fucsia, gradients multicolor, ni paletas alternativas.

## 2) Acento Unico (Regla del 1%)

- Acento permitido: `violet-400`
- Uso permitido:
  - Boton de accion principal (ej: Generar propuesta)
  - Estado seleccionado/activo
  - Icono o metrica verdaderamente critica
- Uso no permitido:
  - Fondos completos
  - Texto de cuerpo
  - Decoracion general o ruido visual

## 3) Estructura sin Sombras

Prohibicion absoluta:
- `shadow-*`
- `drop-shadow-*`
- `box-shadow` custom

La jerarquia visual se define solo con:
- borde de 1px (`border border-zinc-800`)
- contraste de fondo (`#0A0A0A` vs `#121212`)
- espacio/padding consistente

## 4) Tipografia

- Titulos, labels tecnicos, tags, KPIs: `font-mono`
- Texto de cuerpo: `font-sans`
- Interlineado minimo para bloques largos: `leading-relaxed` (o `leading-loose` cuando aplique)

## 5) Componentes Base

Tarjeta base obligatoria:
- `bg-[#121212] border border-zinc-800 rounded-md`

Tag/Pill obligatoria:
- `px-2 py-1 bg-zinc-900 border border-zinc-800 text-zinc-300 text-xs font-mono uppercase tracking-wider`

## 6) Iconografia

- Icono por defecto: `text-zinc-400`
- Icono destacado: `text-violet-400`
- No usar iconos circulares deformados ni contenedores inflados.

## 7) Anti-Slop Checklist (Antes de Merge)

- [ ] No hay `shadow-*` ni `box-shadow`.
- [ ] Todo panel/case usa borde `zinc-800` de 1px.
- [ ] Solo existe 1 acento (`violet-400`).
- [ ] Texto largo tiene `leading-relaxed` o superior.
- [ ] Tags cumplen clase oficial sin deformaciones.
- [ ] No hay colores extra fuera de negro/zinc/violet.

## 8) Regla de Consistencia

Si una pantalla nueva contradice este manifiesto, se considera deuda tecnica visual y debe corregirse antes de cerrar la tarea.
