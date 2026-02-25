# 03 - JOURNEY MAPS: Usuario y Valor

## Journey del Usuario: "El Joven" (Consultor Junior)

### Fase 1: Entrada y Contexto (30 segundos)

**Trigger:** 
- Licitación llega por email
- Cliente potencial menciona necesidad
- Oportunidad urgente en CRM

**Acciones del usuario:**
1. Abre la aplicación web
2. Ve pantalla limpia con formulario
3. Ingresa datos iniciales

**Inputs Requeridos:**
```text
┌─────────────────────────────────────────┐
│  NEO PROPOSAL AGENT                     │
├─────────────────────────────────────────┤
│                                         │
│  ¿Qué tipo de casos buscas?             │
│  ○ Solo casos NEO                       │
│  ○ Solo benchmarks AI                   │
│  ● Ambos (recomendado)                  │
│                                         │
│  Empresa cliente                        │
│  [TechCorp                          ▼]  │
│  Sugerencias: TechCorp, TechSolutions   │
│                                         │
│  Industria/Rubro                        │
│  [Tecnología                        ▼]  │
│  (Auto-completa si empresa existe)      │
│                                         │
│  Área de la empresa                     │
│  [Marketing Digital              ▼]     │
│  (Auto-completa si empresa existe)      │
│                                         │
│  Describe el problema                   │
│  ┌─────────────────────────────────┐   │
│  │ Necesitamos reducir el tiempo   │   │
│  │ de elaboración de reportes...   │   │
│  └─────────────────────────────────┘   │
│  45/500 caracteres (mínimo 20)          │
│                                         │
│     [    🔍 BUSCAR CASOS    ]           │
│                                         │
└─────────────────────────────────────────┘
```

**Comportamientos:**
- Autocomplete empresa: debounce 300ms, top 5 coincidencias
- Si empresa existe: industria y área se autocompletan (deshabilitadas)
- Si empresa nueva: industria editable, área dropdown
- Validación: todos obligatorios, problema mínimo 20 caracteres
- Loading: spinner en botón + "Buscando casos relevantes..."

**Output de esta fase:**
- Estado guardado en sesión
- Botón "Buscar casos" activo
- Transición a Fase 2

---

### Fase 2: Descubrimiento de Casos (10-20 segundos)

**Sistema procesa:**
1. Embedding del problema (Gemini)
2. Búsqueda en Qdrant (colección según switch)
3. Retrieval de top 6-8 casos más similares
4. Ranking por score coseno

**Pantalla resultante - Layout dividido:**
```text
┌─────────────────────────────────────────────────────────────┐
│  🔙  Búsqueda: "reducir tiempo reportes" en TechCorp        │
│       Marketing | Tecnología | Switch: Ambos                │
│       6 casos encontrados                                   │
└─────────────────────────────────────────────────────────────┘

┌──────────────────────────────────┬──────────────────────────┐
│                                  │                          │
│  PANEL IZQUIERDO (60%)           │  PANEL DERECHO (40%)     │
│  Tarjetas de Casos               │  Chat de Contexto        │
│                                  │                          │
│  ┌────────────────────────────┐  │  ┌──────────────────────┐│
│  │ 🔗 Reducción 40% Reportes  │  │  │ 💬 Asistente NEO     ││
│  │    Banco ABC | Operaciones │  │  ├──────────────────────┤│
│  │                            │  │  │                      ││
│  │ 📋 Problema: Procesamiento │  │  │ 🤖 Encontré 6 casos  ││
│  │    manual de datos...      │  │  │    relevantes.       ││
│  │                            │  │  │    ¿Alguno te parece ││
│  │ 💡 Solución: Agentes IA    │  │  │    aplicable?        ││
│  │    para validación...      │  │  │                      ││
│  │                            │  │  │ ─────────────────────││
│  │ 🏷️ LLMs  🏷️ RPA  🏷️ Python│  │  │                      ││
│  │                            │  │  │ 👤 ¿Tienes algo de   ││
│  │ [ ] Seleccionar            │  │  │    fintech?          ││
│  │ [Ver slide original →]     │  │  │                      ││
│  └────────────────────────────┘  │  │ 🤖 Sí, el caso del   ││
│                                  │  │    Banco ABC es de   ││
│  ┌────────────────────────────┐  │  │    sector financiero ││
│  │ 🔗 Optimización ML...      │  │  │                      ││
│  │    Retail Corp | Ventas    │  │  │ ─────────────────────││
│  │ ...                        │  │  │                      ││
│  └────────────────────────────┘  │  │ [Escribe mensaje...] ││
│                                  │  │ [        ➤        ]  ││
│  [Cargar más casos]              │  │                      ││
│                                  │  │ ─────────────────────││
│                                  │  │ 📋 Resumen           ││
│                                  │  │ 2 casos seleccionados││
│                                  │  │                      ││
│                                  │  │ [GENERAR PROPUESTA →]││
│                                  │  │ (activa si ≥1)       ││
│                                  │  └──────────────────────┘│
└──────────────────────────────────┴──────────────────────────┘
```

