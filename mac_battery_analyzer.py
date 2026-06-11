#!/usr/bin/env python3
"""
Analizador de batería para Mac M1
Monitorea salud, ciclos, temperatura y optimización energética
"""

import subprocess
import json
import time
import argparse
from datetime import datetime, timedelta
from typing import Dict, List, Optional

def get_battery_info():
    """Obtiene información detallada de la batería"""
    try:
        result = subprocess.run(['system_profiler', 'SPPowerDataType', '-json'],
                              capture_output=True, text=True)
        if result.returncode == 0:
            data = json.loads(result.stdout)
            return data.get('SPPowerDataType', [])
    except (subprocess.SubprocessError, json.JSONDecodeError):
        pass
    return []

def get_pmset_battery_info():
    """Obtiene información de pmset sobre la batería"""
    info = {}
    try:
        # Información general de batería
        result = subprocess.run(['pmset', '-g', 'batt'], capture_output=True, text=True)
        info['battery_status'] = result.stdout

        # Configuración de gestión de energía
        result = subprocess.run(['pmset', '-g'], capture_output=True, text=True)
        info['power_settings'] = result.stdout

        # Estado de carga optimizada
        result = subprocess.run(['pmset', '-g', 'rawbatterystate'], capture_output=True, text=True)
        info['raw_battery_state'] = result.stdout

    except subprocess.SubprocessError:
        pass
    return info

def get_ioreg_battery_info():
    """Obtiene información detallada usando ioreg"""
    try:
        result = subprocess.run(['ioreg', '-rn', 'AppleSmartBattery'],
                              capture_output=True, text=True)
        return result.stdout
    except subprocess.SubprocessError:
        return ""

def parse_battery_health(ioreg_output: str) -> Dict:
    """Extrae información de salud de la batería del output de ioreg"""
    health_info = {}
    lines = ioreg_output.split('\n')

    for line in lines:
        line = line.strip()
        if '"CycleCount" =' in line:
            health_info['cycle_count'] = int(line.split('=')[1].strip())
        elif '"MaxCapacity" =' in line:
            health_info['max_capacity'] = int(line.split('=')[1].strip())
        elif '"CurrentCapacity" =' in line:
            health_info['current_capacity'] = int(line.split('=')[1].strip())
        elif '"DesignCapacity" =' in line:
            health_info['design_capacity'] = int(line.split('=')[1].strip())
        elif '"Temperature" =' in line:
            # La temperatura viene en centésimas de grado Celsius
            temp = int(line.split('=')[1].strip()) / 100.0
            health_info['temperature'] = temp
        elif '"Voltage" =' in line:
            health_info['voltage'] = int(line.split('=')[1].strip()) / 1000.0  # mV a V
        elif '"Amperage" =' in line:
            health_info['amperage'] = int(line.split('=')[1].strip())
        elif '"IsCharging" =' in line:
            health_info['is_charging'] = 'true' in line.lower()

    return health_info

def calculate_battery_health(health_info: Dict) -> Dict:
    """Calcula métricas de salud de la batería"""
    metrics = {}

    if 'max_capacity' in health_info and 'design_capacity' in health_info:
        health_percentage = (health_info['max_capacity'] / health_info['design_capacity']) * 100
        metrics['health_percentage'] = health_percentage

        if health_percentage >= 80:
            metrics['health_status'] = "Excelente"
        elif health_percentage >= 70:
            metrics['health_status'] = "Buena"
        elif health_percentage >= 60:
            metrics['health_status'] = "Aceptable"
        else:
            metrics['health_status'] = "Necesita reemplazo"

    if 'current_capacity' in health_info and 'max_capacity' in health_info:
        charge_percentage = (health_info['current_capacity'] / health_info['max_capacity']) * 100
        metrics['current_charge'] = charge_percentage

    if 'cycle_count' in health_info:
        # Los MacBooks M1 tienen un límite típico de ~1000 ciclos
        cycle_health = max(0, (1000 - health_info['cycle_count']) / 1000 * 100)
        metrics['cycle_health'] = cycle_health

    return metrics

def get_energy_usage_apps():
    """Obtiene aplicaciones que más energía consumen"""
    try:
        result = subprocess.run(['pmset', '-g', 'stats'], capture_output=True, text=True)
        return result.stdout
    except subprocess.SubprocessError:
        return "No disponible"

def estimate_battery_time(health_info: Dict) -> Dict:
    """Estima tiempo de batería restante"""
    estimates = {}

    if 'current_capacity' in health_info and 'amperage' in health_info:
        if health_info['amperage'] != 0:
            # Cálculo básico: capacidad actual / consumo actual
            hours_remaining = abs(health_info['current_capacity'] / (health_info['amperage'] / 1000))
            estimates['hours_remaining'] = hours_remaining
            estimates['time_remaining'] = f"{int(hours_remaining)}h {int((hours_remaining % 1) * 60)}m"

    return estimates

