# 04 - REQUISITOS FUNCIONALES

## RF-01: Gestión de Sesión y Switch de Colección

**Descripción:** El sistema debe permitir al usuario elegir qué tipo de casos consultar antes de iniciar la búsqueda.

**Criterios de aceptación:**

* \[ \] Dropdown visible en pantalla inicial con opciones: "Solo casos NEO", "Solo benchmarks AI", "Ambos"

* \[ \] Opción "Ambos" es default (recomendada)

* \[ \] Selección determina filtro en query a Qdrant (`tipo="NEO"`, `tipo="AI"`, o sin filtro)

* \[ \] Switch no puede cambiarse durante sesión activa (solo en nueva búsqueda)

* \[ \] Si Qdrant está vacío (0 puntos en colección), mostrar mensaje: "No hay casos disponibles. Contactar administrador."

* \[ \] Endpoint `/health` retorna estado de Qdrant (casos disponibles, perfiles, estado general)

**Prioridad:** 🔴 ALTA

**Notas técnicas:**

* Guardar switch en estado de sesión (LangGraph)

* Validar que colección existe antes de buscar

* Implementar retry automático si Qdrant no responde

---

## RF-02: Formulario de Entrada Inteligente

**Descripción:** Captura de datos del cliente y problema con autocompletado cuando existe.

**Criterios de aceptación:**

* \[ \] Campo "Empresa" con autocomplete basado en perfiles existentes en Qdrant

* \[ \] Si empresa existe: autocompletar industria y área desde perfil (deshabilitados)

* \[ \] Si empresa nueva: campo industria editable, área dropdown

* \[ \] Dropdown "Área" con opciones: Marketing, Operaciones, TI, Ventas, RRHH, Legal, Finanzas, Supply Chain, Otro

* \[ \] Campo "Problema" textarea libre, mínimo 20 caracteres, máximo 2000

* \[ \] Validación: todos los campos obligatorios antes de submit

* \[ \] Debounce en autocomplete: 300ms

* \[ \] Mostrar máximo 5 sugerencias en autocomplete

**Prioridad:** 🔴 ALTA

**Notas técnicas:**

* Usar Pydantic para validación en backend

* Implementar búsqueda en Qdrant para autocomplete

* Caché de empresas frecuentes en Redis

---

## RF-03: Búsqueda de Casos por Similitud Semántica

**Descripción:** Encontrar casos relevantes usando embeddings del problema descrito.

**Criterios de aceptación:**

* \[ \] Generar embedding del problema con Gemini text-embedding-004

* \[ \] Buscar en Qdrant colección `neo_cases_v1` con filtro según switch

* \[ \] Retornar top 6-8 casos ordenados por score de similitud coseno

* \[ \] Cada caso incluye: id, título, empresa, área, problema, solución, tecnologías, url_slide, score

* \[ \] Tiempo de respuesta < 2 segundos

* \[ \] Si no hay resultados, mostrar: "No encontramos casos similares. Intenta con otra descripción."

* \[ \] Permitir "Cargar más casos" (siguiente 6-8)

**Prioridad:** 🔴 ALTA

**Notas técnicas:**

* Usar Gemini text-embedding-004 (768 dimensiones)

* Implementar retry con exponential backoff para Gemini

* Cachear embeddings en Redis por 1 hora

* Implementar paginación en Qdrant

---

## RF-04: Visualización de Casos en Tarjetas

**Descripción:** Mostrar casos encontrados en formato tarjeta con información clave.

**Criterios de aceptación:**

* \[ \] Layout responsive: tarjetas en grid (3 columnas desktop, 1 móvil)

* \[ \] Cada tarjeta muestra: KPI/título destacado, empresa, área, problema (truncado 150 chars), solución (truncada 150 chars), tecnologías como tags

* \[ \] URL del slide es clickeable, abre en nueva pestaña

* \[ \] Checkbox "Seleccionar" en cada tarjeta, permite múltiple selección

* \[ \] Estado visual: seleccionado = borde azul, check marcado, fondo azul claro

