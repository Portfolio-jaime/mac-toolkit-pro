#!/usr/bin/env python3
"""
Monitor de red para Mac M1
Analiza conexiones, velocidad, calidad y problemas de conectividad
"""

import subprocess
import json
import time
import psutil
import argparse
import socket
import requests
from datetime import datetime
from typing import Dict, List, Optional, Tuple

def get_network_interfaces():
    """Obtiene información de interfaces de red"""
    interfaces = {}
    try:
        result = subprocess.run(['ifconfig'], capture_output=True, text=True)
        current_interface = None

        for line in result.stdout.split('\n'):
            if line and not line.startswith('\t') and ':' in line:
                current_interface = line.split(':')[0]
                interfaces[current_interface] = {'raw': line}
            elif current_interface and line.strip():
                if 'raw' not in interfaces[current_interface]:
                    interfaces[current_interface]['raw'] = ''
                interfaces[current_interface]['raw'] += '\n' + line

    except subprocess.SubprocessError:
        pass

    return interfaces

def get_wifi_info():
    """Obtiene información detallada de WiFi"""
    wifi_info = {}
    try:
        # Información básica de WiFi
        result = subprocess.run(['/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport', '-I'],
                              capture_output=True, text=True)
        if result.returncode == 0:
            for line in result.stdout.split('\n'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    wifi_info[key.strip()] = value.strip()

        # Escaneo de redes disponibles
        result = subprocess.run(['/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport', '-s'],
                              capture_output=True, text=True)
        if result.returncode == 0:
            wifi_info['available_networks'] = result.stdout

    except subprocess.SubprocessError:
        pass

    return wifi_info

def test_connectivity() -> Dict:
    """Prueba la conectividad a varios servicios"""
    tests = {
        'google_dns': '8.8.8.8',
        'cloudflare_dns': '1.1.1.1',
        'google_web': 'www.google.com',
        'apple': 'www.apple.com'
    }

    results = {}

    for name, target in tests.items():
        try:
            if target.replace('.', '').isdigit() or ':' in target:  # IP address
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(3)
                result = sock.connect_ex((target, 53))  # DNS port
                sock.close()
                results[name] = 'OK' if result == 0 else 'FAIL'
            else:  # Domain name
                start_time = time.time()
                response = requests.get(f'https://{target}', timeout=5)
                end_time = time.time()
                results[name] = {
                    'status': 'OK' if response.status_code == 200 else f'HTTP {response.status_code}',
                    'response_time': round((end_time - start_time) * 1000, 2)  # ms
                }
        except Exception as e:
            results[name] = f'ERROR: {str(e)[:50]}'

    return results

def get_network_statistics():
    """Obtiene estadísticas de red usando psutil"""
    stats = psutil.net_io_counters(pernic=True)
    return stats

def test_speed(test_url: str = "http://speedtest.selectel.ru/1MB") -> Dict:
    """Prueba básica de velocidad de descarga"""
    try:
        start_time = time.time()
        response = requests.get(test_url, timeout=30, stream=True)

        total_size = 0
        for chunk in response.iter_content(chunk_size=1024):
            total_size += len(chunk)

        end_time = time.time()
        duration = end_time - start_time

        speed_mbps = (total_size * 8) / (duration * 1000000)  # Convert to Mbps

        return {
            'duration': round(duration, 2),
            'size_mb': round(total_size / (1024 * 1024), 2),
            'speed_mbps': round(speed_mbps, 2)
        }
    except Exception as e:
        return {'error': str(e)}

def get_dns_info():
    """Obtiene información de configuración DNS"""
    dns_info = {}
    try:
        result = subprocess.run(['scutil', '--dns'], capture_output=True, text=True)
        dns_info['dns_config'] = result.stdout

        # Prueba de resolución DNS
        start_time = time.time()
        socket.gethostbyname('www.google.com')
        dns_time = (time.time() - start_time) * 1000
        dns_info['dns_resolution_time'] = round(dns_time, 2)

    except Exception as e:
        dns_info['error'] = str(e)

    return dns_info

def get_active_connections():
    """Obtiene conexiones de red activas"""
    connections = []
    try:
        for conn in psutil.net_connections():
            if conn.status == psutil.CONN_ESTABLISHED:
                try:
                    process = psutil.Process(conn.pid) if conn.pid else None
                    connections.append({
                        'local_addr': f"{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr else 'N/A',
                        'remote_addr': f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else 'N/A',
                        'status': conn.status,
                        'pid': conn.pid,
                        'process': process.name() if process else 'Unknown'
                    })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
    except psutil.AccessDenied:
        connections.append({'error': 'Acceso denegado - ejecuta como administrador para ver todas las conexiones'})

    return connections

def format_bytes(bytes_size: int) -> str:
    """Convierte bytes a formato legible"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.1f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.1f} PB"

def display_network_status():
    """Muestra el estado completo de la red"""
    print("🌐 MONITOR DE RED MAC M1")
    print("=" * 60)
    print(f"⏰ Análisis: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Interfaces de red
    interfaces = get_network_interfaces()
    print(f"\n🔌 INTERFACES DE RED:")
    for name, info in interfaces.items():
        if name.startswith('en') or name.startswith('wi'):  # Ethernet y WiFi
            print(f"  {name}: Activa")

    # Información WiFi
    wifi_info = get_wifi_info()
    if wifi_info:
        print(f"\n📶 INFORMACIÓN WIFI:")
        ssid = wifi_info.get('SSID', 'No conectado')
        print(f"  Red actual: {ssid}")

        if 'RSSI' in wifi_info:
            rssi = int(wifi_info['RSSI'])
            signal_quality = "Excelente" if rssi > -30 else "Buena" if rssi > -67 else "Débil"
            print(f"  Señal: {rssi} dBm ({signal_quality})")

        if 'channel' in wifi_info:
            print(f"  Canal: {wifi_info['channel']}")

        if 'CC' in wifi_info:
            print(f"  País: {wifi_info['CC']}")

    # Estadísticas de red
    net_stats = get_network_statistics()
    print(f"\n📊 ESTADÍSTICAS DE RED:")
    for interface, stats in net_stats.items():
        if interface.startswith('en') or interface.startswith('wi'):
            print(f"  {interface}:")
            print(f"    Enviado: {format_bytes(stats.bytes_sent)}")
            print(f"    Recibido: {format_bytes(stats.bytes_recv)}")
            print(f"    Paquetes enviados: {stats.packets_sent}")
            print(f"    Paquetes recibidos: {stats.packets_recv}")

    # Pruebas de conectividad
    print(f"\n🔍 PRUEBAS DE CONECTIVIDAD:")
    connectivity_results = test_connectivity()
    for test_name, result in connectivity_results.items():
        if isinstance(result, dict) and 'response_time' in result:
            print(f"  {test_name}: {result['status']} ({result['response_time']} ms)")
        else:
            status_emoji = "✅" if result == "OK" else "❌"
            print(f"  {status_emoji} {test_name}: {result}")

    # DNS
    dns_info = get_dns_info()
    if 'dns_resolution_time' in dns_info:
        print(f"\n🔍 DNS:")
        print(f"  Tiempo de resolución: {dns_info['dns_resolution_time']} ms")

    # Conexiones activas (top 5)
    connections = get_active_connections()
    print(f"\n🔗 CONEXIONES ACTIVAS (Top 5):")
    if connections and 'error' not in connections[0]:
        for i, conn in enumerate(connections[:5]):
            print(f"  {i+1}. {conn['process']} -> {conn['remote_addr']}")
    elif connections and 'error' in connections[0]:
        print(f"  {connections[0]['error']}")

def monitor_network_continuous(interval: int = 30):
    """Monitor continuo de red"""
    try:
        while True:
            print("\033[H\033[J")  # Limpiar pantalla
            display_network_status()
            print(f"\n⏱️  Actualizando cada {interval}s... (Ctrl+C para salir)")
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\n👋 Monitor de red detenido")

def run_speed_test():
    """Ejecuta una prueba de velocidad"""
    print("🚀 EJECUTANDO PRUEBA DE VELOCIDAD...")
    print("(Esto puede tomar unos segundos)")

    speed_result = test_speed()

    if 'error' in speed_result:
        print(f"❌ Error en prueba de velocidad: {speed_result['error']}")
    else:
        print(f"✅ Prueba completada:")
        print(f"   Tamaño descargado: {speed_result['size_mb']} MB")
        print(f"   Tiempo: {speed_result['duration']} segundos")
        print(f"   Velocidad: {speed_result['speed_mbps']} Mbps")

def diagnose_network_issues():
    """Diagnostica problemas comunes de red"""
    print("🔧 DIAGNÓSTICO DE RED:")
    issues = []

    # Verificar conectividad básica
    connectivity = test_connectivity()
    dns_fails = sum(1 for result in connectivity.values() if 'FAIL' in str(result) or 'ERROR' in str(result))

    if dns_fails > 2:
        issues.append("❌ Múltiples fallos de conectividad detectados")

    # Verificar WiFi
    wifi_info = get_wifi_info()
    if 'RSSI' in wifi_info:
        rssi = int(wifi_info['RSSI'])
        if rssi < -70:
            issues.append("⚠️  Señal WiFi débil (< -70 dBm)")

    # Verificar DNS
    dns_info = get_dns_info()
    if 'dns_resolution_time' in dns_info and dns_info['dns_resolution_time'] > 100:
        issues.append("⚠️  Resolución DNS lenta (> 100ms)")

    if not issues:
        print("✅ No se detectaron problemas obvios")
    else:
        for issue in issues:
            print(f"  {issue}")

def main():
    parser = argparse.ArgumentParser(description='Monitor de red para Mac M1')
    parser.add_argument('--monitor', '-m', action='store_true',
                       help='Modo de monitoreo continuo')
    parser.add_argument('--interval', '-i', type=int, default=30,
                       help='Intervalo de monitoreo en segundos (por defecto: 30)')
    parser.add_argument('--speed-test', '-s', action='store_true',
                       help='Ejecutar prueba de velocidad')
    parser.add_argument('--diagnose', '-d', action='store_true',
                       help='Ejecutar diagnóstico de problemas')
    parser.add_argument('--export', '-e', type=str,
                       help='Exportar información de red a archivo JSON')

    args = parser.parse_args()

    if args.speed_test:
        run_speed_test()
    elif args.diagnose:
        diagnose_network_issues()
    elif args.monitor:
        monitor_network_continuous(args.interval)
    else:
        display_network_status()

        if args.export:
            export_data = {
                'timestamp': datetime.now().isoformat(),
                'interfaces': get_network_interfaces(),
                'wifi_info': get_wifi_info(),
                'network_stats': dict(get_network_statistics()),
                'connectivity_tests': test_connectivity(),
                'dns_info': get_dns_info(),
                'active_connections': get_active_connections()
            }

            with open(args.export, 'w') as f:
                json.dump(export_data, f, indent=2, default=str)
            print(f"\n💾 Información de red exportada a: {args.export}")

if __name__ == "__main__":
    main()