def display_battery_analysis():
    """Muestra análisis completo de la batería"""
    print("🔋 ANALIZADOR DE BATERÍA MAC M1")
    print("=" * 60)
    print(f"⏰ Análisis: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Información del sistema
    battery_data = get_battery_info()
    pmset_info = get_pmset_battery_info()
    ioreg_output = get_ioreg_battery_info()
    health_info = parse_battery_health(ioreg_output)
    metrics = calculate_battery_health(health_info)
    time_estimates = estimate_battery_time(health_info)

    # Estado actual
    print(f"\n📊 ESTADO ACTUAL:")
    if 'current_charge' in metrics:
        print(f"  Carga actual: {metrics['current_charge']:.1f}%")
    if 'temperature' in health_info:
        print(f"  Temperatura: {health_info['temperature']:.1f}°C")
    if 'voltage' in health_info:
        print(f"  Voltaje: {health_info['voltage']:.2f}V")
    if 'is_charging' in health_info:
        status = "Cargando" if health_info['is_charging'] else "Descargando"
        print(f"  Estado: {status}")

    # Salud de la batería
    print(f"\n💚 SALUD DE LA BATERÍA:")
    if 'health_percentage' in metrics:
        print(f"  Salud general: {metrics['health_percentage']:.1f}% - {metrics.get('health_status', 'N/A')}")
    if 'cycle_count' in health_info:
        print(f"  Ciclos de carga: {health_info['cycle_count']}")
        remaining_cycles = max(0, 1000 - health_info['cycle_count'])
        print(f"  Ciclos restantes (aprox): {remaining_cycles}")

    # Capacidad
    if 'max_capacity' in health_info and 'design_capacity' in health_info:
        print(f"  Capacidad máxima: {health_info['max_capacity']} mAh")
        print(f"  Capacidad de diseño: {health_info['design_capacity']} mAh")
        capacity_loss = health_info['design_capacity'] - health_info['max_capacity']
        print(f"  Pérdida de capacidad: {capacity_loss} mAh")

    # Estimaciones de tiempo
    if time_estimates:
        print(f"\n⏱️  ESTIMACIONES DE TIEMPO:")
        if 'time_remaining' in time_estimates:
            print(f"  Tiempo restante estimado: {time_estimates['time_remaining']}")

    # Configuración de energía actual
    if 'power_settings' in pmset_info:
        print(f"\n⚙️  CONFIGURACIÓN DE ENERGÍA:")
        lines = pmset_info['power_settings'].split('\n')[:10]  # Primeras 10 líneas
        for line in lines:
            if line.strip() and not line.startswith('System-wide'):
                print(f"  {line.strip()}")

    # Recomendaciones
    print(f"\n💡 RECOMENDACIONES:")

    if 'health_percentage' in metrics:
        if metrics['health_percentage'] < 80:
            print("  ⚠️  Considera calibrar la batería o contactar soporte técnico")
        else:
            print("  ✅ La batería está en buen estado")

    if 'cycle_count' in health_info:
        if health_info['cycle_count'] > 800:
            print("  ⚠️  Alto número de ciclos, monitorea el rendimiento")
        elif health_info['cycle_count'] > 500:
            print("  ℹ️  Ciclos moderados, mantén buenas prácticas de carga")
        else:
            print("  ✅ Ciclos de batería en rango óptimo")

    if 'temperature' in health_info:
        if health_info['temperature'] > 35:
            print("  🌡️  Temperatura alta, verifica ventilación")
        else:
            print("  ✅ Temperatura normal")

def log_battery_data(filename: str):
    """Registra datos de batería en un archivo"""
    ioreg_output = get_ioreg_battery_info()
    health_info = parse_battery_health(ioreg_output)
    metrics = calculate_battery_health(health_info)

    log_entry = {
        'timestamp': datetime.now().isoformat(),
        'health_info': health_info,
        'metrics': metrics
    }

    try:
        with open(filename, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
        print(f"✅ Datos registrados en {filename}")
    except IOError as e:
        print(f"❌ Error escribiendo archivo: {e}")

def monitor_battery(interval: int = 60, log_file: Optional[str] = None):
    """Monitor continuo de la batería"""
    try:
        while True:
            print("\033[H\033[J")  # Limpiar pantalla
            display_battery_analysis()

            if log_file:
                log_battery_data(log_file)

            print(f"\n⏱️  Actualizando cada {interval}s... (Ctrl+C para salir)")
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\n👋 Monitor de batería detenido")

def main():
    parser = argparse.ArgumentParser(description='Analizador de batería para Mac M1')
    parser.add_argument('--monitor', '-m', action='store_true',
                       help='Modo de monitoreo continuo')
    parser.add_argument('--interval', '-i', type=int, default=60,
                       help='Intervalo de monitoreo en segundos (por defecto: 60)')
    parser.add_argument('--log', '-l', type=str,
                       help='Archivo para registrar datos históricos')
    parser.add_argument('--export', '-e', type=str,
                       help='Exportar análisis actual a archivo JSON')

    args = parser.parse_args()

    if args.monitor:
        monitor_battery(args.interval, args.log)
    else:
        display_battery_analysis()

        if args.log:
            log_battery_data(args.log)

        if args.export:
            ioreg_output = get_ioreg_battery_info()
            health_info = parse_battery_health(ioreg_output)
            metrics = calculate_battery_health(health_info)

            export_data = {
                'timestamp': datetime.now().isoformat(),
                'health_info': health_info,
                'metrics': metrics,
                'pmset_info': get_pmset_battery_info()
            }

            with open(args.export, 'w') as f:
                json.dump(export_data, f, indent=2, default=str)
            print(f"\n💾 Análisis exportado a: {args.export}")

if __name__ == "__main__":
    main()