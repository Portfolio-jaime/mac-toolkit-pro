#!/usr/bin/env python3
"""
Mac M1 Toolkit - Centro de Control
Script principal que organiza y ejecuta todas las utilidades de mantenimiento Mac M1
"""

import os
import sys
import subprocess
import time
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

class MacToolkit:
    def __init__(self):
        self.script_dir = Path(__file__).parent
        self.scripts = {
            'storage': 'mac_storage_analyzer.py',
            'system': 'mac_system_monitor.py',
            'battery': 'mac_battery_analyzer.py',
            'network': 'mac_network_monitor.py',
            'process': 'mac_process_manager.py',
            'cleaner': 'mac_maintenance_cleaner.py',
            'detective': 'mac_storage_detective.py',
            'smart': 'mac_smart_cleaner.py'
        }
        self.reports_dir = self.script_dir / 'reports'
        self.reports_dir.mkdir(exist_ok=True)

    def clear_screen(self):
        """Limpia la pantalla"""
        os.system('clear')

    def print_header(self):
        """Imprime el header del toolkit"""
        print("🍎" + "=" * 58 + "🍎")
        print("           MAC M1 TOOLKIT - CENTRO DE CONTROL")
        print("             Utilidades de Mantenimiento y Monitoreo")
        print("🍎" + "=" * 58 + "🍎")
        print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()

    def check_dependencies(self) -> List[str]:
        """Verifica dependencias y scripts disponibles"""
        missing = []

        # Verificar scripts
        for name, script in self.scripts.items():
            script_path = self.script_dir / script
            if not script_path.exists():
                missing.append(f"Script faltante: {script}")
            elif not os.access(script_path, os.X_OK):
                missing.append(f"Script sin permisos de ejecución: {script}")

        # Verificar dependencias Python
        try:
            import psutil
            import requests
        except ImportError as e:
            missing.append(f"Dependencia Python faltante: {e}")

        return missing

    def run_script(self, script_name: str, args: List[str] = None, background: bool = False) -> Optional[subprocess.Popen]:
        """Ejecuta un script específico"""
        if script_name not in self.scripts:
            print(f"❌ Script '{script_name}' no encontrado")
            return None

        script_path = self.script_dir / self.scripts[script_name]
        cmd = ['python3', str(script_path)]

        if args:
            cmd.extend(args)

        try:
            if background:
                process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                return process
            else:
                result = subprocess.run(cmd, check=True)
                return result
        except subprocess.CalledProcessError as e:
            print(f"❌ Error ejecutando {script_name}: {e}")
            return None
        except FileNotFoundError:
            print(f"❌ Python3 no encontrado o script no ejecutable")
            return None

    def quick_system_overview(self):
        """Ejecuta un análisis rápido del sistema"""
        self.clear_screen()
        self.print_header()
        print("🔍 ANÁLISIS RÁPIDO DEL SISTEMA")
        print("=" * 60)
        print()

        # Almacenamiento rápido
        print("💾 Analizando almacenamiento...")
        self.run_script('storage', ['-t', '5'])

        print("\n" + "─" * 60)

        # Estado del sistema
        print("🖥️  Estado del sistema...")
        self.run_script('system')

        print("\n" + "─" * 60)

        # Estado de la batería
        print("🔋 Estado de la batería...")
        self.run_script('battery')

        input("\n⏸️  Presiona Enter para continuar...")

    def comprehensive_analysis(self):
        """Ejecuta un análisis completo y genera reportes"""
        self.clear_screen()
        self.print_header()
        print("📊 ANÁLISIS COMPLETO DEL SISTEMA")
        print("=" * 60)
        print("Generando reportes detallados...")
        print()

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # Crear directorio para este análisis
        analysis_dir = self.reports_dir / f"analysis_{timestamp}"
        analysis_dir.mkdir(exist_ok=True)

        reports = []

        # Análisis de almacenamiento
        print("💾 1/6 Analizando almacenamiento...")
        storage_report = analysis_dir / "storage_analysis.json"
        self.run_script('storage', ['-e', str(storage_report)])
        reports.append(('Almacenamiento', storage_report))

        # Monitor del sistema
        print("🖥️  2/6 Analizando sistema...")
        system_report = analysis_dir / "system_analysis.json"
        self.run_script('system', ['-e', str(system_report)])
        reports.append(('Sistema', system_report))

        # Análisis de batería
        print("🔋 3/6 Analizando batería...")
        battery_report = analysis_dir / "battery_analysis.json"
        self.run_script('battery', ['-e', str(battery_report)])
        reports.append(('Batería', battery_report))

        # Análisis de red
        print("🌐 4/6 Analizando red...")
        network_report = analysis_dir / "network_analysis.json"
        self.run_script('network', ['-e', str(network_report)])
        reports.append(('Red', network_report))

        # Análisis de procesos
        print("⚙️  5/6 Analizando procesos...")
        process_report = analysis_dir / "process_analysis.json"
        self.run_script('process', ['-e', str(process_report)])
        reports.append(('Procesos', process_report))

        # Análisis de limpieza (simulación)
        print("🧹 6/6 Simulando limpieza...")
        cleanup_report = analysis_dir / "cleanup_simulation.txt"
        self.run_script('cleaner', ['--dry-run', '--all', '-r', str(cleanup_report)])
        reports.append(('Limpieza', cleanup_report))

        # Generar reporte consolidado
        self.generate_consolidated_report(analysis_dir, reports)

        print(f"\n✅ Análisis completo guardado en: {analysis_dir}")
        print(f"📋 Ver reporte consolidado: {analysis_dir / 'consolidated_report.md'}")

        input("\n⏸️  Presiona Enter para continuar...")

    def generate_consolidated_report(self, analysis_dir: Path, reports: List[tuple]):
        """Genera un reporte consolidado en Markdown"""
        consolidated_file = analysis_dir / "consolidated_report.md"

        with open(consolidated_file, 'w') as f:
            f.write(f"# 📊 Reporte Consolidado Mac M1\n\n")
            f.write(f"**Fecha:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"**Directorio:** `{analysis_dir}`\n\n")

            f.write("## 📋 Resumen de Análisis\n\n")

            for name, report_path in reports:
                f.write(f"### {name}\n")
                f.write(f"- **Archivo:** `{report_path.name}`\n")
                f.write(f"- **Estado:** {'✅ Completado' if report_path.exists() else '❌ Error'}\n")
                if report_path.exists():
                    size = report_path.stat().st_size
                    f.write(f"- **Tamaño:** {size} bytes\n")
                f.write("\n")

            f.write("## 🚀 Próximos Pasos Recomendados\n\n")
            f.write("1. **Revisar almacenamiento:** Verificar archivos grandes identificados\n")
            f.write("2. **Monitorear batería:** Revisar ciclos y salud\n")
            f.write("3. **Optimizar procesos:** Eliminar procesos innecesarios\n")
            f.write("4. **Ejecutar limpieza:** Usar modo real si la simulación es satisfactoria\n")
            f.write("5. **Programar mantenimiento:** Ejecutar análisis semanalmente\n\n")

            f.write("## 📁 Archivos Generados\n\n")
            for name, report_path in reports:
                if report_path.exists():
                    f.write(f"- `{report_path.name}` - {name}\n")

    def system_maintenance_menu(self):
        """Menú de mantenimiento del sistema"""
        while True:
            self.clear_screen()
            self.print_header()
            print("🔧 MANTENIMIENTO DEL SISTEMA")
            print("=" * 60)
            print()
            print("1. 🧹 Simulación de limpieza (seguro)")
            print("2. 🗑️  Limpieza básica (cachés y logs)")
            print("3. 🚨 Limpieza completa (PRECAUCIÓN)")
            print("4. ⚙️  Optimización del sistema")
            print("5. 🔍 Buscar archivos grandes")
            print("6. 📊 Generar reporte de limpieza")
            print("0. ⬅️  Volver al menú principal")
            print()

            choice = input("Selecciona una opción: ").strip()

            if choice == "1":
                self.clear_screen()
                print("🔍 SIMULACIÓN DE LIMPIEZA")
                print("=" * 40)
                self.run_script('cleaner', ['--dry-run', '--all'])
                input("\n⏸️  Presiona Enter para continuar...")

            elif choice == "2":
                self.clear_screen()
                print("🧹 LIMPIEZA BÁSICA")
                print("=" * 40)
                confirm = input("¿Confirmar limpieza básica? (y/N): ")
                if confirm.lower() == 'y':
                    self.run_script('cleaner', ['-c', '-l'])
                input("\n⏸️  Presiona Enter para continuar...")

            elif choice == "3":
                self.clear_screen()
                print("🚨 LIMPIEZA COMPLETA")
                print("=" * 40)
                print("⚠️  ADVERTENCIA: Esto eliminará cachés, logs, duplicados y más")
                confirm = input("¿Estás SEGURO? Escribe 'CONFIRMAR': ")
                if confirm == 'CONFIRMAR':
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    report_file = self.reports_dir / f"cleanup_{timestamp}.txt"
                    self.run_script('cleaner', ['--all', '-r', str(report_file)])
                input("\n⏸️  Presiona Enter para continuar...")

            elif choice == "4":
                self.clear_screen()
                print("⚙️  OPTIMIZACIÓN DEL SISTEMA")
                print("=" * 40)
                self.run_script('cleaner', ['-o'])
                input("\n⏸️  Presiona Enter para continuar...")

            elif choice == "5":
                self.clear_screen()
                print("🔍 BÚSQUEDA DE ARCHIVOS GRANDES")
                print("=" * 40)
                size = input("Tamaño mínimo en MB (por defecto 500): ").strip()
                if not size:
                    size = "500"
                try:
                    self.run_script('cleaner', ['-f', size])
                except ValueError:
                    print("❌ Tamaño inválido")
                input("\n⏸️  Presiona Enter para continuar...")

            elif choice == "6":
                self.clear_screen()
                print("📊 REPORTE DE LIMPIEZA")
                print("=" * 40)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                report_file = self.reports_dir / f"cleanup_report_{timestamp}.txt"
                self.run_script('cleaner', ['--dry-run', '--all', '-r', str(report_file)])
                print(f"\n📋 Reporte guardado en: {report_file}")
                input("\n⏸️  Presiona Enter para continuar...")

            elif choice == "0":
                break
            else:
                print("❌ Opción inválida")
                time.sleep(1)

    def monitoring_menu(self):
        """Menú de monitoreo en tiempo real"""
        while True:
            self.clear_screen()
            self.print_header()
            print("📊 MONITOREO EN TIEMPO REAL")
            print("=" * 60)
            print()
            print("1. 🖥️  Monitor del sistema")
            print("2. 🔋 Monitor de batería")
            print("3. 🌐 Monitor de red")
            print("4. ⚙️  Monitor de procesos")
            print("5. 📈 Monitor múltiple (nueva ventana)")
            print("6. 🎯 Monitor personalizado")
            print("0. ⬅️  Volver al menú principal")
            print()

            choice = input("Selecciona una opción: ").strip()

            if choice == "1":
                self.clear_screen()
                print("🖥️  MONITOR DEL SISTEMA")
                print("Presiona Ctrl+C para salir")
                print("=" * 40)
                self.run_script('system', ['-c'])

            elif choice == "2":
                self.clear_screen()
                print("🔋 MONITOR DE BATERÍA")
                print("Presiona Ctrl+C para salir")
                print("=" * 40)
                self.run_script('battery', ['-m'])

            elif choice == "3":
                self.clear_screen()
                print("🌐 MONITOR DE RED")
                print("Presiona Ctrl+C para salir")
                print("=" * 40)
                self.run_script('network', ['-m'])

            elif choice == "4":
                self.clear_screen()
                print("⚙️  MONITOR DE PROCESOS")
                print("Presiona Ctrl+C para salir")
                print("=" * 40)
                self.run_script('process', ['-m'])

            elif choice == "5":
                self.clear_screen()
                print("📈 INICIANDO MONITORS MÚLTIPLES")
                print("=" * 40)
                print("Se abrirán nuevas ventanas de terminal...")

                # Abrir monitores en nuevas ventanas
                try:
                    system_cmd = f"osascript -e 'tell app \"Terminal\" to do script \"cd {self.script_dir} && python3 {self.scripts['system']} -c\"'"
                    battery_cmd = f"osascript -e 'tell app \"Terminal\" to do script \"cd {self.script_dir} && python3 {self.scripts['battery']} -m\"'"
                    network_cmd = f"osascript -e 'tell app \"Terminal\" to do script \"cd {self.script_dir} && python3 {self.scripts['network']} -m\"'"

                    os.system(system_cmd)
                    time.sleep(1)
                    os.system(battery_cmd)
                    time.sleep(1)
                    os.system(network_cmd)

                    print("✅ Monitores iniciados en nuevas ventanas")
                except Exception as e:
                    print(f"❌ Error abriendo ventanas: {e}")

                input("\n⏸️  Presiona Enter para continuar...")

            elif choice == "6":
                self.clear_screen()
                print("🎯 MONITOR PERSONALIZADO")
                print("=" * 40)
                print("Selecciona qué monitorear:")
                print("1. Solo CPU y memoria")
                print("2. Solo red")
                print("3. Solo batería")
                print("4. Procesos específicos")

                sub_choice = input("Opción: ").strip()

                if sub_choice == "1":
                    self.run_script('system', ['-c', '-i', '3'])
                elif sub_choice == "2":
                    self.run_script('network', ['-m', '-i', '10'])
                elif sub_choice == "3":
                    self.run_script('battery', ['-m', '-i', '30'])
                elif sub_choice == "4":
                    self.run_script('process', ['-I'])

            elif choice == "0":
                break
            else:
                print("❌ Opción inválida")
                time.sleep(1)

    def tools_menu(self):
        """Menú de herramientas específicas"""
        while True:
            self.clear_screen()
            self.print_header()
            print("🛠️  HERRAMIENTAS ESPECÍFICAS")
            print("=" * 60)
            print()
            print("1. 🔍 Análisis detallado de almacenamiento")
            print("2. 🌡️  Prueba de velocidad de red")
            print("3. 🔋 Calibración de batería")
            print("4. 💀 Administrador de procesos interactivo")
            print("5. 🐳 Comandos específicos para Docker")
            print("6. 📋 Información del sistema M1")
            print("7. 🗂️  Explorador de reportes")
            print("0. ⬅️  Volver al menú principal")
            print()

            choice = input("Selecciona una opción: ").strip()

            if choice == "1":
                self.clear_screen()
                print("🔍 ANÁLISIS DETALLADO DE ALMACENAMIENTO")
                print("=" * 50)
                print("1. Análisis estándar de directorio")
                print("2. 🕵️ Storage Detective (análisis interactivo)")
                print()
                sub_choice = input("Selecciona opción: ").strip()

                if sub_choice == "1":
                    directory = input("Directorio a analizar (Enter para home): ").strip()
                    args = ['-t', '20'] if not directory else ['-d', directory, '-t', '20']
                    self.run_script('storage', args)
                elif sub_choice == "2":
                    self.run_script('detective')

                input("\n⏸️  Presiona Enter para continuar...")

            elif choice == "2":
                self.clear_screen()
                print("🌡️  PRUEBA DE VELOCIDAD DE RED")
                print("=" * 40)
                self.run_script('network', ['-s'])
                input("\n⏸️  Presiona Enter para continuar...")

            elif choice == "3":
                self.clear_screen()
                print("🔋 INFORMACIÓN DE BATERÍA DETALLADA")
                print("=" * 40)
                self.run_script('battery')
                input("\n⏸️  Presiona Enter para continuar...")

            elif choice == "4":
                self.clear_screen()
                print("💀 ADMINISTRADOR DE PROCESOS INTERACTIVO")
                print("=" * 50)
                self.run_script('process', ['-I'])

            elif choice == "5":
                self.clear_screen()
                print("🐳 COMANDOS ESPECÍFICOS PARA DOCKER")
                print("=" * 40)
                print("Docker detectado con 200GB de uso")
                print()
                print("Comandos disponibles:")
                print("1. docker system df - Ver uso del espacio")
                print("2. docker system prune - Limpiar recursos no usados")
                print("3. docker system prune -a - Limpieza agresiva")
                print()
                cmd_choice = input("Selecciona comando (1-3): ").strip()

                if cmd_choice == "1":
                    os.system("docker system df")
                elif cmd_choice == "2":
                    confirm = input("¿Confirmar limpieza básica de Docker? (y/N): ")
                    if confirm.lower() == 'y':
                        os.system("docker system prune")
                elif cmd_choice == "3":
                    confirm = input("¿Confirmar limpieza AGRESIVA de Docker? (y/N): ")
                    if confirm.lower() == 'y':
                        os.system("docker system prune -a")

                input("\n⏸️  Presiona Enter para continuar...")

            elif choice == "6":
                self.clear_screen()
                print("📋 INFORMACIÓN DEL SISTEMA M1")
                print("=" * 40)
                try:
                    os.system("system_profiler SPHardwareDataType")
                    print("\n" + "─" * 40)
                    os.system("sysctl -n machdep.cpu.brand_string")
                except:
                    print("❌ Error obteniendo información del sistema")
                input("\n⏸️  Presiona Enter para continuar...")

            elif choice == "7":
                self.clear_screen()
                print("🗂️  EXPLORADOR DE REPORTES")
                print("=" * 40)

                if self.reports_dir.exists():
                    reports = list(self.reports_dir.glob("*"))
                    if reports:
                        print("Reportes disponibles:")
                        for i, report in enumerate(reports, 1):
                            size = report.stat().st_size if report.is_file() else "DIR"
                            print(f"{i:2d}. {report.name} ({size})")
                        print(f"\n📁 Directorio: {self.reports_dir}")
                    else:
                        print("No hay reportes disponibles")
                else:
                    print("Directorio de reportes no existe")

                input("\n⏸️  Presiona Enter para continuar...")

            elif choice == "0":
                break
            else:
                print("❌ Opción inválida")
                time.sleep(1)

    def main_menu(self):
        """Menú principal del toolkit"""
        # Verificar dependencias al inicio
        missing = self.check_dependencies()
        if missing:
            self.clear_screen()
            print("❌ DEPENDENCIAS FALTANTES")
            print("=" * 40)
            for item in missing:
                print(f"• {item}")
            print("\nPor favor, instala las dependencias faltantes:")
            print("pip3 install psutil requests")
            print("chmod +x *.py")
            input("\nPresiona Enter para continuar (puede haber errores)...")

        while True:
            self.clear_screen()
            self.print_header()
            print("🎯 MENÚ PRINCIPAL")
            print("=" * 60)
            print()
            print("📊 ANÁLISIS Y REPORTES")
            print("  1. 🚀 Análisis rápido del sistema")
            print("  2. 📋 Análisis completo + reportes")
            print()
            print("🔧 MANTENIMIENTO")
            print("  3. 🧹 Smart Cleaner (recomendado)")
            print("  4. 🧹 Mantenimiento avanzado")
            print("  5. 📊 Monitoreo en tiempo real")
            print()
            print("🛠️  HERRAMIENTAS")
            print("  6. 🔍 Herramientas específicas")
            print("  7. ℹ️  Información y ayuda")
            print()
            print("  0. 🚪 Salir")
            print()

            choice = input("Selecciona una opción: ").strip()

            if choice == "1":
                self.quick_system_overview()

            elif choice == "2":
                self.comprehensive_analysis()

            elif choice == "3":
                self.run_script('smart')

            elif choice == "4":
                self.system_maintenance_menu()

            elif choice == "5":
                self.monitoring_menu()

            elif choice == "6":
                self.tools_menu()

            elif choice == "7":
                self.clear_screen()
                self.print_header()
                print("ℹ️  INFORMACIÓN Y AYUDA")
                print("=" * 60)
                print()
                print("📁 Scripts disponibles:")
                for name, script in self.scripts.items():
                    status = "✅" if (self.script_dir / script).exists() else "❌"
                    print(f"  {status} {script}")
                print()
                print("📋 Funcionalidades:")
                print("  • Análisis de almacenamiento y archivos grandes")
                print("  • Monitoreo de sistema, CPU, memoria y temperatura")
                print("  • Análisis de batería y ciclos de carga")
                print("  • Monitoreo de red y conectividad")
                print("  • Administración de procesos y memoria")
                print("  • Limpieza y mantenimiento automático")
                print()
                print("🔗 Para más información, ver README.md")
                print(f"📁 Directorio: {self.script_dir}")
                print(f"📊 Reportes: {self.reports_dir}")
                print()
                input("⏸️  Presiona Enter para continuar...")

            elif choice == "0":
                self.clear_screen()
                print("👋 ¡Gracias por usar Mac M1 Toolkit!")
                print("🍎 Mantén tu Mac en óptimas condiciones")
                break

            else:
                print("❌ Opción inválida")
                time.sleep(1)

def main():
    try:
        toolkit = MacToolkit()
        toolkit.main_menu()
    except KeyboardInterrupt:
        print("\n\n👋 Salida por interrupción del usuario")
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        print("Por favor, reporta este error")

if __name__ == "__main__":
    main()