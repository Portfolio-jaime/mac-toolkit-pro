# 🖥 Mac DevOps Toolkit Pro — Guía de Comandos

**Repo:** [Portfolio-jaime/mac-toolkit-pro](https://github.com/Portfolio-jaime/mac-toolkit-pro)  
**Entry point:** `toolkit` (tras `pip install -e .`) o `./toolkit` (desde el repo)  
**Versión:** 3.0

---

## Instalación

### Opción A — pip (recomendado)
```bash
git clone git@github-portfolio:Portfolio-jaime/mac-toolkit-pro.git
cd mac-toolkit-pro
pip install -e .
toolkit    # abre el menú interactivo
```

### Opción B — desde el repo sin instalar
```bash
pip install click rich questionary psutil
./toolkit --help
```

---

## Menú interactivo

Ejecutar `toolkit` sin argumentos abre un menú con todas las opciones:

```bash
toolkit
```

```
Mac DevOps Toolkit Pro — choose an action

❯ 🔍 Analyze disk (all domains)
  🧹 Clean disk (interactive)
  📊 Full flow (analyze + clean)
  📋 Domain status
  🔋 Battery health
  💻 System (CPU / memory)
  ⚙️  Processes (top CPU / mem)
  🌐 Network
  ❌ Quit
```

---

## Monitors

### `battery` — Salud de la batería

```bash
toolkit battery
```

Muestra: salud (%), ciclos, carga actual, si está cargando, tiempo restante, temperatura, voltaje, capacidad máxima vs diseño.

---

### `system` — CPU y memoria

```bash
toolkit system
```

Muestra: modelo del chip, núcleos, RAM total, CPU%, memoria usada/total, swap, estado térmico (pmset).

---

### `processes` — Top procesos

```bash
toolkit processes
```

Muestra: presión de memoria, top 10 por CPU% y top 10 por memoria%, con PID, nombre, usuario y color por severidad.

---

### `network` — Red y conectividad

```bash
toolkit network
```

Muestra: estado de conectividad (online/offline), SSID WiFi, RSSI, canal, total enviado/recibido, paquetes, conexiones activas.

---

## Disk Cleanup

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

## Dominios de disco (11)

| Dominio | Qué escanea | Riesgo |
|---------|-------------|--------|
| `disk` | Volumen APFS — uso total | — |
| `ollama` | `~/.ollama/models/blobs` — modelos LLM | 🔴 danger |
| `docker` | `Docker.raw` — imagen virtual | 🔴 danger |
| `browser` | Cachés Chrome, Safari, Firefox, Edge | 🟢 safe |
| `logs` | `~/Library/Logs`, `/var/log` (>7 días) | 🟢 safe |
| `downloads` | `~/Downloads`, `~/Desktop` — ZIPs, duplicados | 🟡 warn |
| `appsupport` | `~/Library/Application Support` | 🟡 warn |
| `repos` | repos locales — node_modules, .venv, __pycache__ | 🟢 safe |
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
  analysis_20260620_143022/
    report.md      # Reporte en Markdown
    report.json    # Datos para automatización
  cleanup_20260620_150000/
    audit.json     # Log de lo borrado (path, bytes, resultado)
```

---

## Flujos recomendados

### Primera vez — ver todo de un vistazo
```bash
toolkit           # menú interactivo
```

### Diagnóstico completo antes de limpiar
```bash
toolkit system    # cuánta RAM queda
toolkit battery   # salud de la batería
toolkit analyze   # qué ocupa espacio
```

### Liberar espacio de dev caches en un paso
```bash
toolkit clean --execute --domain dev_caches
```

### Limpieza segura completa
```bash
toolkit full --mode deal            # simula primero
toolkit full --execute --mode deal  # ejecuta si el resultado te gusta
```

### Limpieza quirúrgica de Xcode
```bash
toolkit analyze --domain xcode --verbose
toolkit clean --execute --domain xcode --mode item
```

### Monitorear rendimiento antes de una demo
```bash
toolkit processes   # ver qué procesos consumen más
toolkit system      # CPU y memoria actuales
toolkit network     # conectividad y estadísticas
```

---

## Seguridad

- **Sin `--execute` todo es simulación** — nunca borra accidentalmente
- **Preview antes de borrar** — tabla con tamaño, riesgo y antigüedad de cada item
- **Lista negra** — `/System`, `/usr`, `/bin`, `/sbin` y prefs de sistema nunca se tocan
- **Audit log** — cada sesión de limpieza queda en `reports/cleanup_*/audit.json`
- **Timeout 120s por dominio** — resultado parcial si un dominio tarda demasiado

---

## Estructura del paquete

```
mac_toolkit_pro/
  cli.py              # Click CLI + invoca menú si no hay subcomando
  menu.py             # Menú interactivo con questionary
  core/
    config.py         # Paths, thresholds, blacklist
    models.py         # CleanableItem, AnalysisResult
    runner.py         # run_analyzers() — paralelo con ThreadPoolExecutor
    approval.py       # ApprovalEngine — modos deal/category/item/checklist
  analyzers/          # Un archivo por dominio de disco (11 total)
  monitors/
    base.py           # BaseMonitor ABC
    battery.py        # ioreg + pmset
    system.py         # psutil + system_profiler
    processes.py      # psutil process_iter
    network.py        # psutil + urllib (sin requests)
  cleaners/
    generic.py        # GenericCleaner con blacklist
  reporters/
    terminal.py       # Rich console + print_preview_table()
    markdown.py       # Guarda report.md
    json_reporter.py  # Guarda report.json
    audit.py          # Escribe audit.json post-cleanup
```

---

*Mac DevOps Toolkit Pro v3.0 — Jaime Henao*