**Tarjeta de Caso (Detalle):**
```text
┌─────────────────────────────────────────┐
│                                         │
│  📈 Reducción 40% en Reportes Mensuales │
│                                         │
│  Banco ABC  •  Operaciones              │
│  Score: 0.87 (muy relevante)            │
│                                         │
│  ─────────────────────────────────────  │
│                                         │
│  📋 PROBLEMA                            │
│  Procesamiento manual de datos          │
│  financieros en Excel, 5 días/mes       │
│  [Ver más...]                           │
│                                         │
│  💡 SOLUCIÓN                            │
│  Automatización con Python +            │
│  Power BI, reducción a 1 día            │
│                                         │
│  ─────────────────────────────────────  │
│                                         │
│  🏷️ Python  🏷️ Power BI  🏷️ RPA       │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │  ☑️  Seleccionar para propuesta  │   │
│  └─────────────────────────────────┘   │
│                                         │
│  [📎 Ver slide original →]              │
│  (abre en nueva pestaña)                │
│                                         │
└─────────────────────────────────────────┘
```

**Estados de tarjeta:**
- Default: borde gris claro, sombra suave
- Hover: sombra más pronunciada, leve elevación
- Seleccionada: borde azul primario, fondo azul muy claro, check marcado

**Interacción HITL:**
- Usuario marca checkbox en tarjetas deseadas (0 a N)
- Puede no marcar ninguno y pedir más búsqueda
- URLs de slides son clickeables, abren en nueva pestaña
- Chat permite refinar búsqueda: "¿Tienes algo de retail?"

**Output de esta fase:**
- Lista de IDs de casos seleccionados
- Contexto del chat (opcional, para refinement)
- Transición a Fase 3

---

### Fase 3: Enriquecimiento Automático (5 segundos, background)

**Sistema ejecuta en paralelo (sin pantalla dedicada):**
1. **Perfil de cliente:** Busca en `neo_profiles_v1` por empresa+área
   - Si existe: extrae objetivos, prioridades, dolor principal
   - Si no existe: marca para completar post-propuesta
2. **Inteligencia sector:** 
   - Revisa Redis cache por rubro+área
   - Si miss: consulta Gemini con web grounding
   - Guarda en cache para próximas

**Indicador visual:**
```
Preparando contexto... ⏳
```

---

### Fase 4: Generación de Propuesta (15-30 segundos)

**Trigger:** Usuario hace clic en "Generar propuesta de valor"

**Sistema:**
1. Construye prompt con:
   - Datos del cliente (empresa, rubro, área, problema)
   - Casos seleccionados (títulos, problemas, soluciones, KPIs)
   - Perfil de cliente (objetivos, prioridades)
   - Inteligencia sector (tendencias, benchmarks)
2. Llama a Gemini con temperatura 0.3 (determinista)
3. Parsea respuesta en estructura slide-ready