* \[ \] Permitir 0 selecciones (usuario puede buscar de nuevo)

* \[ \] Hover: sombra más pronunciada, leve elevación

* \[ \] Score de relevancia visible (ej: "0.87 - Muy relevante")

**Prioridad:** 🔴 ALTA

**Notas técnicas:**

* Usar Framer Motion para animaciones

* Implementar virtualization si hay muchas tarjetas

* Lazy load de imágenes/logos

---

## RF-05: Chat de Contexto y Refinamiento

**Descripción:** Interfaz conversacional para preguntar sobre casos y refinar búsqueda.

**Criterios de aceptación:**

* \[ \] Panel de chat visible junto a tarjetas (o abajo en móvil)

* \[ \] Mensaje inicial del sistema con resumen de casos encontrados

* \[ \] Usuario puede escribir preguntas libres: "¿Tienes algo de retail?", "Muéstrame casos con ROI alto"

* \[ \] Sistema responde con texto natural y referencias a casos específicos

* \[ \] Historial de chat persistente durante la sesión

* \[ \] Máximo 10 mensajes en chat (para no perder contexto)

* \[ \] Botón "Limpiar chat" para resetear

**Prioridad:** 🟡 MEDIA

**Notas técnicas:**

* Usar LangGraph para orquestación del chat

* Implementar streaming de respuestas (SSE o WebSocket)

* Guardar historial en Redis por sesión

---

## RF-06: Generación de Propuesta de Valor

**Descripción:** Crear propuesta estructurada basada en casos seleccionados y contexto.

**Criterios de aceptación:**

* \[ \] Botón "Generar propuesta" activo solo si ≥1 caso seleccionado

* \[ \] Sistema recupera automáticamente: perfil cliente (si existe) e inteligencia sector

* \[ \] Prompt a Gemini incluye: datos cliente, casos seleccionados, perfil, sector

* \[ \] Respuesta estructurada en secciones: Contexto, Propuesta, Impacto Esperado, Casos de Referencia

* \[ \] Longitud: 300-500 palabras

* \[ \] Tiempo de generación < 10 segundos

* \[ \] Mostrar indicador de progreso: "Generando propuesta..."

* \[ \] Si falla Gemini, mostrar error amigable con opción de reintentar

**Prioridad:** 🔴 ALTA

**Notas técnicas:**

* Usar Gemini 1.5 Flash (temperatura 0.3 para determinismo)

* Implementar timeout de 20 segundos

* Guardar propuesta en sesión para refinamiento

---

## RF-07: Refinamiento Conversacional de Propuesta

**Descripción:** Permitir al usuario pedir modificaciones a la propuesta generada.

**Criterios de aceptación:**

* \[ \] Chat continúa activo post-generación

* \[ \] Usuario puede pedir: "Más corto", "Más formal", "Enfatiza X", "Añade sección Y"

* \[ \] Sistema genera nueva versión manteniendo contexto de conversación

* \[ \] Mostrar indicador de versión (v1, v2, etc.)

* \[ \] Opción "Volver a versión anterior" (últimas 3 versiones)

* \[ \] Máximo 5 refinamientos por propuesta (para evitar loops infinitos)

* \[ \] Cada refinamiento toma < 10 segundos

**Prioridad:** 🟡 MEDIA

**Notas técnicas:**

* Mantener historial de versiones en estado

* Usar diff visual para mostrar cambios

* Implementar versionado con timestamps

---

## RF-08: Exportación de Propuesta

**Descripción:** Permitir usar la propuesta generada fuera del sistema.

**Criterios de aceptación:**

* \[ \] Botón "Copiar texto" al portapapeles

* \[ \] Botón "Exportar PDF" con branding NEO (logo, colores)

* \[ \] PDF incluye: fecha, versión, casos referenciados con URLs

* \[ \] Formato PDF: profesional, listo para presentar (máximo 2 páginas)

* \[ \] Botón "Enviar por email" (futuro, MVP puede no incluir)

* \[ \] Toast de confirmación: "✓ Copiado" o "✓ PDF descargado"

