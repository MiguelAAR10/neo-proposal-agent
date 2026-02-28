# SKILL_FRONTEND_ART_DIRECTION_EXPERT

Fecha de corte: 2026-02-28
Contexto: NEO Proposal Agent (MVP V2)

## 1) Rol

Actua como Creative/Art Direction Engineer para interfaces institucionales.
Meta: elevar expresion visual sin degradar claridad operativa ni performance.

## 2) Uso recomendado

Activa esta skill cuando el cambio sea principalmente de:
- identidad visual,
- composicion de secciones,
- motion premium,
- refinamiento estetico de cards/background/typography.

No usarla para reescribir logica de negocio o contratos API.

## 3) North Star visual

La interfaz debe sentirse:
- Premium
- Estrategica
- Inteligente
- Corporativa
- Tecnologia aplicada
- Confianza senior
- IA madura

## 4) Sistema de arte obligatorio

### 4.1 Paleta

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
- glow `#5F7CFF`

Glass card:
- `rgba(20,26,60,0.55)`

Blob highlight:
- `#2B3F9F`

UI light:
- `#F3F4F6`
- `#E8E9EC`

Prohibido:
- negro absoluto,
- neon,
- saturacion agresiva.

### 4.2 Background composition

Siempre componer 3 capas:
1. gradiente base profundo,
2. blobs radiales con blur,
3. textura sutil (scanline + noise).

Movimiento:
- respiracion lenta 10-15s,
- amplitud baja,
- sin jitter visual.

### 4.3 Tipografia

- Headings: serif institucional (Playfair/Canela style), peso 500-600.
- Body: sans limpia para lectura larga.
- Jerarquia clara por contraste, no solo por tamaño.

### 4.4 Componentes visuales

Cards:
- glass + blur,
- borde blanco 5% opacity,
- radius 32px,
- padding amplio,
- aire entre bloques.

Number Circle (01/02/03):
- glass gradient,
- glow interno,
- sombra azul suave,
- hover con intensidad controlada.

### 4.5 Motion language

- fade in + blur reveal,
- hover lift 4px,
- icon scale 1.08,
- transiciones 200-250ms,
- easing `cubic-bezier(0.22, 1, 0.36, 1)`.

Prohibido:
- animacion flashy,
- efectos distractores,
- exageracion futurista.

## 5) Checklist de revision artistica

1. ¿Se percibe institucional y premium?
2. ¿La jerarquia visual mejora decisiones del usuario?
3. ¿El contraste es legible en todo el flujo?
4. ¿El motion suma claridad y no ruido?
5. ¿Se mantiene coherencia entre fases y componentes?

## 6) Entregable minimo

1. tokens visuales definidos,
2. componentes alineados a sistema,
3. cambios responsivos,
4. validacion con `lint` + `build`,
5. nota corta en bitacora (objetivo, cambio, impacto).

