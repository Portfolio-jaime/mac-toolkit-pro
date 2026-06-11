# 🍎 Scripts de Mantenimiento Mac M1

Colección de scripts en Python para monitorear, analizar y mantener tu Mac M1 en óptimas condiciones.

## 📁 Scripts Disponibles

### 1. 💾 `mac_storage_analyzer.py` - Analizador de Almacenamiento
Analiza el uso del disco y encuentra archivos/directorios que consumen más espacio.

```bash
# Análisis básico del directorio home
python3 mac_storage_analyzer.py

# Analizar directorio específico
python3 mac_storage_analyzer.py -d /Applications

# Buscar archivos grandes de 50MB+
python3 mac_storage_analyzer.py -f 50

# Mostrar top 20 elementos
python3 mac_storage_analyzer.py -t 20
```

**Características:**
- Análisis de uso del disco por directorios
- Detección de archivos grandes
- Información del sistema de almacenamiento
- Análisis de cachés y archivos temporales

### 2. 🖥️ `mac_system_monitor.py` - Monitor del Sistema
Monitorea CPU, memoria, temperatura y rendimiento en tiempo real.

```bash
# Análisis único del sistema
python3 mac_system_monitor.py

# Monitor continuo cada 5 segundos
python3 mac_system_monitor.py -c -i 5

# Exportar datos a JSON
python3 mac_system_monitor.py -e system_report.json
```

**Características:**
- Monitoreo de CPU y memoria
- Información del chip M1
- Estado térmico del sistema
- Top procesos por consumo de recursos
- Información de energía

### 3. 🔋 `mac_battery_analyzer.py` - Analizador de Batería
Analiza la salud, ciclos y optimización energética de la batería.

```bash
# Análisis completo de batería
python3 mac_battery_analyzer.py

# Monitor continuo cada 60 segundos
python3 mac_battery_analyzer.py -m -i 60

# Registrar datos históricos
python3 mac_battery_analyzer.py -l battery_log.json

# Exportar análisis
python3 mac_battery_analyzer.py -e battery_report.json
```

**Características:**
- Salud y ciclos de la batería
- Temperatura y voltaje
- Estimaciones de tiempo restante
- Recomendaciones de optimización
- Historial de datos

### 4. 🌐 `mac_network_monitor.py` - Monitor de Red
Analiza conexiones, velocidad y calidad de red.

```bash
# Análisis de red completo
python3 mac_network_monitor.py

# Monitor continuo
python3 mac_network_monitor.py -m -i 30

# Prueba de velocidad
python3 mac_network_monitor.py -s

# Diagnóstico de problemas
python3 mac_network_monitor.py -d

# Exportar información
python3 mac_network_monitor.py -e network_report.json
```

**Características:**
- Información de interfaces de red
- Análisis detallado de WiFi
- Pruebas de conectividad
- Estadísticas de uso de red
- Conexiones activas
- Diagnóstico de problemas

### 5. ⚙️ `mac_process_manager.py` - Administrador de Procesos
Gestiona procesos, memoria y optimización del sistema.

```bash
# Ver estado de recursos
python3 mac_process_manager.py

# Monitor continuo
python3 mac_process_manager.py -m -i 5

# Modo interactivo
python3 mac_process_manager.py -I

# Matar proceso por PID
python3 mac_process_manager.py --kill-pid 1234

# Matar procesos por nombre
python3 mac_process_manager.py --kill-name "Chrome" -f

# Liberar memoria
python3 mac_process_manager.py --free-memory
```

**Características:**
- Monitoreo de CPU y memoria
- Top procesos por consumo
- Detección de procesos problemáticos
- Administrador interactivo
- Liberación de memoria
- Gestión de procesos zombie

### 6. 🧹 `mac_maintenance_cleaner.py` - Limpiador y Mantenimiento
Limpia cachés, logs, archivos temporales y optimiza el sistema.

```bash
# Simulación (no hace cambios)
python3 mac_maintenance_cleaner.py --dry-run --all

# Limpieza completa
python3 mac_maintenance_cleaner.py --all

# Limpiezas específicas
python3 mac_maintenance_cleaner.py -c  # Cachés
python3 mac_maintenance_cleaner.py -l  # Logs
python3 mac_maintenance_cleaner.py -d  # Duplicados
python3 mac_maintenance_cleaner.py -t  # Papelera
python3 mac_maintenance_cleaner.py -b  # Navegadores

# Optimizar sistema
python3 mac_maintenance_cleaner.py -o

# Encontrar archivos grandes
python3 mac_maintenance_cleaner.py -f 1000  # >1GB

# Generar reporte
python3 mac_maintenance_cleaner.py --all -r cleanup_report.txt
```