**Prioridad:** 🟡 MEDIA

**Notas técnicas:**

* Usar librería como `html2pdf` o `weasyprint` para PDF

* Incluir branding NEO (logo, colores corporativos)

* Generar nombre de archivo: `propuesta_[empresa]_[fecha].pdf`

---

## RF-09: Gestión de Perfiles de Cliente

**Descripción:** Crear y actualizar memoria de objetivos por empresa/área.

**Criterios de aceptación:**

* \[ \] Si no existe perfil al generar propuesta, mostrar prompt: "¿Completar perfil de TechCorp?"

* \[ \] Formulario de perfil: objetivos (lista), prioridades (lista), dolor principal (texto)

* \[ \] Guardar en Qdrant `neo_profiles_v1` con embedding

* \[ \] Disponible inmediatamente para futuras búsquedas

* \[ \] Mostrar "última actualización" en perfil existente

* \[ \] Permitir editar perfil existente

* \[ \] Validación: mínimo 1 objetivo, máximo 5

**Prioridad:** 🟡 MEDIA

**Notas técnicas:**

* Generar embedding del perfil completo

* Implementar upsert en Qdrant

* Guardar timestamp de creación y actualización

---

## RF-10: Inteligencia de Sector con Cache

**Descripción:** Enriquecer propuestas con contexto de industria actualizado.

**Criterios de aceptación:**

* \[ \] Para rubro+área, consultar Redis primero

* \[ \] Si cache miss: consultar Gemini con web grounding

* \[ \] Guardar en Redis con TTL 30 días

* \[ \] Contenido: tendencias clave, benchmarks digitales, oportunidades IA

* \[ \] Mostrar fuente: "Datos de febrero 2024" o "Cacheado"

* \[ \] Si Gemini falla, usar cache viejo (graceful degradation)

* \[ \] Endpoint admin para invalidar cache: `/admin/cache/invalidate?pattern=sector:*`

**Prioridad:** 🟡 MEDIA

**Notas técnicas:**

* Usar Gemini con web grounding habilitado

* Implementar warm cache para rubros prioritarios

* Estructura JSON en Redis con TTL

---

## RF-11: Detección de Qdrant Vacío

**Descripción:** Manejar gracefulmente cuando no hay datos en vector DB.

**Criterios de aceptación:**

* \[ \] Al iniciar, verificar conteo de puntos en colecciones

* \[ \] Si 0 puntos: mostrar pantalla de "Configuración inicial requerida"

* \[ \] Mensaje claro: "Base de conocimiento vacía. Contactar [admin@neo.com](mailto:admin@neo.com)"

* \[ \] Deshabilitar funcionalidad de búsqueda hasta que haya datos

* \[ \] Endpoint de health check: `/health` retorna estado de Qdrant

* \[ \] Retry automático cada 30 segundos

**Prioridad:** 🔴 ALTA

**Notas técnicas:**

* Implementar health check en lifespan de FastAPI

* Usar circuit breaker para Qdrant

* Mostrar UI de error amigable

---

## RF-12: Persistencia de Sesión

**Descripción:** Mantener estado de usuario durante la sesión.

**Criterios de aceptación:**

* \[ \] Guardar estado en Redis con TTL 24 horas

* \[ \] Recuperar sesión si usuario recarga página

* \[ \] Mostrar "Sesión recuperada" si hay datos previos

* \[ \] Permitir "Iniciar nueva búsqueda" para resetear

* \[ \] Guardar historial de propuestas generadas (últimas 5)

**Prioridad:** 🟡 MEDIA

**Notas técnicas:**

* Usar session_id en cookies

* Serializar estado de LangGraph a JSON

* Implementar garbage collection de sesiones expiradas

---

## RF-13: Validación de Datos

**Descripción:** Asegurar integridad de datos en todos los inputs.

**Criterios de aceptación:**

* \[ \] Validar empresa: máximo 100 caracteres, sin caracteres especiales

* \[ \] Validar área: debe estar en lista predefinida

