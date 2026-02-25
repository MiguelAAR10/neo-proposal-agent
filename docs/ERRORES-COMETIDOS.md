# ERRORES COMETIDOS — Lecciones Aprendidas V2

**Fecha:** 25 de Febrero, 2026
**Contexto:** Desarrollo del NEO Proposal Agent V2
**Autor:** Antigravity AI (autocrítica en primera persona)

---

## RESUMEN EJECUTIVO

Cometí errores graves durante el desarrollo del NEO Proposal Agent V2. Escribí más de 60 archivos de código sin poder ejecutar, probar ni verificar absolutamente nada. El resultado fue un caos de archivos no funcionales que tuvieron que ser borrados por completo. Este documento detalla cada error, su causa raíz, y cómo debería haberse hecho correctamente.

---

## ERROR 0 — PROBLEMA RAÍZ INCOMPATIBILIDAD WSL Y ANTIGRAVITY

### Descripción del problema

El proyecto está ubicado en WSL (Ubuntu 24.04) accedido vía `\\wsl.localhost\Ubuntu-24.04\...`. Sin embargo, yo (Antigravity) tengo una limitación crítica:

```text
WSL extension is supported only in Microsoft versions of VS Code
```

**Antigravity NO puede ejecutar comandos en WSL.** Cada vez que intenté correr un comando (`npm install`, `npx create-next-app`, `rm -rf`, etc.), el sistema intentó usar `wsl.exe -c <comando>` internamente y falló con:

```text
Invalid command line argument: -c
Please use 'wsl.exe --help' to get a list of supported arguments.
```

### Por qué es el error más grave

Porque al no poder ejecutar comandos, **no pude**:

- Instalar dependencias (`npm install`, `pip install`)
- Inicializar proyectos correctamente (`npx create-next-app`)
- Ejecutar tests (`pytest`, `npm test`)
- Verificar que el código compila (`npm run build`, `python -c "import app"`)
- Validar que los servicios arrancan (`npm run dev`, `uvicorn`)
- Correr linters (`eslint`, `mypy`)

En resumen: escribí 60+ archivos completamente a ciegas.

### Acción correcta que debí tomar

1. **DETENERME INMEDIATAMENTE** cuando el primer comando falló
2. Informar al usuario: "No puedo ejecutar comandos en tu entorno WSL. Necesitamos resolver esto primero antes de escribir cualquier código."
3. Diagnosticar el problema y proponer soluciones ANTES de escribir una sola línea de código
4. Nunca proceder a "crear archivos manualmente" como alternativa a un proyecto scaffoldeado correctamente

### Solución para el futuro

El usuario necesita trabajar con una de estas opciones:

- **Opción A:** Abrir VS Code desde dentro de WSL (`code .` desde terminal Ubuntu) para que la extensión funcione dentro del entorno Linux
- **Opción B:** Mover el proyecto a una ruta nativa de Windows (`C:\Users\arias\Projects\...`)
- **Opción C:** Usar un editor/extensión que soporte WSL Remote nativamente (VS Code con extensión "Remote - WSL" de Microsoft)

**REGLA: Nunca escribir código si no puedo verificar que funciona.**

---

## ERROR 1 — ESTRUCTURA DE PROYECTO MONOREPO CAÓTICO

### Descripción del error

Puse `backend/` y `frontend/` dentro del mismo repositorio git como subdirectorios:

```text
neo-proposal-agent/          ← un solo repo
├── backend/                 ← FastAPI aquí dentro
├── frontend/                ← Next.js aquí dentro
├── docs/
├── data/
├── api.py                   ← archivo V1 suelto
├── app.py                   ← archivo V1 suelto
├── load_data.py             ← archivo V1 suelto
├── docker-compose.yml
└── ...20+ archivos sueltos
```

Esto es un caos por múltiples razones:

- Archivos de V1 (`api.py`, `app.py`, `load_data.py`, `src/`, etc.) mezclados con V2
- Un solo `git log` con commits de backend Y frontend mezclados
- Imposible deployar frontend y backend por separado
- Imposible tener CI/CD independiente para cada parte
- `npm install` y `pip install` en el mismo repo genera confusión
- No se puede dar acceso a un equipo de frontend sin dar acceso al backend

### Estructura profesional correcta

La estructura correcta usa **repositorios separados**:

```text
neo-proposal-agent-backend/    ← Repo Git 1
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── models/
│   ├── services/
│   ├── routers/
│   └── graph/
├── tests/
├── scripts/
├── Dockerfile
├── requirements.txt
├── pyproject.toml
├── .env.example
├── .gitignore
└── README.md

neo-proposal-agent-frontend/   ← Repo Git 2
├── src/
│   ├── app/
│   ├── components/
│   ├── hooks/
│   ├── stores/
│   ├── lib/
│   └── types/
├── public/
├── Dockerfile
├── package.json
├── tsconfig.json
├── tailwind.config.ts
├── .env.example
├── .gitignore
└── README.md

neo-proposal-agent-infra/      ← Repo Git 3 (opcional)
├── docker-compose.yml
├── k8s/
└── terraform/
```

**Alternativa aceptable (monorepo profesional):** Si se usa monorepo, debe ser con herramientas como `turborepo`, `nx`, o al menos con un `.gitignore` limpio y un `docker-compose.yml` que orqueste correctamente. Pero NUNCA archivos sueltos en la raíz.

### Regla aprendida

**Cada servicio deployable independiente = un repositorio separado (o un workspace bien configurado en un monorepo profesional).**

---

## ERROR 2 — 60 ARCHIVOS SIN VERIFICAR NI UNO

### Qué ocurrió en el error 2

Creé archivo tras archivo en una cascada de `write_to_file` sin parar a verificar:

- Backend: 40 archivos (routers, services, models, graph nodes, tests)
- Frontend: 24 archivos (pages, components, stores, hooks, config)
- Ninguno fue ejecutado, compilado, ni probado

Esto violó el principio fundamental del desarrollo de software: **Red → Green → Refactor** (TDD) o como mínimo **Write → Run → Fix → Repeat**.

### Consecuencias de no verificar

1. **Sin `npm install`**, no sé si las dependencias existen o son compatibles
2. **Sin `npm run build`**, no sé si TypeScript compila
3. **Sin `npm run dev`**, no sé si la app arranca
4. **Sin `pytest`**, no sé si los tests pasan
5. **Sin `uvicorn`**, no sé si FastAPI levanta
6. Los archivos pudieron tener errores de importación, tipeo, lógica — imposible saberlo
7. Los line endings pudieron estar mal (CRLF vs LF)

### Flujo correcto de desarrollo

```text
Paso 1. Verificar entorno    → Puedo ejecutar comandos? Node/Python instalados?
Paso 2. Scaffoldear          → npx create-next-app / mkdir + pip init
Paso 3. Verificar scaffold   → npm run dev → funciona?
Paso 4. Crear UN componente  → escribir el archivo
Paso 5. Verificar            → npm run dev → compila? se ve en browser?
Paso 6. Crear siguiente      → escribir el archivo
Paso 7. Verificar            → funciona?
Paso 8. Repetir 6-7          → iteración incremental
Paso 9. Tests                → escribir y ejecutar tests
Paso 10. Commit              → solo código verificado
```

**NUNCA** escribir más de 2-3 archivos sin verificar que funcionan.

---

## ERROR 3 — IGNORÉ LA DOCUMENTACIÓN DEL USUARIO

### Qué ocurrió en el error 3

El usuario tenía documentación detallada en `docs/v2_planning/` con:

- Requisitos funcionales (`04-REQUISITOS-FUNCIONALES.md`)
- Requisitos técnicos (`05-REQUISITOS-TECNICOS.md`)
- Skills de frontend (`SKILLS-FRONTEND-UX-EXPERT.md`)
- Skills de backend (`SKILLS-BACKEND-EXPERT.md`)

Leí estos documentos, pero **no los seguí al pie de la letra**. Por ejemplo:

- El documento especificaba **Shadcn/ui** como librería de componentes — yo no lo incluí
- El documento tenía una estructura de carpetas específica — yo usé una diferente
- El documento tenía patrones de código específicos — yo los adapté libremente

### Cómo seguir la documentación correctamente

1. Leer TODA la documentación antes de escribir una línea
2. Crear un checklist de requisitos específicos extraído de los documentos
3. Seguir EXACTAMENTE las especificaciones del usuario, no "mejorarlas"
4. Si hay algo que creo que debería ser diferente, PREGUNTAR antes de cambiar

---

## ERROR 4 — ARCHIVOS MARKDOWN EN DIRECTORIOS DE DATOS

### Qué ocurrió en el error 4

Creé archivos `.md` (Markdown) en ubicaciones que causan ruido:

- `docs/task.md` — generaba warnings y errores de linting
- Archivos de recetas/data en markdown que el linter de VS Code intenta validar

