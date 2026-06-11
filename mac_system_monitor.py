#!/usr/bin/env python3
"""
Monitor de sistema para Mac M1
Monitorea CPU, memoria, temperatura y rendimiento en tiempo real
"""

import subprocess
import json
import time
import psutil
import argparse
from datetime import datetime
from typing import Dict, Optional

def get_cpu_info():
    """Obtiene información del procesador M1"""
    try:
        result = subprocess.run(['system_profiler', 'SPHardwareDataType', '-json'],
                              capture_output=True, text=True)
        if result.returncode == 0:
            data = json.loads(result.stdout)
            hardware = data.get('SPHardwareDataType', [{}])[0]
            return {
                'model': hardware.get('machine_name', 'Unknown'),
                'chip': hardware.get('chip_type', 'Unknown'),
                'cores': hardware.get('number_processors', 'Unknown'),
                'memory': hardware.get('physical_memory', 'Unknown')
            }
    except (subprocess.SubprocessError, json.JSONDecodeError):
        pass
    return {}

def get_thermal_state():
    """Obtiene el estado térmico del sistema"""
    try:
        result = subprocess.run(['pmset', '-g', 'therm'], capture_output=True, text=True)
        return result.stdout.strip()
    except subprocess.SubprocessError:
        return "No disponible"

def get_power_metrics():
    """Obtiene métricas de energía"""
    try:
        result = subprocess.run(['pmset', '-g', 'batt'], capture_output=True, text=True)
        power_info = result.stdout

        result = subprocess.run(['pmset', '-g', 'ps'], capture_output=True, text=True)
        power_source = result.stdout

        return {
            'battery': power_info,
            'power_source': power_source
        }
    except subprocess.SubprocessError:
        return {}

def get_m1_specific_stats():
    """Obtiene estadísticas específicas del M1"""
    stats = {}

    # Frecuencia de CPU (aproximada usando powermetrics si está disponible)
    try:
        result = subprocess.run(['sudo', 'powermetrics', '--samplers', 'cpu_power',
                               '--sample-count', '1', '--show-usage-summary'],
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            stats['powermetrics'] = result.stdout
    except (subprocess.SubprocessError, subprocess.TimeoutExpired):
        pass

    return stats

def format_bytes(bytes_size: int) -> str:
    """Convierte bytes a formato legible"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.1f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.1f} PB"

def display_system_status():
    """Muestra el estado actual del sistema"""
    print("🖥️  MONITOR DE SISTEMA MAC M1")
    print("=" * 60)
    print(f"⏰ Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Información del hardware
    cpu_info = get_cpu_info()
    if cpu_info:
        print(f"\n💻 HARDWARE:")
        print(f"  Modelo: {cpu_info.get('model', 'N/A')}")
        print(f"  Chip: {cpu_info.get('chip', 'N/A')}")
        print(f"  Cores: {cpu_info.get('cores', 'N/A')}")
        print(f"  Memoria: {cpu_info.get('memory', 'N/A')}")

    # CPU y Memoria
    cpu_percent = psutil.cpu_percent(interval=1)
    cpu_freq = psutil.cpu_freq()
    memory = psutil.virtual_memory()

    print(f"\n📊 RENDIMIENTO:")
    print(f"  CPU: {cpu_percent:.1f}%")
    if cpu_freq:
        print(f"  Frecuencia CPU: {cpu_freq.current:.0f} MHz")
    print(f"  Memoria: {memory.percent:.1f}% ({format_bytes(memory.used)}/{format_bytes(memory.total)})")
    print(f"  Swap: {format_bytes(psutil.swap_memory().used)}")

    # Procesos top
    processes = sorted(psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']),
                      key=lambda p: p.info['cpu_percent'], reverse=True)[:5]

    print(f"\n🔥 TOP 5 PROCESOS (CPU):")
    for proc in processes:
        try:
            print(f"  {proc.info['name']:<20} CPU: {proc.info['cpu_percent']:>5.1f}% MEM: {proc.info['memory_percent']:>5.1f}%")
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    # Estado térmico
    thermal = get_thermal_state()
    print(f"\n🌡️  ESTADO TÉRMICO:")
    print(f"  {thermal}")

    # Información de energía
    power_info = get_power_metrics()
    if power_info:
        print(f"\n🔋 ENERGÍA:")
        if 'battery' in power_info:
            lines = power_info['battery'].split('\n')
            for line in lines:
                if 'InternalBattery' in line or '%' in line:
                    print(f"  {line.strip()}")

def monitor_continuous(interval: int = 5):
    """Monitor continuo del sistema"""
    try:
        while True:
            print("\033[H\033[J")  # Limpiar pantalla
            display_system_status()
            print(f"\n⏱️  Actualizando cada {interval}s... (Ctrl+C para salir)")
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\n👋 Monitor detenido")

def main():
    parser = argparse.ArgumentParser(description='Monitor de sistema para Mac M1')
    parser.add_argument('--continuous', '-c', action='store_true',
                       help='Modo de monitoreo continuo')
    parser.add_argument('--interval', '-i', type=int, default=5,
                       help='Intervalo de actualización en segundos (por defecto: 5)')
    parser.add_argument('--export', '-e', type=str,
                       help='Exportar datos a archivo JSON')

    args = parser.parse_args()

    if args.continuous:
        monitor_continuous(args.interval)
    else:
        display_system_status()

        if args.export:
            # Exportar datos a JSON
            data = {
                'timestamp': datetime.now().isoformat(),
                'cpu_info': get_cpu_info(),
                'cpu_percent': psutil.cpu_percent(),
                'memory': dict(psutil.virtual_memory()._asdict()),
                'thermal_state': get_thermal_state(),
                'power_info': get_power_metrics()
            }

            with open(args.export, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            print(f"\n💾 Datos exportados a: {args.export}")

if __name__ == "__main__":
    main()