**Características:**
- Limpieza de cachés del sistema
- Eliminación de logs antiguos
- Detección de archivos duplicados
- Vaciado de papelera
- Limpieza de datos de navegadores
- Optimización del sistema
- Búsqueda de archivos grandes
- Reportes detallados

## 🚀 Uso Rápido

### Ejecutar el Toolkit Principal
```bash
# Ejecutar el centro de control principal
python3 mac_toolkit.py
```

El **Mac Toolkit** (`mac_toolkit.py`) es el script principal que organiza todos los demás scripts en un menú interactivo fácil de usar.

### Características del Toolkit:
- 🎯 **Menú principal** organizado por categorías
- 🚀 **Análisis rápido** del sistema completo
- 📊 **Análisis completo** con generación de reportes
- 🧹 **Mantenimiento guiado** con confirmaciones de seguridad
- 📈 **Monitoreo en tiempo real** con múltiples opciones
- 🛠️ **Herramientas específicas** para tareas puntuales
- 📁 **Gestión de reportes** automática

## 🚀 Instalación

### Dependencias
```bash
# Instalar psutil para monitoreo del sistema
pip3 install psutil requests
```

### Permisos
Algunos scripts requieren permisos de administrador para funcionalidades avanzadas:

```bash
# Para limpieza del sistema y optimización
sudo python3 mac_maintenance_cleaner.py --all

# Para monitoreo avanzado de procesos
sudo python3 mac_process_manager.py -I
```

## 📊 Ejemplos de Uso Común

### Análisis Completo del Sistema
```bash
# 1. Verificar almacenamiento
python3 mac_storage_analyzer.py

# 2. Estado del sistema
python3 mac_system_monitor.py

# 3. Salud de la batería
python3 mac_battery_analyzer.py

# 4. Estado de la red
python3 mac_network_monitor.py

# 5. Procesos problemáticos
python3 mac_process_manager.py

# 6. Limpieza (simulación)
python3 mac_maintenance_cleaner.py --dry-run --all
```

### Mantenimiento Semanal
```bash
# Ejecutar limpieza completa
python3 mac_maintenance_cleaner.py --all -r weekly_cleanup.txt

# Optimizar sistema
python3 mac_maintenance_cleaner.py -o

# Verificar mejoras
python3 mac_storage_analyzer.py
```

### Monitoreo en Tiempo Real
```bash
# En terminales separadas:
python3 mac_system_monitor.py -c
python3 mac_process_manager.py -m
python3 mac_network_monitor.py -m
```

## ⚠️ Recomendaciones Importantes

### Seguridad
- **Siempre** usa `--dry-run` antes de ejecutar limpiezas
- Revisa los archivos antes de eliminarlos
- Haz backups antes de limpiezas masivas

### Optimización
- Ejecuta limpieza semanal para mantener rendimiento
- Monitorea la salud de la batería regularmente
- Revisa procesos de alto consumo periódicamente

### Archivos Específicos Detectados
Basado en tu análisis anterior:

```bash
# Docker (200GB) - Limpieza específica
docker system prune -a

# Logs grandes de BrowserLock (8.3GB)
# Revisar configuración en BrowserLock

# Modelos Ollama (12.8GB)
ollama rm <modelo_no_usado>

# Múltiples versiones de Edge
# Usar el limpiador de navegadores
```

## 🛠️ Solución de Problemas

### Script no ejecuta
```bash
chmod +x mac_*.py
python3 mac_script.py
```

### Sin permisos
```bash
sudo python3 mac_script.py
```

### Dependencias faltantes
```bash
pip3 install psutil requests
```

## 📈 Interpretación de Resultados

### Estado de Batería
- **>80%**: Excelente
- **70-80%**: Buena
- **60-70%**: Aceptable
- **<60%**: Necesita reemplazo

### Uso de Memoria
- **<70%**: Normal
- **70-85%**: Moderado
- **>85%**: Alto (considerar limpieza)

### Temperatura CPU
- **<35°C**: Normal
- **35-70°C**: Caliente pero aceptable
- **>70°C**: Verificar ventilación

---

**💡 Consejo**: Ejecuta estos scripts regularmente para mantener tu Mac M1 en óptimas condiciones.