**Pantalla resultante:**
```text
┌─────────────────────────────────────────────────────────────┐
│  🔙 Volver a casos    v1    [💾] [📋] [📄] [✉️]            │
│                         ↑                                   │
│                    selector de versión                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  PROPUESTA DE VALOR ESTRATÉGICA                             │
│  Para: TechCorp - Marketing Digital                         │
│  Fecha: 20 de febrero, 2024                                 │
│                                                             │
│  ─────────────────────────────────────────────────────────  │
│                                                             │
│  CONTEXTO                                                   │
│  TechCorp opera en el sector tecnológico, donde el 73%      │
│  de las empresas líderes han implementado automatización    │
│  en marketing. El área de Marketing Digital enfrenta el     │
│  desafío de reducir el tiempo dedicado a reportes manuales, │
│  alineado con su objetivo estratégico declarado de          │
│  automatizar procesos en 30%.                               │
│                                                             │
│  PROPUESTA                                                  │
│  Implementar un ecosistema de agentes de IA generativa      │
│  para la automatización integral de reportes y análisis     │
│  predictivo de campañas. La solución combina: (1) Ingesta   │
│  automatizada de datos desde múltiples fuentes de marketing,│
│  (2) Generación dinámica de insights mediante LLMs          │
│  entrenados en el contexto específico de TechCorp, y        │
│  (3) Dashboards ejecutivos actualizados en tiempo real.     │
│                                                             │
│  IMPACTO ESPERADO                                           │
│  • Reducción 30-40% en tiempo de reportes (benchmark        │
│    sectorial: 20-30% típico, 40% con implementación        │
│    avanzada)                                                │
│  • Mejora 15-25% en precisión de forecasting de demanda     │
│  • ROI positivo en 8-10 meses                               │
│  • Escalabilidad: capacidad de procesar 3x volumen sin      │
│    incremento de equipo                                     │
│                                                             │
│  CASOS DE REFERENCIA                                        │
│  • Banco ABC: 40% reducción en reportes operativos          │
│    [Ver caso →]                                             │
│  • Retail Corp: Optimización de 15 procesos analíticos      │
│    [Ver caso →]                                             │
│                                                             │
│  ─────────────────────────────────────────────────────────  │
│                                                             │
│  ¿Te gustaría ajustar algo?                                 │
│  • Hacerlo más corto                                        │
│  • Enfatizar componente técnico                             │
│  • Añadir sección de inversión                              │
│  • Cambiar tono a más ejecutivo                             │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Toolbar de acciones:**
- 💾 Guardar (en sesión)
- 📋 Copiar texto al portapapeles
- 📄 Exportar PDF con branding NEO
- ✉️ Enviar por email (futuro)

**Output de esta fase:**
- Propuesta generada
- Transición a Fase 5 (opcional)

---

### Fase 5: Refinamiento Conversacional (Loop opcional, 5-10 minutos)

**Chat activo al lado de la propuesta:**

Usuario puede decir:
- "Hazlo más corto, 200 palabras máximo"
- "Enfatiza el componente de IA generativa"
- "Añade una sección de riesgos y mitigación"
- "Adapta el tono para C-level, más estratégico"
- "Quita la parte técnica, más enfocado en negocio"

**Sistema:**
1. Toma historial del chat + propuesta actual
2. Genera nueva versión
3. Mantiene versiones (v1, v2, v3...) para comparar

**Indicador de versión:**
```
v1 (original) → v2 (más corto) → v3 (C-level)
```

**Output final:** Propuesta aprobada por usuario

---

### Fase 6: Exportación y Seguimiento (2 minutos)

**Acciones disponibles:**
1. **Copiar texto plano** (Portapapeles → Pegar en Word/Slides)
2. **Exportar a PDF** (Con branding NEO, logo, colores, URLs clickeables)
3. **Enviar por email** (futuro, a cliente/equipo/CRM)
4. **Guardar en CRM** (futuro, Salesforce/HubSpot)

**Post-acción si empresa es nueva:**
```text
┌─────────────────────────────────────┐
│  ¿Completar perfil de TechCorp?     │
│                                     │
│  Esto ayudará a futuras propuestas  │
│  para esta empresa.                 │
│                                     │
│  [Completar perfil]  [Más tarde]    │
└─────────────────────────────────────┘
```

**Feedback opcional:**
```text
¿Te sirvió esta propuesta?
👍 Muy útil    👎 No tanto    💬 Comentario
```

---

## Journey de Aporte de Valor: Construcción de Memoria

### Ingesta de Casos (Administrador/Automático)
**Frecuencia:** Mensual o por evento (nuevo proyecto cerrado)
**Proceso:**
1. Scraper extrae diapositivas de presentaciones de venta
2. Chunking y enriquecimiento con Gemini (contexto para embedding)
3. Validación humana rápida (5 min por caso)
4. Ingesta a Qdrant con embeddings

**Valor generado:** Base de conocimiento crece, búsquedas más precisas.

### Actualización de Perfiles de Cliente
**Trigger:** Post-reunión de descubrimiento, cierre de proyecto, formulario trimestral.
**Procesamiento:** Embedding de texto completo, upsert a `neo_profiles_v1`, disponible para próximas propuestas.
**Valor generado:** Propuestas más personalizadas, mejor alineación con objetivos cliente.

### Actualización de Inteligencia Sectorial
**Automático:** Scraper mensual de fuentes de industria, Gemini con web grounding, Cache en Redis con TTL 30 días.
**Manual (admin):** Invalidación de cache específico, forzar regeneración por evento.
**Valor generado:** Propuestas contextualizadas en tendencias, posicionamiento como experto en vertical.

---

## Mapa de Valor por Interacción

| Interacción del Usuario | Valor para Joven | Valor para NEO | Dato Persistido |
|------------------------|------------------|----------------|-----------------|
| Ingresa empresa nueva | Estructura clara | Oportunidad identificada | Sesión |
| Describe problema | Búsqueda relevante | Contexto de necesidad | Analytics |
| Selecciona casos | Control total | Feedback de relevancia | Interacción |
| Genera propuesta | Propuesta profesional | Contenido reutilizable | Historial |
| Refina por chat | Propuesta personalizada | Preferencias de tono | Perfil usuario |
| Completa perfil cliente | Futuras propuestas mejores | Memoria de cliente | Qdrant |
| Exporta propuesta | Listo para presentar | Métrica de éxito | CRM |
| Feedback (thumbs) | Mejora del sistema | Datos de satisfacción | Analytics |

---

## Métricas de Éxito por Fase

| Fase | Métrica | Target | Cómo se mide |
|------|---------|--------|-------------|
| **Intake** | Tiempo de entrada | < 1 min | Logs |
| **Búsqueda** | Latencia | < 2 seg | Logs |
| **Curación** | Casos seleccionados | 2-4 promedio | Analytics |
| **Generación** | Latencia | < 15 seg | Logs |
| **Refinamiento** | Iteraciones | 1-2 promedio | Analytics |
| **Exportación** | Tasa de uso | > 80% | Analytics |
| **Total** | Tiempo end-to-end | 20-30 min | Logs |
| **Satisfacción** | NPS | > 8/10 | Feedback |

---

## Casos de Uso Específicos

### Caso 1: Licitación Urgente (30 minutos)
**Escenario:** Licitación llega por email, respuesta en 24h
1. Joven abre app (1 min)
2. Ingresa datos de licitación (2 min)
3. Busca casos similares (1 min)
4. Selecciona 3 casos (2 min)
5. Genera propuesta (1 min)
6. Refina tono para C-level (5 min)
7. Exporta PDF (1 min)
8. Envía a cliente (1 min)
**Total: 14 minutos** (vs 6 horas manual)

### Caso 2: Reunión de Descubrimiento (20 minutos)
**Escenario:** Joven sale de reunión con cliente, necesita propuesta para próxima semana
1. Ingresa datos del cliente (2 min)
2. Busca casos (1 min)
3. Selecciona casos (2 min)
4. Genera propuesta (1 min)
5. Completa perfil de cliente (5 min)
6. Refina propuesta (5 min)
7. Exporta (1 min)
**Total: 17 minutos** (vs 4 horas manual)

### Caso 3: Propuesta Compleja (45 minutos)
**Escenario:** Cliente grande, múltiples áreas, propuesta debe ser muy personalizada
1. Ingresa datos (3 min)
2. Busca casos (1 min)
3. Selecciona casos (3 min)
4. Genera propuesta (1 min)
5. Refina múltiples veces (20 min)
6. Completa perfil detallado (10 min)
7. Exporta y revisa (5 min)
**Total: 43 minutos** (vs 8 horas manual)

---

## Indicadores de Salud del Sistema

| Indicador | Umbral | Acción |
|-----------|--------|--------|
| Casos en Qdrant | < 100 | Ingestar más datos |
| Cache hit rate | < 60% | Revisar TTL |
| Latencia búsqueda | > 3 seg | Optimizar índices |
| Latencia generación | > 20 seg | Revisar prompt |
| Errores Gemini | > 2% | Revisar rate limiting |
| Satisfacción usuario | < 4/5 | Recopilar feedback |