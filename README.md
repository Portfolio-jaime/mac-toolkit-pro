# 🖥 Mac DevOps Toolkit Pro

Herramienta CLI para analizar y limpiar espacio en disco en macOS. Escanea 11 dominios en paralelo, muestra severidad y riesgo, y borra solo lo que apruebes.

## Instalación

```bash
git clone git@github-portfolio:Portfolio-jaime/mac-toolkit-pro.git
cd mac-toolkit-pro
pip install -e .
toolkit --help
```

O sin instalar, desde el repo:
```bash
pip install click rich questionary
./toolkit --help
```

## Uso rápido

```bash
# Ver qué ocupa espacio
toolkit analyze

# Ver dominios disponibles y su nivel de riesgo
toolkit status

# Simular limpieza (nunca borra sin --execute)
toolkit clean

# Limpiar de verdad con aprobación interactiva
toolkit clean --execute --mode checklist

# Solo un dominio
toolkit analyze --domain dev_caches
toolkit clean --execute --domain xcode

# Flujo completo: analiza → guarda reporte → limpia
toolkit full --execute
```

## Dominios (v2)

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

## Monitors

| Comando | Descripción |
|---------|-------------|
| `toolkit battery` | Salud, ciclos, temperatura y estado de carga |
| `toolkit system` | CPU, memoria, swap y estado térmico |
| `toolkit processes` | Top procesos por CPU y memoria |
| `toolkit network` | WiFi, estadísticas de red y conectividad |

Ejecutar `toolkit` sin argumentos abre el **menú interactivo**.

## Comandos

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
# Tests
pytest tests/

# Test de un módulo
pytest tests/test_cli_domain.py -v

# Estructura del paquete
mac_toolkit_pro/
  cli.py           # Entry point Click
  core/            # config, models, runner, approval
  analyzers/       # un archivo por dominio
  cleaners/        # GenericCleaner con blacklist
  reporters/       # terminal, markdown, json, audit
```

Ver [TOOLKIT_GUIDE.md](TOOLKIT_GUIDE.md) para referencia completa de flags y flujos.

---

*Mac DevOps Toolkit Pro v2.0 — [Portfolio-jaime](https://github.com/Portfolio-jaime)*
