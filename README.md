# 🖥 Mac DevOps Toolkit Pro

CLI para macOS que cubre dos grandes áreas:

- **Disk cleanup** — escanea 11 dominios en paralelo, muestra severidad y riesgo, borra solo lo que apruebes
- **System monitors** — batería, CPU/memoria, procesos y red en tiempo real

Ejecutar `toolkit` sin argumentos abre el **menú interactivo**.

## Instalación

```bash
git clone git@github-portfolio:Portfolio-jaime/mac-toolkit-pro.git
cd mac-toolkit-pro
pip install -e .
toolkit    # abre el menú interactivo
```

Sin instalar, desde el repo:
```bash
pip install click rich questionary psutil
./toolkit --help
```

## Uso rápido

```bash
# Menú interactivo (sin argumentos)
toolkit

# Disk cleanup
toolkit analyze
toolkit clean --execute --mode checklist
toolkit analyze --domain dev_caches
toolkit full --execute

# Monitors
toolkit battery
toolkit system
toolkit processes
toolkit network
```

## Monitors

| Comando | Qué muestra |
|---------|-------------|
| `toolkit battery` | Salud, ciclos, temperatura, voltaje, tiempo restante |
| `toolkit system` | Modelo, CPU%, memoria, swap, estado térmico |
| `toolkit processes` | Top 10 por CPU y top 10 por memoria |
| `toolkit network` | WiFi, estadísticas de red, conexiones activas, conectividad |

## Disk Cleanup — Dominios

| Dominio | Qué limpia | Riesgo |
|---------|-----------|--------|
| `ollama` | Modelos LLM descargados | 🔴 danger |
| `docker` | Imagen virtual de Docker | 🔴 danger |
| `dev_caches` | npm, pip, brew, Gradle, Maven, Cargo, Go | 🟢 safe |
| `browser` | Cachés Chrome, Safari, Firefox, Edge | 🟢 safe |
| `logs` | Logs del sistema y apps (>7 días) | 🟢 safe |
| `repos` | node_modules, .venv, __pycache__ en repos | 🟢 safe |
| `xcode` | DerivedData, Simulators, Archives | 🟢/🟡 |
| `downloads` | Archivos grandes, ZIPs, duplicados | 🟡 warn |
| `appsupport` | Application Support de apps | 🟡 warn |
| `trash` | Papelera (`~/.Trash`) | 🟡 warn |
| `disk` | Uso total del volumen APFS | — |

## Comandos de cleanup

| Comando | Descripción |
|---------|-------------|
| `toolkit analyze` | Análisis completo sin borrar |
| `toolkit analyze --domain <d>` | Solo un dominio |
| `toolkit analyze --save` | Guardar reporte MD + JSON |
| `toolkit clean` | Simular limpieza |
| `toolkit clean --execute` | Limpiar de verdad |
| `toolkit clean --domain <d>` | Limpiar un dominio |
| `toolkit clean --mode checklist` | Selección manual ítem a ítem |
| `toolkit full --execute` | Analizar + guardar + limpiar |
| `toolkit status` | Ver dominios y niveles de riesgo |
| `toolkit report --last` | Ver último reporte guardado |

## Modos de aprobación (`--mode`)

- `deal` — resumen total → aprueba por categoría (default)
- `category` — s/N por cada dominio
- `item` — s/N por cada archivo individual
- `checklist` — checkbox interactivo con flechas + espacio

## Seguridad

- Sin `--execute` **nunca borra nada** — todo es dry-run por defecto
- Antes de borrar muestra tabla de **preview** con tamaño, riesgo y antigüedad
- `/System`, `/usr`, `/bin`, `/sbin` en lista negra permanente
- Cada sesión genera un `audit.json` con log de lo eliminado

## Desarrollo

```bash
# Tests (59 tests)
pytest tests/

# Test de un módulo
pytest tests/test_monitor_battery.py -v

# Estructura del paquete
mac_toolkit_pro/
  cli.py           # Entry point Click + menú sin args
  menu.py          # Menú interactivo (questionary)
  core/            # config, models, runner, approval
  analyzers/       # un archivo por dominio (11 dominios)
  monitors/        # battery, system, processes, network
  cleaners/        # GenericCleaner con blacklist
  reporters/       # terminal, markdown, json, audit
```

Ver [TOOLKIT_GUIDE.md](TOOLKIT_GUIDE.md) para referencia completa de flags y flujos.

---

*Mac DevOps Toolkit Pro v3.0 — [Portfolio-jaime](https://github.com/Portfolio-jaime)*
