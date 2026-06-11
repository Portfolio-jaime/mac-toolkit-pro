# 🖥 Mac DevOps Toolkit Pro — Guía de Comandos

**Ruta:** `scripts-mac/`  
**Entry point:** `./toolkit`

---

## Instalación rápida

```bash
cd scripts-mac
pip3 install click rich questionary pytest
./toolkit --help
```

---

## Comandos principales

### `analyze` — Solo análisis (nunca borra)

```bash
# Análisis completo de los 8 dominios en paralelo
./toolkit analyze

# Análisis + guardar reportes (MD + JSON en reports/)
./toolkit analyze --save

# Mostrar todos los archivos encontrados
./toolkit analyze --verbose

# Filtrar por tamaño mínimo (default: 50MB)
./toolkit analyze --verbose --min-size 200

# Todo junto
./toolkit analyze --save --verbose --min-size 100
```

---

### `clean` — Analizar + limpiar con aprobación

> ⚠️ **Por defecto es SIMULACIÓN.** Agrega `--execute` para borrar de verdad.

```bash
# Simulación (modo deal — resumen → aprueba por categoría)
./toolkit clean

# Ver qué limpiaría, pregunta por categoría
./toolkit clean --mode category

# Ítem por ítem (el más granular)
./toolkit clean --mode item

# Menú tipo checkbox con flechas + espacio
./toolkit clean --mode checklist

# Resumen total primero → luego por categoría (default)
./toolkit clean --mode deal

# ⚡ EJECUCIÓN REAL — borra archivos aprobados
./toolkit clean --execute

# REAL con modo específico
./toolkit clean --execute --mode category
./toolkit clean --execute --mode checklist

# REAL filtrando solo archivos >500MB
./toolkit clean --execute --mode deal --min-size 500
```

---

### `full` — Flujo completo: analiza → reporta → limpia

```bash
# Simulación completa (nunca borra)
./toolkit full

# Simulación con modo checklist
./toolkit full --mode checklist

# Ejecución real
./toolkit full --execute

# Ejecución real con aprobación por categoría
./toolkit full --execute --mode category
```

---

### `report` — Ver reportes guardados

```bash
# Ver el último reporte guardado
./toolkit report --last

# Los reportes se guardan en:
ls reports/
```

---

## Dominios que analiza

| Dominio | Qué escanea |
|---------|------------|
| `disk` | Volumen APFS — uso total del disco |
| `ollama` | `~/.ollama/models/blobs` — modelos LLM |
| `docker` | `Docker.raw` — imagen virtual de Docker |
| `browser` | Cachés Chrome, Safari, Firefox, Edge |
| `logs` | `~/Library/Logs`, `/var/log` (>7 días) |
| `downloads` | `~/Downloads`, `~/Desktop` — archivos grandes, ZIPs, duplicados |
| `appsupport` | `~/Library/Application Support` por app |
| `repos` | `~/arqueanja`, `~/arheanja` — node_modules, .venv, __pycache__ |

---

## Modos de aprobación

| Modo | Comportamiento |
|------|---------------|
| `deal` | Muestra total → pregunta si arrancar → confirma por categoría |
| `category` | Muestra cada categoría y pregunta s/N |
| `item` | Muestra cada archivo individual y pregunta s/N |
| `checklist` | Menú interactivo con flechas + espacio para seleccionar |

---

## Flags globales

| Flag | Descripción | Default |
|------|-------------|---------|
| `--execute` | Borra de verdad (requerido para limpiar) | `False` (dry-run) |
| `--save` | Guarda reportes MD + JSON | `False` |
| `--verbose` | Muestra todos los items encontrados | `False` |
| `--min-size N` | Tamaño mínimo en MB para mostrar | `50` |
| `--mode` | Modo de aprobación | `deal` |

---

## Reportes generados

Cada `analyze --save` o `full` crea:
```
reports/
  analysis_20260316_143022/
    report.md      ← Reporte legible en Markdown
    report.json    ← Datos estructurados para automatización
    audit.json     ← Log de auditoría de lo que se borró
```

---

## Flujos recomendados

### 1. Diagnóstico rápido
```bash
./toolkit analyze
```

### 2. Investigación + reporte guardado
```bash
./toolkit analyze --save --verbose
```

### 3. Limpieza segura (recomendado)
```bash
# Primero simula
./toolkit full --mode deal

# Si el resultado te gusta, ejecuta
./toolkit full --execute --mode deal
```

### 4. Limpieza quirúrgica
```bash
# Ver todo, seleccionar manualmente
./toolkit clean --execute --mode checklist
```

---

## Casos de uso frecuentes

### Liberar espacio de Ollama
```bash
./toolkit clean --execute --mode item
# Aprueba solo los blobs de modelos que no usas
```

### Limpiar cachés del navegador
```bash
./toolkit clean --execute --mode category
# Aprueba solo "browser"
```

### Limpiar repos (node_modules, .venv)
```bash
./toolkit clean --execute --mode category
# Aprueba solo "repos"
```

### Ver archivos >1GB en Downloads/Desktop
```bash
./toolkit analyze --verbose --min-size 1000
```

---

## Seguridad

- **Nunca borra sin `--execute`** — por defecto todo es simulación
- **Lista negra protegida** — `/System`, `/usr`, `/bin`, `/sbin`, `com.apple.dock`, `com.apple.finder`, `com.apple.spotlight` nunca se tocan
- **Audit log** — cada sesión de limpieza queda registrada en `reports/cleanup_*/audit.json`
- **Timeout 30s por dominio** — si un dominio tarda mucho, devuelve resultado parcial sin bloquear

---

*Mac DevOps Toolkit Pro — Jaime Henao*
