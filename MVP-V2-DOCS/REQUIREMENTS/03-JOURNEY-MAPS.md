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

```
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
│  [BCP                               ▼]  │
│  Sugerencias: BCP, BBVA, Alicorp        │
│                                         │
│  Industria/Rubro                        │
│  [Banca                             ▼]  │
│  (Auto-completa si empresa existe)      │
│                                         │
│  Área de la empresa                     │
│  [Operaciones                    ▼]     │
│  (Auto-completa si empresa existe)      │
│                                         │
│  Describe el problema                   │
│  ┌─────────────────────────────────┐   │
│  │ Necesitamos reducir el tiempo   │   │
│  │ de conciliación bancaria...     │   │
│  └─────────────────────────────────┘   │
│  45/500 caracteres (mínimo 20)          │
│                                         │
│     [    🔍 BUSCAR CASOS    ]           │
│                                         │
└─────────────────────────────────────────┘
```

**Comportamientos:**
- Autocomplete empresa: debounce 300ms, top coincidencias (Top Corporativos Perú).
- Si empresa existe: industria y área se autocompletan. **Crucial:** Silenciosamente se carga el `neo_profile` (insights de reuniones pasadas).
- Si empresa nueva: industria editable, área dropdown.
- Validación: todos obligatorios, problema mínimo 20 caracteres.

**Output de esta fase:**
- Estado guardado en sesión.
- Transición a Fase 2.

---

### Fase 2: Descubrimiento y Selección (HITL) (10-20 segundos)

**Sistema procesa:**
1. Embedding del problema (Gemini).
2. Búsqueda en Qdrant (`neo_cases_v1`) aplicando el filtro del Switch.
3. Retrieval de top casos más similares (Ranking por score coseno).

**Pantalla resultante - Layout dividido:**

```
┌─────────────────────────────────────────────────────────────┐
│  🔙  Búsqueda: "tiempo de conciliación" en BCP              │
│       Operaciones | Banca | Switch: Ambos                   │
│       6 casos encontrados                                   │
└─────────────────────────────────────────────────────────────┘

┌──────────────────────────────────┬──────────────────────────┐
│                                  │                          │
│  PANEL IZQUIERDO (60%)           │  PANEL DERECHO (40%)     │
│  Tarjetas de Casos               │  Chat de Contexto        │
│                                  │                          │
│  ┌────────────────────────────┐  │  ┌──────────────────────┐│
│  │ 🔗 Conciliación Automática │  │  │ 💬 Asistente NEO     ││
│  │    BBVA | Operaciones      │  │  ├──────────────────────┤│
│  │                            │  │  │                      ││
│  │ 📋 Problema: Cuadre manual │  │  │ 🤖 Encontré 6 casos  ││
│  │    de miles de tx...       │  │  │    relevantes.       ││
│  │                            │  │  │    ¿Cuál se parece a ││
│  │ 💡 Solución: RPA + Python  │  │  │    lo que busca BCP? ││
│  │                            │  │  │                      ││
│  │ 🏷️ RPA  🏷️ Python          │  │  │ ─────────────────────││
│  │                            │  │  │                      ││
│  │ [x] Seleccionar            │  │  │ 👤 El caso del BBVA  ││
│  │ [Ver slide original →]     │  │  │    está perfecto.    ││
│  └────────────────────────────┘  │  │                      ││
│                                  │  │ ─────────────────────││
│  [Cargar más casos]              │  │                      ││
│                                  │  │ [GENERAR PROPUESTA →]││
│                                  │  │ (activa si ≥1)       ││
│                                  │  └──────────────────────┘│
└──────────────────────────────────┴──────────────────────────┘
```

**La Regla de Oro del Perfil (El Criterio de Decisión):**
Aquí es donde brilla el sistema. El usuario ve los casos (ej. BBVA) y **él decide** cuál usar como base tecnológica/resolutiva. El perfil del BCP cargado en la fase anterior **NO restringe los casos que se muestran**, sirve como contexto para la *siguiente* fase (generación).

**Output de esta fase:**
- Lista de IDs de casos seleccionados (El "Qué" vamos a hacer).
- Transición a Fase 3.