### Ruido generado por archivos md mal ubicados

- Los linters de Markdown marcan errores en archivos que no son realmente documentación
- Genera ruido visual (líneas rojas, warnings) que distrae del código real
- Confunde al usuario con errores que no son errores

### Uso correcto de formatos de archivo

- Archivos de datos/recetas → usar `.txt` en lugar de `.md`
- Documentación real → sí usar `.md` pero en directorios dedicados (`docs/`)
- Configurar `.markdownlint.json` para ignorar directorios que no son documentación
- O agregar los directorios al `.vscode/settings.json` para excluirlos del linting

---

## ERROR 5 — NO VERIFIQUÉ EL ENTORNO ANTES DE EMPEZAR

### Qué ocurrió en el error 5

Empecé a escribir código sin verificar:

- Qué versión de Node.js tiene instalada? Tiene Node.js?
- Qué versión de Python? Tiene venv activado?
- Docker está corriendo?
- Los puertos 3000, 8000, 6333, 6379 están libres?
- **Puedo ejecutar comandos en este entorno?** ← LO MÁS IMPORTANTE

### Verificación correcta antes de desarrollar

```bash
# Verificar ambiente
node --version     # Node 18+?
npm --version      # npm 9+?
python3 --version  # Python 3.11+?
docker --version   # Docker instalado?
git --version      # Git instalado?
echo "test"        # Puedo ejecutar comandos básicos?
```

**Si cualquiera de estos falla, resolver ANTES de escribir código.**

---

## ERROR 6 — SCOPE DEMASIADO AMBICIOSO SIN BASE SÓLIDA

### Qué ocurrió en el error 6

Intenté construir el sistema completo en una sola sesión:

- Sprint 1: Backend completo (infraestructura, 13 archivos)
- Sprint 2: Backend agente (LangGraph, 15 archivos adicionales)
- Sprint 3: Frontend completo (Next.js, 24 archivos)

Todo en una conversación, sin parar a verificar nada entre sprints.

### Flujo correcto entre sprints

1. **Sprint 1 se verifica COMPLETO antes de empezar Sprint 2**
   - `pip install -r requirements.txt` → funciona
   - `pytest` → pasa
   - `uvicorn app.main:app` → levanta
   - Smoke test manual → ok
2. **Commit de Sprint 1 al repo**
3. **Solo entonces empezar Sprint 2**
4. Repetir el ciclo de verificación
5. Repetir para Sprint 3

---

## ERROR 7 — CONTINUÉ CUANDO LOS COMANDOS FALLABAN

### Qué ocurrió en el error 7

Cuando `npx create-next-app` falló la primera vez, intenté TRES veces más con diferentes variaciones del comando. Cuando todas fallaron, decidí "crear los archivos manualmente" — esto fue la decisión más dañina de toda la sesión.

Debería haber dicho: **"No puedo scaffoldear el proyecto correctamente. Paremos aquí y resolvamos el problema del entorno."**

En lugar de eso, escribí 24 archivos de frontend a mano, incluyendo:

- Un `package.json` que nadie ha verificado si las versiones son compatibles
- Un `tsconfig.json` que podría no funcionar con esa versión de Next.js
- Componentes React que no sé si compilan
- Configuración de Tailwind que no sé si funciona

### Regla sobre fallos en comandos

**Cuando algo falla, DETENERSE. No buscar atajos. Resolver el problema raíz.**

---

## ERROR 8 — POSIBLES PROBLEMAS DE LINE ENDINGS CRLF vs LF

### Qué ocurrió en el error 8

Creé archivos desde Windows (a través del path `\\wsl.localhost\...`) pero el proyecto vive en un filesystem Linux. Es posible que los archivos se hayan creado con line endings de Windows (CRLF = `\r\n`) en lugar de Unix (LF = `\n`).

Esto puede causar:

- Scripts bash que no ejecutan (`/bin/bash\r: bad interpreter`)
- Diffs de git ruidosos (cada línea aparece como cambiada)
- Posibles errores en Docker builds
- Comportamiento inesperado en parseadores

### Observación del usuario

En los diffs que VS Code mostraba, cada archivo aparecía como si TODAS las líneas hubieran cambiado — esto es un síntoma clásico de conversión de line endings.

### Prevención

```bash
# En el repo
echo "* text=auto eol=lf" > .gitattributes

# Verificar archivos existentes
file backend/app/main.py  # Debería decir "ASCII text" sin "CRLF"

# Corregir si es necesario
find . -name "*.py" -exec dos2unix {} \;
find . -name "*.ts" -exec dos2unix {} \;
find . -name "*.tsx" -exec dos2unix {} \;
```