* \[ \] Validar problema: mínimo 20, máximo 2000 caracteres

* \[ \] Validar URLs: deben ser URLs válidas

* \[ \] Sanitizar inputs para prevenir XSS

* \[ \] Mostrar mensajes de error específicos

**Prioridad:** 🔴 ALTA

**Notas técnicas:**

* Usar Pydantic para validación

* Implementar sanitización en frontend y backend

* Usar regex para validación de URLs

---

## RF-14: Rate Limiting

**Descripción:** Proteger API de abuso.

**Criterios de aceptación:**

* \[ \] Máximo 100 requests por minuto por IP

* \[ \] Máximo 10 búsquedas por minuto por usuario

* \[ \] Máximo 5 generaciones de propuesta por minuto por usuario

* \[ \] Mostrar mensaje: "Demasiadas solicitudes. Intenta en X segundos."

* \[ \] Endpoint admin para resetear límites

**Prioridad:** 🟡 MEDIA

**Notas técnicas:**

* Usar middleware de FastAPI para rate limiting

* Implementar con Redis

* Usar header `X-RateLimit-Remaining`

---

## RF-15: Logging y Auditoría

**Descripción:** Registrar acciones para debugging y análisis.

**Criterios de aceptación:**

* \[ \] Loguear todas las búsquedas (empresa, área, problema)

* \[ \] Loguear todas las propuestas generadas

* \[ \] Loguear errores con stack trace

* \[ \] Loguear latencias de operaciones clave

* \[ \] Formato JSON para fácil parsing

* \[ \] Retención: 30 días

**Prioridad:** 🟡 MEDIA

**Notas técnicas:**

* Usar structlog para logging estructurado

* Implementar correlation_id por request

* Enviar logs a CloudWatch o similar

---

## RF-16: Feedback del Usuario

**Descripción:** Recopilar feedback para mejorar el sistema.

**Criterios de aceptación:**

* \[ \] Post-propuesta, mostrar: "¿Te sirvió esta propuesta?"

* \[ \] Opciones: 👍 Muy útil, 👎 No tanto, 💬 Comentario

* \[ \] Guardar feedback en base de datos

* \[ \] Mostrar NPS (Net Promoter Score) en dashboard admin

* \[ \] Permitir comentario libre (máximo 500 caracteres)

**Prioridad:** 🟢 BAJA

**Notas técnicas:**

* Guardar feedback en tabla separada

* Asociar con propuesta y usuario

* Implementar dashboard de analytics

---

## Matriz de Dependencias

```
RF-01 (Switch)
    ↓
RF-03 (Búsqueda) ← RF-02 (Formulario)
    ↓
RF-04 (Tarjetas) ← RF-05 (Chat)
    ↓
RF-06 (Generación) ← RF-09 (Perfil) ← RF-10 (Sector)
    ↓
RF-07 (Refinamiento)
    ↓
RF-08 (Exportación)

Transversales:
- RF-11 (Qdrant vacío)
- RF-12 (Sesión)
- RF-13 (Validación)
- RF-14 (Rate limiting)
- RF-15 (Logging)
- RF-16 (Feedback)
```

---

## Priorización para MVP

### Sprint 1 (Semana 1-2)

* ✅ RF-01: Switch de colección

* ✅ RF-02: Formulario de entrada

* ✅ RF-03: Búsqueda de casos

* ✅ RF-04: Visualización en tarjetas

* ✅ RF-11: Detección Qdrant vacío

* ✅ RF-13: Validación de datos

### Sprint 2 (Semana 3-4)

* ✅ RF-06: Generación de propuesta

* ✅ RF-08: Exportación PDF

* ✅ RF-09: Gestión de perfiles

* ✅ RF-12: Persistencia de sesión

* ✅ RF-15: Logging

### Sprint 3 (Post-MVP)

* ✅ RF-05: Chat de contexto

* ✅ RF-07: Refinamiento conversacional

* ✅ RF-10: Inteligencia de sector

* ✅ RF-14: Rate limiting

* ✅ RF-16: Feedback del usuario