---

### Fase 3: Enriquecimiento y Generación Orientada (15-30 segundos)

**Trigger:** Usuario hace clic en "Generar propuesta"

**Sistema:**
Construye un mega-prompt para Gemini combinando:
1.  **El Caso Seleccionado (La Base):** "Vamos a proponer RPA + Python como se hizo en BBVA".
2.  **El Perfil del Cliente (El Enfoque):** Busca en `neo_profiles_v1` (ej. Dummy data del BCP) y encuentra: *"El BCP es adverso al riesgo y prefiere implementaciones modulares"*.
3.  **El Problema Actual:** "Reducir tiempo de conciliación".

**La Magia del LLM:** 
Gemini toma la solución del BBVA, pero **redacta** la propuesta resaltando los puntos de interés del BCP. La propuesta no dirá "Implementación total inmediata", dirá "Implementación modular de RPA para mitigar riesgos, logrando...".

**Pantalla resultante:**

```
┌─────────────────────────────────────────────────────────────┐
│  🔙 Volver a casos    v1    [💾] [📋] [📄]                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  PROPUESTA DE VALOR: Automatización de Conciliación         │
│  Para: BCP - Operaciones                                    │
│                                                             │
│  CONTEXTO                                                   │
│  Entendemos la necesidad crítica del BCP de optimizar los   │
│  tiempos de conciliación manteniendo el máximo control y    │
│  minimizando riesgos operativos.                            │
│                                                             │
│  ENFOQUE PROPUESTO (Basado en éxito comprobado)             │
│  Proponemos una implementación **modular** de agentes RPA   │
│  y Python. Iniciaremos con un piloto controlado en las      │
│  transacciones de mayor volumen, garantizando 0 impacto en  │
│  sistemas legacy, alineado a su cultura de gestión de riesgo│
│                                                             │
│  IMPACTO ESPERADO                                           │
│  • Reducción de 40% en tiempos de cuadre.                   │
│  • Trazabilidad total de cada transacción.                  │
│                                                             │
│  CASOS DE REFERENCIA                                        │
│  • BBVA: Conciliación Automática (RPA + Python)             │
│    [Ver caso →]                                             │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Output de esta fase:**
- Propuesta generada y fuertemente orientada al perfil corporativo.

---

### Fase 4: Refinamiento Conversacional (Loop opcional)

El consultor puede usar el chat para afinar detalles (ej. "Ponlo más en formato bullet points").

---

### Fase 5: Retroalimentación y Memoria (El Ciclo Virtuoso)

Al exportar la propuesta, si el consultor tiene nuevos insights (ej. "En la reunión de hoy, el BCP mencionó que ahora usan AWS"), puede actualizar el perfil del cliente.

**Formulario de Insights (Post-Propuesta):**
```
┌─────────────────────────────────────┐
│  Actualizar Perfil: BCP             │
├─────────────────────────────────────┤
│                                     │
│  ¿Algún insight nuevo de la reunión?│
│  [ Ahora están migrando a AWS y  ]  │
│  [ buscan soluciones cloud-native]  │
│                                     │
│        [💾 GUARDAR INSIGHT]         │
└─────────────────────────────────────┘
```
*Este nuevo texto se vectoriza y se suma al `neo_profiles_v1`, haciendo que la próxima propuesta sea aún mejor.*

---

## Estrategia de Dummy Data (Top Corporativos Perú)

Para la V2, no crearemos un CRUD complejo. Ingestaremos directamente a Qdrant un JSON con perfiles simulados de alto valor para validar el modelo:

- **BCP:** Enfoque en riesgo, seguridad, implementaciones modulares.
- **Alicorp:** Enfoque en cadena de suministro, volumen masivo, eficiencia de costos.
- **Interbank:** Enfoque en agilidad, innovación, time-to-market.
- **Supermercados Peruanos:** Enfoque en rotación de inventario, márgenes ajustados.

*Este es el verdadero núcleo del valor: la tecnología sirve al consultor, el perfil orienta el discurso, y el caso seleccionado da la credibilidad.*
