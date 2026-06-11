#!/usr/bin/env python3
"""
Administrador de procesos y memoria para Mac M1
Gestiona procesos, memoria, optimización y limpieza del sistema
"""

import subprocess
import psutil
import json
import time
import argparse
import signal
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple

def get_memory_info():
    """Obtiene información detallada de memoria"""
    memory = psutil.virtual_memory()
    swap = psutil.swap_memory()

    return {
        'total': memory.total,
        'available': memory.available,
        'used': memory.used,
        'free': memory.free,
        'percent': memory.percent,
        'swap_total': swap.total,
        'swap_used': swap.used,
        'swap_free': swap.free,
        'swap_percent': swap.percent
    }

def get_memory_pressure():
    """Obtiene información de presión de memoria específica de macOS"""
    try:
        result = subprocess.run(['memory_pressure'], capture_output=True, text=True)
        return result.stdout.strip()
    except subprocess.SubprocessError:
        return "No disponible"

def get_top_processes_by_cpu(limit: int = 10) -> List[Dict]:
    """Obtiene los procesos que más CPU consumen"""
    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'create_time', 'username']):
        try:
            proc_info = proc.info
            proc_info['age'] = time.time() - proc_info['create_time']
            processes.append(proc_info)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    return sorted(processes, key=lambda p: p['cpu_percent'], reverse=True)[:limit]

def get_top_processes_by_memory(limit: int = 10) -> List[Dict]:
    """Obtiene los procesos que más memoria consumen"""
    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'memory_percent', 'memory_info', 'create_time', 'username']):
        try:
            proc_info = proc.info
            proc_info['memory_mb'] = proc_info['memory_info'].rss / (1024 * 1024)
            proc_info['age'] = time.time() - proc_info['create_time']
            processes.append(proc_info)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    return sorted(processes, key=lambda p: p['memory_percent'], reverse=True)[:limit]

def get_zombie_processes() -> List[Dict]:
    """Encuentra procesos zombie o problemáticos"""
    zombies = []
    for proc in psutil.process_iter(['pid', 'name', 'status', 'cpu_percent', 'memory_percent']):
        try:
            if proc.info['status'] == psutil.STATUS_ZOMBIE:
                zombies.append(proc.info)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return zombies

def get_high_resource_processes(cpu_threshold: float = 80, memory_threshold: float = 10) -> List[Dict]:
    """Encuentra procesos que consumen muchos recursos"""
    high_resource = []
    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'create_time']):
        try:
            proc_info = proc.info
            if (proc_info['cpu_percent'] > cpu_threshold or
                proc_info['memory_percent'] > memory_threshold):
                proc_info['age'] = time.time() - proc_info['create_time']
                high_resource.append(proc_info)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return high_resource

def kill_process_by_name(name: str, force: bool = False) -> Dict:
    """Mata procesos por nombre"""
    killed = []
    errors = []

    for proc in psutil.process_iter(['pid', 'name']):
        try:
            if name.lower() in proc.info['name'].lower():
                pid = proc.info['pid']
                try:
                    if force:
                        os.kill(pid, signal.SIGKILL)
                    else:
                        os.kill(pid, signal.SIGTERM)
                    killed.append({'pid': pid, 'name': proc.info['name']})
                except ProcessLookupError:
                    errors.append(f"Proceso {pid} ya no existe")
                except PermissionError:
                    errors.append(f"Sin permisos para matar proceso {pid}")
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    return {'killed': killed, 'errors': errors}

def kill_process_by_pid(pid: int, force: bool = False) -> Dict:
    """Mata un proceso por PID"""
    try:
        proc = psutil.Process(pid)
        name = proc.name()

        if force:
            os.kill(pid, signal.SIGKILL)
        else:
            os.kill(pid, signal.SIGTERM)

        return {'success': True, 'pid': pid, 'name': name}
    except psutil.NoSuchProcess:
        return {'success': False, 'error': f'Proceso {pid} no encontrado'}
    except PermissionError:
        return {'success': False, 'error': f'Sin permisos para matar proceso {pid}'}
    except Exception as e:
        return {'success': False, 'error': str(e)}

def free_memory():
    """Intenta liberar memoria usando comandos del sistema"""
    commands = [
        (['sudo', 'purge'], "Purgar cachés del sistema"),
        (['sudo', 'sync'], "Sincronizar buffers"),
    ]

    results = []
    for cmd, description in commands:
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            results.append({
                'command': ' '.join(cmd),
                'description': description,
                'success': result.returncode == 0,
                'output': result.stdout if result.returncode == 0 else result.stderr
            })
        except subprocess.TimeoutExpired:
            results.append({
                'command': ' '.join(cmd),
                'description': description,
                'success': False,
                'output': 'Timeout'
            })
        except Exception as e:
            results.append({
                'command': ' '.join(cmd),
                'description': description,
                'success': False,
                'output': str(e)
            })

    return results