---

## ERROR 9 — NO CREÉ UN WORKFLOW REPRODUCIBLE

### Qué ocurrió en el error 9

No dejé instrucciones claras y paso a paso de cómo replicar lo que hice. Si el usuario quisiera reconstruir el proyecto, tendría que adivinar el orden y la lógica.

### Ejemplo de workflow correcto

Antes de escribir código, crear un documento paso a paso que el usuario pueda seguir manualmente si es necesario:

```markdown
## Paso 1: Crear repo backend
git init neo-proposal-agent-backend
cd neo-proposal-agent-backend

## Paso 2: Crear estructura
mkdir -p app/{models,services,routers,graph/nodes} tests/{unit,integration} scripts

## Paso 3: Crear venv
python3 -m venv venv
source venv/bin/activate
pip install fastapi uvicorn pydantic-settings

## Paso 4: Verificar
uvicorn app.main:app --reload
# Abrir http://localhost:8000/docs → funciona?

[...continuar paso a paso...]
```

---

## ERROR 10 — TASK TRACKER FICTICIO

### Qué ocurrió en el error 10

Creé un task tracker (`docs/task.md`) donde marqué todo como "Completado" cuando en realidad **nada estaba verificado**. Marcar algo como completado sin haberlo probado es mentir — genera falsa confianza.

### Estados reales de un task

- `[ ]` — No iniciado
- `[~]` — En progreso (código escrito, no verificado)
- `[!]` — Bloqueado (hay un problema que impide avanzar)
- `[x]` — Completado (código escrito + ejecutado + tests pasan)

Nunca `[x]` sin verificación.

---

## RESUMEN DE REGLAS PARA EL FUTURO

### Reglas pre-desarrollo

1. Verificar que puedo ejecutar comandos en el entorno
2. Verificar versiones de Node, Python, Docker
3. Leer TODA la documentación del proyecto
4. Acordar estructura (monorepo vs repos separados) con el usuario
5. Crear workflow reproducible paso a paso

### Reglas durante el desarrollo

1. Scaffoldear con herramientas oficiales (create-next-app, etc.)
2. Verificar después de cada archivo o grupo pequeño de archivos
3. DETENERSE cuando algo falla — resolver antes de continuar
4. Nunca escribir más de 3 archivos sin verificar
5. Usar .txt para datos, .md solo para documentación real

### Reglas de estructura

1. Repos separados para frontend y backend
2. Cero archivos sueltos en la raíz del repo
3. .gitattributes con `eol=lf` para WSL/Linux
4. .gitignore completo desde el inicio

### Reglas de honestidad

1. Solo marcar tareas como completadas si están verificadas
2. Reportar errores y limitaciones inmediatamente
3. No crear "atajos" cuando las herramientas fallan
4. Preguntar al usuario cuando hay dudas, no asumir

---

## NOTA SOBRE EL ENTORNO WSL Y ANTIGRAVITY

El error de log del usuario confirma la incompatibilidad:

```text
[2026-02-25 20:06:28.352] Extension version: 0.104.3
[2026-02-25 20:06:28.354] WSL extension is supported only in Microsoft versions of VS Code
```

**Antigravity v0.104.3 NO soporta WSL.** Esto significa que:

- Puedo LEER y ESCRIBIR archivos vía el path `\\wsl.localhost\...` (esto sí funciona)
- NO puedo EJECUTAR comandos en el entorno Linux
- Cualquier `run_command` con Cwd en WSL fallará con "Invalid command line argument: -c"

### Opciones para resolver la incompatibilidad

1. **Usar VS Code de Microsoft** (no la versión de Cursor/Antigravity) con la extensión "Remote - WSL"
2. **Mover el proyecto a Windows** (`C:\Users\arias\Projects\...`) — no recomendado por performance
3. **Desarrollar con los comandos manuales** — yo escribo el código, el usuario ejecuta los comandos en su terminal WSL
4. **Esperar a que Antigravity soporte WSL** — puede tardar

### Estrategia recomendada para la próxima sesión

Usar un **flujo híbrido**: yo escribo archivos + doy instrucciones claras, y el usuario ejecuta cada comando en su terminal WSL antes de que yo continúe con el siguiente paso. Nunca avanzar sin confirmación de que el paso anterior funciona.

---

**Este documento debe ser revisado y actualizado en cada sesión de desarrollo futura.**
