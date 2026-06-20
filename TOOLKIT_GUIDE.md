# 🖥 Mac DevOps Toolkit Pro — Guía de Comandos

**Repo:** [Portfolio-jaime/mac-toolkit-pro](https://github.com/Portfolio-jaime/mac-toolkit-pro)  
**Entry point:** `toolkit` (tras `pip install -e .`) o `./toolkit` (desde el repo)

---

## Instalación

### Opción A — pip (recomendado)
```bash
git clone git@github-portfolio:Portfolio-jaime/mac-toolkit-pro.git
cd mac-toolkit-pro
pip install -e .
toolkit --help    # disponible globalmente
```

### Opción B — desde el repo sin instalar
```bash
pip install click rich questionary
./toolkit --help
```

---

## Comandos

### `analyze` — Solo análisis, nunca borra

```bash
# Análisis completo (11 dominios en paralelo)
toolkit analyze

# Guardar reportes MD + JSON en reports/
toolkit analyze --save

# Mostrar todos los items encontrados
toolkit analyze --verbose

# Filtrar por tamaño mínimo (default 50MB)
toolkit analyze --verbose --min-size 200

# Solo un dominio específico
toolkit analyze --domain dev_caches
toolkit analyze --domain xcode --verbose
```

---

### `clean` — Analizar + limpiar con aprobación interactiva

> ⚠️ Por defecto es **SIMULACIÓN**. Agrega `--execute` para borrar de verdad.
> Antes de borrar muestra una tabla de preview con tamaño, riesgo y antigüedad.

```bash
# Simulación — modo deal (default)
toolkit clean

# Pregunta por categoría
toolkit clean --mode category

# Ítem por ítem (más granular)
toolkit clean --mode item

# Checkbox interactivo con flechas + espacio
toolkit clean --mode checklist

# Solo un dominio
toolkit clean --domain dev_caches
toolkit clean --domain xcode --mode item

# ⚡ EJECUCIÓN REAL
toolkit clean --execute
toolkit clean --execute --mode checklist
toolkit clean --execute --domain dev_caches
toolkit clean --execute --min-size 500
```

---

### `status` — Ver todos los dominios registrados

```bash
toolkit status
# Muestra tabla: dominio, clase, nivel de riesgo
```

---

### `full` — Flujo completo: analiza → guarda reportes → limpia

```bash
# Simulación completa
toolkit full

# Ejecución real con checklist
toolkit full --execute --mode checklist

# Ejecución real modo deal
toolkit full --execute
```

---

### `report` — Ver reportes guardados

```bash
toolkit report --last
ls reports/
```

---

## Dominios (11 en v2)

| Dominio | Qué escanea | Riesgo |
|---------|-------------|--------|
| `disk` | Volumen APFS — uso total | — |
| `ollama` | `~/.ollama/models/blobs` — modelos LLM | 🔴 danger |
| `docker` | `Docker.raw` — imagen virtual | 🔴 danger |
| `browser` | Cachés Chrome, Safari, Firefox, Edge | 🟢 safe |
| `logs` | `~/Library/Logs`, `/var/log` (>7 días) | 🟢 safe |
| `downloads` | `~/Downloads`, `~/Desktop` — ZIPs, duplicados | 🟡 warn |
| `appsupport` | `~/Library/Application Support` | 🟡 warn |
| `repos` | `~/arqueanja`, `~/arheanja` — node_modules, .venv | 🟢 safe |
| `dev_caches` | npm, pip, brew, Gradle, Maven, Cargo, Go | 🟢 safe |
| `xcode` | DerivedData, Simulators (safe) · Archives (warn) | 🟢/🟡 |
| `trash` | `~/.Trash` | 🟡 warn |

---

## Modos de aprobación

| Modo | Comportamiento |
|------|---------------|
| `deal` | Total → confirma arrancar → aprueba por categoría |
| `category` | Pregunta s/N por cada dominio |
| `item` | Pregunta s/N por cada archivo individual |
| `checklist` | Menú flechas + espacio para selección múltiple |

---

## Flags

| Flag | Comandos | Descripción | Default |
|------|----------|-------------|---------|
| `--execute` | clean, full | Borra de verdad | `False` (dry-run) |
| `--domain` | analyze, clean | Solo este dominio | todos |
| `--save` | analyze | Guarda reportes MD + JSON | `False` |
| `--verbose` | analyze | Muestra todos los items | `False` |
| `--min-size N` | analyze, clean | Tamaño mínimo en MB | `50` |
| `--mode` | clean, full | Modo de aprobación | `deal` |

---

## Reportes generados

```
reports/
  analysis_20260619_143022/
    report.md      # Reporte en Markdown
    report.json    # Datos para automatización
  cleanup_20260619_150000/
    audit.json     # Log de lo borrado (path, bytes, resultado)
```

---

## Flujos recomendados

### Diagnóstico rápido
```bash
toolkit analyze
```

### Liberar espacio de dev caches en un paso
```bash
toolkit clean --execute --domain dev_caches
```

### Limpieza segura completa
```bash
toolkit full --mode deal          # simula primero
toolkit full --execute --mode deal  # ejecuta si el resultado te gusta
```

### Limpieza quirúrgica de Xcode
```bash
toolkit analyze --domain xcode --verbose
toolkit clean --execute --domain xcode --mode item
```

### Ver archivos grandes en Downloads
```bash
toolkit analyze --domain downloads --verbose --min-size 500
```

---

## Seguridad

- **Sin `--execute` todo es simulación** — nunca borra accidentalmente
- **Preview antes de borrar** — tabla con tamaño, riesgo y antigüedad de cada item
- **Lista negra** — `/System`, `/usr`, `/bin`, `/sbin` y prefs de sistema nunca se tocan
- **Audit log** — cada sesión de limpieza queda en `reports/cleanup_*/audit.json`
- **Timeout 120s por dominio** — resultado parcial si un dominio tarda demasiado

---

*Mac DevOps Toolkit Pro v2.0 — Jaime Henao*