def format_bytes(bytes_size: int) -> str:
    """Convierte bytes a formato legible"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.1f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.1f} PB"

def format_age(seconds: float) -> str:
    """Convierte segundos a formato legible de tiempo"""
    if seconds < 60:
        return f"{int(seconds)}s"
    elif seconds < 3600:
        return f"{int(seconds/60)}m"
    elif seconds < 86400:
        return f"{int(seconds/3600)}h"
    else:
        return f"{int(seconds/86400)}d"

def display_system_resources():
    """Muestra el estado actual de recursos del sistema"""
    print("🖥️  ADMINISTRADOR DE PROCESOS MAC M1")
    print("=" * 60)
    print(f"⏰ Análisis: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Información de memoria
    memory_info = get_memory_info()
    print(f"\n💾 MEMORIA:")
    print(f"  Total: {format_bytes(memory_info['total'])}")
    print(f"  Usada: {format_bytes(memory_info['used'])} ({memory_info['percent']:.1f}%)")
    print(f"  Disponible: {format_bytes(memory_info['available'])}")
    print(f"  Swap: {format_bytes(memory_info['swap_used'])}/{format_bytes(memory_info['swap_total'])}")

    # Presión de memoria (macOS específico)
    memory_pressure = get_memory_pressure()
    if "normal" in memory_pressure.lower():
        status_emoji = "✅"
    elif "warn" in memory_pressure.lower():
        status_emoji = "⚠️"
    else:
        status_emoji = "❌"
    print(f"  Presión de memoria: {status_emoji} {memory_pressure}")

    # CPU
    cpu_percent = psutil.cpu_percent(interval=1)
    cpu_count = psutil.cpu_count()
    print(f"\n🔥 CPU:")
    print(f"  Uso actual: {cpu_percent:.1f}%")
    print(f"  Núcleos: {cpu_count}")
    print(f"  Load average: {', '.join(map(str, psutil.getloadavg()))}")

    # Top procesos por CPU
    print(f"\n🚀 TOP PROCESOS (CPU):")
    cpu_processes = get_top_processes_by_cpu(5)
    for i, proc in enumerate(cpu_processes, 1):
        print(f"  {i}. {proc['name']:<20} PID:{proc['pid']:<8} CPU:{proc['cpu_percent']:>5.1f}% MEM:{proc['memory_percent']:>5.1f}% Age:{format_age(proc['age'])}")

    # Top procesos por memoria
    print(f"\n💾 TOP PROCESOS (MEMORIA):")
    memory_processes = get_top_processes_by_memory(5)
    for i, proc in enumerate(memory_processes, 1):
        print(f"  {i}. {proc['name']:<20} PID:{proc['pid']:<8} MEM:{proc['memory_percent']:>5.1f}% ({proc['memory_mb']:.0f}MB)")

    # Procesos problemáticos
    high_resource = get_high_resource_processes()
    if high_resource:
        print(f"\n⚠️  PROCESOS DE ALTO CONSUMO:")
        for proc in high_resource[:3]:
            print(f"  ⚠️  {proc['name']} (PID:{proc['pid']}) - CPU:{proc['cpu_percent']:.1f}% MEM:{proc['memory_percent']:.1f}%")

    # Procesos zombie
    zombies = get_zombie_processes()
    if zombies:
        print(f"\n☠️  PROCESOS ZOMBIE:")
        for zombie in zombies:
            print(f"  ☠️  {zombie['name']} (PID:{zombie['pid']})")

def monitor_resources_continuous(interval: int = 5):
    """Monitor continuo de recursos"""
    try:
        while True:
            print("\033[H\033[J")  # Limpiar pantalla
            display_system_resources()
            print(f"\n⏱️  Actualizando cada {interval}s... (Ctrl+C para salir)")
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\n👋 Monitor de recursos detenido")

def interactive_process_manager():
    """Administrador interactivo de procesos"""
    while True:
        print("\n🔧 ADMINISTRADOR INTERACTIVO DE PROCESOS")
        print("1. Ver procesos por CPU")
        print("2. Ver procesos por memoria")
        print("3. Matar proceso por PID")
        print("4. Matar proceso por nombre")
        print("5. Liberar memoria")
        print("6. Buscar procesos problemáticos")
        print("0. Salir")

        choice = input("\nSelecciona una opción: ").strip()

        if choice == "1":
            processes = get_top_processes_by_cpu(10)
            print("\n🚀 TOP 10 PROCESOS (CPU):")
            for i, proc in enumerate(processes, 1):
                print(f"{i:2d}. {proc['name']:<25} PID:{proc['pid']:<8} CPU:{proc['cpu_percent']:>6.1f}%")

        elif choice == "2":
            processes = get_top_processes_by_memory(10)
            print("\n💾 TOP 10 PROCESOS (MEMORIA):")
            for i, proc in enumerate(processes, 1):
                print(f"{i:2d}. {proc['name']:<25} PID:{proc['pid']:<8} MEM:{proc['memory_mb']:>6.0f}MB")

        elif choice == "3":
            try:
                pid = int(input("Introduce el PID del proceso: "))
                force = input("¿Forzar terminación? (y/N): ").lower() == 'y'
                result = kill_process_by_pid(pid, force)
                if result['success']:
                    print(f"✅ Proceso {result['name']} (PID:{result['pid']}) terminado")
                else:
                    print(f"❌ Error: {result['error']}")
            except ValueError:
                print("❌ PID inválido")

        elif choice == "4":
            name = input("Introduce el nombre del proceso: ")
            force = input("¿Forzar terminación? (y/N): ").lower() == 'y'
            result = kill_process_by_name(name, force)
            if result['killed']:
                for proc in result['killed']:
                    print(f"✅ Proceso {proc['name']} (PID:{proc['pid']}) terminado")
            if result['errors']:
                for error in result['errors']:
                    print(f"❌ {error}")

        elif choice == "5":
            print("🧹 Liberando memoria...")
            results = free_memory()
            for result in results:
                status = "✅" if result['success'] else "❌"
                print(f"{status} {result['description']}")

        elif choice == "6":
            high_resource = get_high_resource_processes(50, 5)  # Umbral más bajo para búsqueda
            if high_resource:
                print("\n⚠️  PROCESOS DE ALTO CONSUMO:")
                for proc in high_resource:
                    print(f"  {proc['name']} (PID:{proc['pid']}) - CPU:{proc['cpu_percent']:.1f}% MEM:{proc['memory_percent']:.1f}%")
            else:
                print("✅ No se encontraron procesos problemáticos")

        elif choice == "0":
            break
        else:
            print("❌ Opción inválida")

def main():
    parser = argparse.ArgumentParser(description='Administrador de procesos para Mac M1')
    parser.add_argument('--monitor', '-m', action='store_true',
                       help='Modo de monitoreo continuo')
    parser.add_argument('--interval', '-i', type=int, default=5,
                       help='Intervalo de monitoreo en segundos (por defecto: 5)')
    parser.add_argument('--interactive', '-I', action='store_true',
                       help='Modo interactivo de administración')
    parser.add_argument('--kill-pid', type=int,
                       help='Matar proceso por PID')
    parser.add_argument('--kill-name', type=str,
                       help='Matar procesos por nombre')
    parser.add_argument('--force', '-f', action='store_true',
                       help='Forzar terminación de procesos')
    parser.add_argument('--free-memory', action='store_true',
                       help='Intentar liberar memoria')
    parser.add_argument('--export', '-e', type=str,
                       help='Exportar información de procesos a archivo JSON')

    args = parser.parse_args()

    if args.interactive:
        interactive_process_manager()
    elif args.kill_pid:
        result = kill_process_by_pid(args.kill_pid, args.force)
        if result['success']:
            print(f"✅ Proceso {result['name']} (PID:{result['pid']}) terminado")
        else:
            print(f"❌ Error: {result['error']}")
    elif args.kill_name:
        result = kill_process_by_name(args.kill_name, args.force)
        if result['killed']:
            for proc in result['killed']:
                print(f"✅ Proceso {proc['name']} (PID:{proc['pid']}) terminado")
        if result['errors']:
            for error in result['errors']:
                print(f"❌ {error}")
    elif args.free_memory:
        print("🧹 Liberando memoria...")
        results = free_memory()
        for result in results:
            status = "✅" if result['success'] else "❌"
            print(f"{status} {result['description']}")
    elif args.monitor:
        monitor_resources_continuous(args.interval)
    else:
        display_system_resources()

        if args.export:
            export_data = {
                'timestamp': datetime.now().isoformat(),
                'memory_info': get_memory_info(),
                'memory_pressure': get_memory_pressure(),
                'top_cpu_processes': get_top_processes_by_cpu(10),
                'top_memory_processes': get_top_processes_by_memory(10),
                'high_resource_processes': get_high_resource_processes(),
                'zombie_processes': get_zombie_processes()
            }

            with open(args.export, 'w') as f:
                json.dump(export_data, f, indent=2, default=str)
            print(f"\n💾 Información de procesos exportada a: {args.export}")

if __name__ == "__main__":
    main()