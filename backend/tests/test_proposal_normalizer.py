"""Tests para el normalizador de propuestas markdown -> estructura."""
import pytest
from src.agent.nodes import _normalize_proposal_to_structure


# Fixture 1: Markdown canónico (headers ideales)
MARKDOWN_CANONICAL = """
### 🔍 DIAGNÓSTICO
- Alto costo operativo en conciliaciones manuales
- Errores frecuentes por procesos repetitivos
- Falta de trazabilidad en auditorías

### 💡 SOLUCIÓN PROPUESTA
- Automatización con RPA para conciliaciones
- Dashboard en tiempo real para monitoreo
- Integración con sistemas legacy

### 🏗️ ARQUITECTURA Y STACK
- Orquestador de procesos con [Python] y [Celery]
- Base de datos [PostgreSQL] para trazabilidad
- Frontend con [React] y [TypeScript]
- Quick Win: Automatizar top 3 procesos → 4 semanas
- Escala: Integrar sistemas adicionales → 8 semanas

### 📊 IMPACTO Y KPIs
- Reducción de tiempo: 70% en conciliaciones
- ROI esperado: 180% en 12 meses
- Errores: Reducción de 85% vs baseline

### 🗓️ ROADMAP
- **Fase 1 (Quick Win):** Piloto con 3 procesos críticos - 6 semanas
- **Fase 2 (Consolidación):** Escalado a 10 procesos - 12 semanas
- **Fase 3 (Optimización):** ML para detección de anomalías

### 🎯 SIGUIENTE PASO
- Reunión de validación de alcance con equipo de TI
- Definir procesos prioritarios para piloto
"""

# Fixture 2: Markdown con formato "Sección N"
MARKDOWN_SECCION_FORMAT = """
Sección 1: 🔍 Diagnóstico del Problema

- Procesos manuales consumen 40 horas/mes
- Riesgo de sanciones regulatorias por errores

Sección 2: 💡 Solución Propuesta

- Sistema automatizado de validación
- Alertas proactivas para excepciones

Sección 3: 🏗️ Arquitectura y Stack

- Backend en [Java] con [Spring Boot]
- Mensajería con [Kafka]
- Monitoreo con [Grafana]

Sección 4: 📊 Resultados Estimados

- Ahorro anual: $120K USD
- Time to market: 10 semanas

Sección 5: 🗓️ Roadmap Sugerido

- **Fase 1:** MVP funcional
- **Fase 2:** Integración completa

Sección 6: 🎯 Siguiente Paso Recomendado

- Kick-off meeting próxima semana
"""

# Fixture 3: Markdown con duplicación y artefacts
MARKDOWN_WITH_DUPLICATES = """
### 🔍 DIAGNÓSTICO

**Problema identificado:**
- Baja eficiencia en procesamiento de datos
- Sistemas legacy sin **integración**

### 💡 SOLUCIÓN

- Migración a arquitectura cloud
- [AWS] [Lambda] [S3] para storage

### 🏗️ ARQUITECTURA

- Stack moderno con [React] [Node.js]
- Microservicios en [Docker]

### 📊 IMPACTO

- **Métrica 1:** Reducción de costos 30%
- **Métrica 2:** Escalabilidad 10x

### 🗓️ ROADMAP

- Fase 1: Migración inicial
- Fase 2: Optimización

### 🎯 SIGUIENTE

- Validar con stakeholders
"""

# Fixture 4: Markdown parcial (falta sección roadmap)
MARKDOWN_PARTIAL = """
### 🔍 DIAGNÓSTICO
- Problema crítico necesita solución

### 💡 SOLUCIÓN
- Propuesta de valor clara

### 🏗️ ARQUITECTURA
- Tecnologías modernas [Python]

### 📊 IMPACTO
- ROI positivo esperado

### 🎯 SIGUIENTE
- Próximos pasos definidos
"""


def test_normalize_canonical_format():
    """Test con markdown formato canónico."""
    result = _normalize_proposal_to_structure(MARKDOWN_CANONICAL)

    assert 'diagnostico' in result
    assert 'solucion' in result
    assert 'arquitectura' in result
    assert 'impacto' in result
    assert 'roadmap' in result
    assert 'siguiente_paso' in result

    # Verificar bullets extraídos
    assert len(result['diagnostico']) >= 2
    assert 'conciliaciones' in result['diagnostico'][0].lower()

    # Verificar tags extraídos de arquitectura
    assert 'bullets' in result['arquitectura']
    assert 'tags' in result['arquitectura']
    assert 'Python' in result['arquitectura']['tags']
    assert 'PostgreSQL' in result['arquitectura']['tags']

    # Verificar limpieza de markdown artifacts
    for bullet in result['solucion']:
        assert '**' not in bullet
        assert '[' not in bullet or ']' not in bullet


def test_normalize_seccion_format():
    """Test con formato 'Sección N:'."""
    result = _normalize_proposal_to_structure(MARKDOWN_SECCION_FORMAT)

    assert len(result['diagnostico']) > 0
    assert len(result['solucion']) > 0
    assert len(result['arquitectura']['tags']) > 0

    # Verificar que se extraen tags correctamente
    assert 'Java' in result['arquitectura']['tags']
    assert 'Kafka' in result['arquitectura']['tags']


def test_normalize_with_duplicates():
    """Test con contenido duplicado y artefacts."""
    result = _normalize_proposal_to_structure(MARKDOWN_WITH_DUPLICATES)

    # Todas las secciones deben tener contenido
    assert len(result['diagnostico']) > 0
    assert len(result['solucion']) > 0

    # No debe haber markdown artifacts
    for section_key in ['diagnostico', 'solucion', 'impacto']:
        for bullet in result[section_key]:
            assert '**' not in bullet  # Sin negritas
            assert not bullet.startswith('[')  # Tags removidos


def test_normalize_partial_with_fallbacks():
    """Test con sección faltante - debe usar fallback."""
    result = _normalize_proposal_to_structure(MARKDOWN_PARTIAL)

    # Sección roadmap falta en el markdown
    assert 'roadmap' in result
    assert len(result['roadmap']) > 0  # Debe tener fallback

    # Verificar que el fallback tiene contenido válido
    assert 'Fase 1' in result['roadmap'][0] or 'Quick Win' in result['roadmap'][0]


def test_normalize_empty_input():
    """Test con entrada vacía - debe devolver estructura con fallbacks."""
    result = _normalize_proposal_to_structure("")

    # Todas las secciones deben existir con fallbacks
    assert result['diagnostico']
    assert result['solucion']
    assert result['arquitectura']['bullets']
    assert result['impacto']
    assert result['roadmap']
    assert result['siguiente_paso']


def test_normalize_max_bullets_limit():
    """Test que verifica límite de bullets por sección."""
    long_markdown = """
### 🔍 DIAGNÓSTICO
- Punto 1
- Punto 2
- Punto 3
- Punto 4
- Punto 5
- Punto 6
- Punto 7
- Punto 8
"""
    result = _normalize_proposal_to_structure(long_markdown)

    # Máximo 5 bullets por sección
    assert len(result['diagnostico']) <= 5


def test_normalize_max_tags_limit():
    """Test que verifica límite de tags."""
    markdown_with_many_tags = """
### 🏗️ ARQUITECTURA
- Stack: [Python] [React] [PostgreSQL] [Redis] [Docker] [K8s] [AWS] [Lambda] [S3] [DynamoDB]
"""
    result = _normalize_proposal_to_structure(markdown_with_many_tags)

    # Máximo 8 tags
    assert len(result['arquitectura']['tags']) <= 8
