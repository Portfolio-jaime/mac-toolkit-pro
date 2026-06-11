#!/usr/bin/env python3
"""
Storage Detective para Mac M1
Análisis interactivo profundo de hallazgos de almacenamiento con acciones específicas
"""

import os
import subprocess
import json
import time
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

class StorageDetective:
    def __init__(self):
        self.home = Path.home()
        self.findings = {}
        self.actions_log = []

    def clear_screen(self):
        """Limpia la pantalla"""
        os.system('clear')

    def format_bytes(self, bytes_size: int) -> str:
        """Convierte bytes a formato legible"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_size < 1024.0:
                return f"{bytes_size:.1f} {unit}"
            bytes_size /= 1024.0
        return f"{bytes_size:.1f} PB"

    def get_directory_size(self, path: Path) -> int:
        """Calcula el tamaño de un directorio"""
        total_size = 0
        try:
            for item in path.rglob('*'):
                if item.is_file():
                    try:
                        total_size += item.stat().st_size
                    except (OSError, FileNotFoundError):
                        continue
        except PermissionError:
            pass
        return total_size

    def analyze_docker_usage(self) -> Dict:
        """Analiza específicamente el uso de Docker"""
        docker_info = {
            'raw_file': self.home / "Library/Containers/com.docker.docker/Data/vms/0/data/Docker.raw",
            'containers': [],
            'images': [],
            'volumes': [],
            'system_info': {}
        }

        # Verificar archivo Docker.raw
        if docker_info['raw_file'].exists():
            docker_info['raw_size'] = docker_info['raw_file'].stat().st_size
        else:
            docker_info['raw_size'] = 0

        # Obtener información de Docker si está disponible
        try:
            # Información del sistema Docker
            result = subprocess.run(['docker', 'system', 'df'], capture_output=True, text=True)
            if result.returncode == 0:
                docker_info['system_info']['df'] = result.stdout

            # Contenedores
            result = subprocess.run(['docker', 'ps', '-a', '--format', 'table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Size}}'],
                                  capture_output=True, text=True)
            if result.returncode == 0:
                docker_info['containers'] = result.stdout

            # Imágenes
            result = subprocess.run(['docker', 'images', '--format', 'table {{.Repository}}\t{{.Tag}}\t{{.Size}}'],
                                  capture_output=True, text=True)
            if result.returncode == 0:
                docker_info['images'] = result.stdout

            # Volúmenes
            result = subprocess.run(['docker', 'volume', 'ls'], capture_output=True, text=True)
            if result.returncode == 0:
                docker_info['volumes'] = result.stdout

        except FileNotFoundError:
            docker_info['error'] = "Docker no está instalado o no está en PATH"

        return docker_info

    def analyze_ollama_models(self) -> Dict:
        """Analiza los modelos de Ollama"""
        ollama_dir = self.home / ".ollama"
        ollama_info = {
            'models_dir': ollama_dir / "models",
            'models': [],
            'total_size': 0
        }

        if not ollama_dir.exists():
            return ollama_info

        try:
            # Buscar archivos de modelos
            models_dir = ollama_dir / "models" / "blobs"
            if models_dir.exists():
                for blob_file in models_dir.glob("sha256-*"):
                    if blob_file.is_file():
                        size = blob_file.stat().st_size
                        ollama_info['models'].append({
                            'file': str(blob_file),
                            'name': blob_file.name[:16] + "...",
                            'size': size,
                            'size_human': self.format_bytes(size)
                        })
                        ollama_info['total_size'] += size

            # Intentar obtener lista de modelos instalados
            try:
                result = subprocess.run(['ollama', 'list'], capture_output=True, text=True)
                if result.returncode == 0:
                    ollama_info['installed_models'] = result.stdout
            except FileNotFoundError:
                ollama_info['note'] = "Comando ollama no disponible"

            ollama_info['models'].sort(key=lambda x: x['size'], reverse=True)

        except PermissionError:
            ollama_info['error'] = "Sin permisos para acceder a directorio Ollama"

        return ollama_info

    def analyze_browserlock_logs(self) -> Dict:
        """Analiza los logs de BrowserLock"""
        browserlock_dir = self.home / ".BrowserLock"
        log_info = {
            'log_dir': browserlock_dir,
            'main_log': browserlock_dir / "log" / "BrowserLock.log",
            'total_size': 0,
            'log_files': []
        }

        if not browserlock_dir.exists():
            return log_info

        try:
            if log_info['main_log'].exists():
                size = log_info['main_log'].stat().st_size
                log_info['main_log_size'] = size
                log_info['total_size'] += size

                # Analizar las últimas líneas del log
                try:
                    with open(log_info['main_log'], 'r', encoding='utf-8', errors='ignore') as f:
                        lines = f.readlines()
                        log_info['total_lines'] = len(lines)
                        log_info['sample_lines'] = lines[-10:] if lines else []
                except Exception:
                    log_info['read_error'] = "No se pudo leer el archivo de log"

            # Buscar otros logs
            if (browserlock_dir / "log").exists():
                for log_file in (browserlock_dir / "log").glob("*.log*"):
                    if log_file != log_info['main_log']:
                        size = log_file.stat().st_size
                        log_info['log_files'].append({
                            'file': str(log_file),
                            'name': log_file.name,
                            'size': size,
                            'size_human': self.format_bytes(size)
                        })
                        log_info['total_size'] += size

        except PermissionError:
            log_info['error'] = "Sin permisos para acceder a BrowserLock"

        return log_info

    def analyze_edge_versions(self) -> Dict:
        """Analiza las múltiples versiones de Microsoft Edge"""
        edge_dir = self.home / "Library/Application Support/Microsoft/EdgeUpdater/apps/msedge-stable"
        edge_info = {
            'base_dir': edge_dir,
            'versions': [],
            'total_size': 0
        }

        if not edge_dir.exists():
            return edge_info

        try:
            for version_dir in edge_dir.iterdir():
                if version_dir.is_dir() and version_dir.name.replace('.', '').isdigit():
                    size = self.get_directory_size(version_dir)
                    edge_info['versions'].append({
                        'version': version_dir.name,
                        'path': str(version_dir),
                        'size': size,
                        'size_human': self.format_bytes(size),
                        'date': datetime.fromtimestamp(version_dir.stat().st_mtime)
                    })
                    edge_info['total_size'] += size

            edge_info['versions'].sort(key=lambda x: x['date'], reverse=True)

        except PermissionError:
            edge_info['error'] = "Sin permisos para acceder a Edge"

        return edge_info

    def analyze_terraform_providers(self) -> Dict:
        """Analiza los providers de Terraform"""
        terraform_info = {
            'providers': [],
            'total_size': 0
        }

        # Buscar directorios .terraform en arheanja
        arheanja_dir = self.home / "arheanja"
        if arheanja_dir.exists():
            try:
                for terraform_dir in arheanja_dir.rglob(".terraform"):
                    if terraform_dir.is_dir():
                        providers_dir = terraform_dir / "providers"
                        if providers_dir.exists():
                            size = self.get_directory_size(providers_dir)
                            terraform_info['providers'].append({
                                'project': terraform_dir.parent.name,
                                'path': str(providers_dir),
                                'size': size,
                                'size_human': self.format_bytes(size)
                            })
                            terraform_info['total_size'] += size

                terraform_info['providers'].sort(key=lambda x: x['size'], reverse=True)

            except PermissionError:
                terraform_info['error'] = "Sin permisos para acceder a arheanja"

        return terraform_info

    def analyze_library_caches(self) -> Dict:
        """Analiza los cachés en Library"""
        library_dir = self.home / "Library"
        cache_info = {
            'caches_dir': library_dir / "Caches",
            'app_support_dir': library_dir / "Application Support",
            'caches': [],
            'app_support': [],
            'total_cache_size': 0,
            'total_app_support_size': 0
        }

        try:
            # Analizar Caches
            if cache_info['caches_dir'].exists():
                for cache_dir in cache_info['caches_dir'].iterdir():
                    if cache_dir.is_dir():
                        size = self.get_directory_size(cache_dir)
                        cache_info['caches'].append({
                            'app': cache_dir.name,
                            'path': str(cache_dir),
                            'size': size,
                            'size_human': self.format_bytes(size)
                        })
                        cache_info['total_cache_size'] += size

                cache_info['caches'].sort(key=lambda x: x['size'], reverse=True)

            # Analizar Application Support (top 10)
            if cache_info['app_support_dir'].exists():
                for app_dir in cache_info['app_support_dir'].iterdir():
                    if app_dir.is_dir():
                        size = self.get_directory_size(app_dir)
                        cache_info['app_support'].append({
                            'app': app_dir.name,
                            'path': str(app_dir),
                            'size': size,
                            'size_human': self.format_bytes(size)
                        })
                        cache_info['total_app_support_size'] += size

                cache_info['app_support'].sort(key=lambda x: x['size'], reverse=True)
                cache_info['app_support'] = cache_info['app_support'][:10]  # Top 10

        except PermissionError:
            cache_info['error'] = "Sin permisos para acceder a Library"

        return cache_info

    def docker_detective_menu(self, docker_info: Dict):
        """Menú detective para Docker"""
        while True:
            self.clear_screen()
            print("🐳 DOCKER DETECTIVE")
            print("=" * 60)
            print(f"📁 Archivo Docker.raw: {self.format_bytes(docker_info.get('raw_size', 0))}")
            print()

            if 'system_info' in docker_info and 'df' in docker_info['system_info']:
                print("📊 Estado del sistema Docker:")
                print(docker_info['system_info']['df'])
                print()

            print("ACCIONES DISPONIBLES:")
            print("1. 🔍 Ver contenedores detallados")
            print("2. 🖼️  Ver imágenes instaladas")
            print("3. 📦 Ver volúmenes")
            print("4. 🧹 Limpiar contenedores parados")
            print("5. 🗑️  Limpiar imágenes no usadas")
            print("6. 🚨 Limpieza agresiva (PRECAUCIÓN)")
            print("7. 📊 Ejecutar docker system df")
            print("8. 📋 Generar reporte Docker")
            print("0. ⬅️  Volver")
            print()

            choice = input("Selecciona una acción: ").strip()

            if choice == "1":
                self.clear_screen()
                print("🔍 CONTENEDORES DOCKER")
                print("=" * 40)
                if docker_info.get('containers'):
                    print(docker_info['containers'])
                else:
                    print("No se pudieron obtener contenedores")
                input("\n⏸️  Presiona Enter para continuar...")

            elif choice == "2":
                self.clear_screen()
                print("🖼️  IMÁGENES DOCKER")
                print("=" * 40)
                if docker_info.get('images'):
                    print(docker_info['images'])
                else:
                    print("No se pudieron obtener imágenes")
                input("\n⏸️  Presiona Enter para continuar...")

            elif choice == "3":
                self.clear_screen()
                print("📦 VOLÚMENES DOCKER")
                print("=" * 40)
                if docker_info.get('volumes'):
                    print(docker_info['volumes'])
                else:
                    print("No se pudieron obtener volúmenes")
                input("\n⏸️  Presiona Enter para continuar...")

            elif choice == "4":
                self.clear_screen()
                print("🧹 LIMPIAR CONTENEDORES PARADOS")
                print("=" * 40)
                confirm = input("¿Confirmar limpieza de contenedores parados? (y/N): ")
                if confirm.lower() == 'y':
                    try:
                        result = subprocess.run(['docker', 'container', 'prune', '-f'],
                                              capture_output=True, text=True)
                        print("✅ Resultado:")
                        print(result.stdout)
                        self.actions_log.append(f"Docker: Contenedores parados eliminados - {datetime.now()}")
                    except Exception as e:
                        print(f"❌ Error: {e}")
                input("\n⏸️  Presiona Enter para continuar...")

            elif choice == "5":
                self.clear_screen()
                print("🗑️  LIMPIAR IMÁGENES NO USADAS")
                print("=" * 40)
                confirm = input("¿Confirmar limpieza de imágenes no usadas? (y/N): ")
                if confirm.lower() == 'y':
                    try:
                        result = subprocess.run(['docker', 'image', 'prune', '-f'],
                                              capture_output=True, text=True)
                        print("✅ Resultado:")
                        print(result.stdout)
                        self.actions_log.append(f"Docker: Imágenes no usadas eliminadas - {datetime.now()}")
                    except Exception as e:
                        print(f"❌ Error: {e}")
                input("\n⏸️  Presiona Enter para continuar...")

            elif choice == "6":
                self.clear_screen()
                print("🚨 LIMPIEZA AGRESIVA DOCKER")
                print("=" * 40)
                print("⚠️  ADVERTENCIA: Esto eliminará:")
                print("   • Todos los contenedores parados")
                print("   • Todas las imágenes no usadas")
                print("   • Todas las redes no usadas")
                print("   • Todo el cache de build")
                print()
                confirm = input("¿Estás SEGURO? Escribe 'ELIMINAR': ")
                if confirm == 'ELIMINAR':
                    try:
                        result = subprocess.run(['docker', 'system', 'prune', '-a', '-f'],
                                              capture_output=True, text=True)
                        print("✅ Resultado:")
                        print(result.stdout)
                        self.actions_log.append(f"Docker: Limpieza agresiva ejecutada - {datetime.now()}")
                    except Exception as e:
                        print(f"❌ Error: {e}")
                input("\n⏸️  Presiona Enter para continuar...")

            elif choice == "7":
                self.clear_screen()
                print("📊 DOCKER SYSTEM DF")
                print("=" * 40)
                try:
                    subprocess.run(['docker', 'system', 'df'])
                except Exception as e:
                    print(f"❌ Error: {e}")
                input("\n⏸️  Presiona Enter para continuar...")

            elif choice == "8":
                self.clear_screen()
                print("📋 GENERANDO REPORTE DOCKER...")
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                report_file = Path.home() / f"docker_report_{timestamp}.txt"

                with open(report_file, 'w') as f:
                    f.write(f"Docker Report - {datetime.now()}\n")
                    f.write("=" * 50 + "\n\n")
                    f.write(f"Docker.raw size: {self.format_bytes(docker_info.get('raw_size', 0))}\n\n")

                    if docker_info.get('containers'):
                        f.write("CONTAINERS:\n")
                        f.write(docker_info['containers'])
                        f.write("\n\n")

                    if docker_info.get('images'):
                        f.write("IMAGES:\n")
                        f.write(docker_info['images'])
                        f.write("\n\n")

                    if docker_info.get('volumes'):
                        f.write("VOLUMES:\n")
                        f.write(docker_info['volumes'])

                print(f"✅ Reporte guardado en: {report_file}")
                input("\n⏸️  Presiona Enter para continuar...")

            elif choice == "0":
                break
            else:
                print("❌ Opción inválida")
                time.sleep(1)

    def ollama_detective_menu(self, ollama_info: Dict):
        """Menú detective para Ollama"""
        while True:
            self.clear_screen()
            print("🤖 OLLAMA DETECTIVE")
            print("=" * 60)
            print(f"📁 Tamaño total: {self.format_bytes(ollama_info.get('total_size', 0))}")
            print()

            if ollama_info.get('installed_models'):
                print("📋 Modelos instalados:")
                print(ollama_info['installed_models'])
                print()

            print("🗂️  Archivos de modelos encontrados:")
            for i, model in enumerate(ollama_info.get('models', [])[:10], 1):
                print(f"  {i:2d}. {model['size_human']:>8} - {model['name']}")
            print()

            print("ACCIONES DISPONIBLES:")
            print("1. 📋 Ver lista completa de modelos")
            print("2. 🗑️  Eliminar modelo específico")
            print("3. 🧹 Limpiar modelos no usados")
            print("4. 📊 Mostrar uso detallado")
            print("5. 📁 Explorar directorio de modelos")
            print("0. ⬅️  Volver")
            print()

            choice = input("Selecciona una acción: ").strip()

            if choice == "1":
                self.clear_screen()
                print("📋 LISTA COMPLETA DE MODELOS")
                print("=" * 60)
                for i, model in enumerate(ollama_info.get('models', []), 1):
                    print(f"{i:3d}. {model['size_human']:>10} - {model['file']}")
                input("\n⏸️  Presiona Enter para continuar...")

            elif choice == "2":
                self.clear_screen()
                print("🗑️  ELIMINAR MODELO ESPECÍFICO")
                print("=" * 40)
                try:
                    result = subprocess.run(['ollama', 'list'], capture_output=True, text=True)
                    if result.returncode == 0:
                        print("Modelos disponibles:")
                        print(result.stdout)
                        model_name = input("\nNombre del modelo a eliminar: ").strip()
                        if model_name:
                            confirm = input(f"¿Confirmar eliminación de '{model_name}'? (y/N): ")
                            if confirm.lower() == 'y':
                                result = subprocess.run(['ollama', 'rm', model_name],
                                                      capture_output=True, text=True)
                                if result.returncode == 0:
                                    print("✅ Modelo eliminado exitosamente")
                                    self.actions_log.append(f"Ollama: Modelo {model_name} eliminado - {datetime.now()}")
                                else:
                                    print(f"❌ Error: {result.stderr}")
                    else:
                        print("❌ No se pudo obtener lista de modelos")
                except FileNotFoundError:
                    print("❌ Comando ollama no encontrado")
                input("\n⏸️  Presiona Enter para continuar...")

            elif choice == "3":
                self.clear_screen()
                print("🧹 LIMPIAR MODELOS NO USADOS")
                print("=" * 40)
                print("Esta opción eliminará archivos de modelo huérfanos...")
                confirm = input("¿Continuar? (y/N): ")
                if confirm.lower() == 'y':
                    # Aquí implementarías la lógica para identificar y limpiar modelos huérfanos
                    print("🔍 Funcionalidad en desarrollo...")
                input("\n⏸️  Presiona Enter para continuar...")

            elif choice == "4":
                self.clear_screen()
                print("📊 USO DETALLADO DE OLLAMA")
                print("=" * 40)
                print(f"Directorio base: {ollama_info.get('models_dir', 'N/A')}")
                print(f"Total de archivos: {len(ollama_info.get('models', []))}")
                print(f"Tamaño total: {self.format_bytes(ollama_info.get('total_size', 0))}")
                print()
                print("Top 5 archivos más grandes:")
                for i, model in enumerate(ollama_info.get('models', [])[:5], 1):
                    print(f"  {i}. {model['size_human']:>8} - {model['name']}")
                input("\n⏸️  Presiona Enter para continuar...")

            elif choice == "5":
                self.clear_screen()
                print("📁 EXPLORAR DIRECTORIO DE MODELOS")
                print("=" * 40)
                models_dir = ollama_info.get('models_dir')
                if models_dir and Path(models_dir).exists():
                    try:
                        subprocess.run(['open', str(models_dir)])
                        print(f"✅ Abriendo directorio: {models_dir}")
                    except Exception:
                        print(f"📁 Directorio: {models_dir}")
                        print("(No se pudo abrir automáticamente)")
                else:
                    print("❌ Directorio no encontrado")
                input("\n⏸️  Presiona Enter para continuar...")

            elif choice == "0":
                break
            else:
                print("❌ Opción inválida")
                time.sleep(1)

    def browserlock_detective_menu(self, log_info: Dict):
        """Menú detective para BrowserLock"""
        while True:
            self.clear_screen()
            print("🔒 BROWSERLOCK DETECTIVE")
            print("=" * 60)
            print(f"📁 Log principal: {self.format_bytes(log_info.get('main_log_size', 0))}")
            print(f"📄 Total de líneas: {log_info.get('total_lines', 'N/A'):,}")
            print()

            if log_info.get('sample_lines'):
                print("📋 Últimas 5 líneas del log:")
                for line in log_info['sample_lines'][-5:]:
                    print(f"  {line.strip()[:80]}...")
                print()

            print("ACCIONES DISPONIBLES:")
            print("1. 📄 Ver últimas líneas del log")
            print("2. 🔍 Buscar en el log")
            print("3. 📊 Analizar patrones del log")
            print("4. 🗑️  Rotar/comprimir log (PRECAUCIÓN)")
            print("5. 📁 Abrir directorio de logs")
            print("6. 📋 Generar reporte BrowserLock")
            print("0. ⬅️  Volver")
            print()

            choice = input("Selecciona una acción: ").strip()

            if choice == "1":
                self.clear_screen()
                print("📄 ÚLTIMAS LÍNEAS DEL LOG")
                print("=" * 60)
                lines = input("¿Cuántas líneas mostrar? (por defecto 50): ").strip()
                lines = int(lines) if lines.isdigit() else 50

                try:
                    result = subprocess.run(['tail', f'-{lines}', str(log_info['main_log'])],
                                          capture_output=True, text=True)
                    print(result.stdout)
                except Exception as e:
                    print(f"❌ Error: {e}")
                input("\n⏸️  Presiona Enter para continuar...")

            elif choice == "2":
                self.clear_screen()
                print("🔍 BUSCAR EN EL LOG")
                print("=" * 40)
                pattern = input("Patrón a buscar: ").strip()
                if pattern:
                    try:
                        result = subprocess.run(['grep', '-n', pattern, str(log_info['main_log'])],
                                              capture_output=True, text=True)
                        if result.stdout:
                            print(f"Coincidencias encontradas:")
                            print(result.stdout)
                        else:
                            print("No se encontraron coincidencias")
                    except Exception as e:
                        print(f"❌ Error: {e}")
                input("\n⏸️  Presiona Enter para continuar...")

            elif choice == "3":
                self.clear_screen()
                print("📊 ANÁLISIS DE PATRONES")
                print("=" * 40)
                try:
                    # Analizar patrones comunes
                    result = subprocess.run(['tail', '-1000', str(log_info['main_log'])],
                                          capture_output=True, text=True)
                    if result.stdout:
                        lines = result.stdout.split('\n')
                        print(f"Últimas 1000 líneas analizadas:")
                        print(f"Total de líneas: {len(lines)}")

                        # Buscar patrones comunes
                        error_count = len([l for l in lines if 'error' in l.lower()])
                        warning_count = len([l for l in lines if 'warning' in l.lower()])

                        print(f"Errores: {error_count}")
                        print(f"Warnings: {warning_count}")

                except Exception as e:
                    print(f"❌ Error: {e}")
                input("\n⏸️  Presiona Enter para continuar...")

            elif choice == "4":
                self.clear_screen()
                print("🗑️  ROTAR/COMPRIMIR LOG")
                print("=" * 40)
                print("⚠️  ADVERTENCIA: Esto moverá el log actual")
                print("El log se comprimirá y se creará uno nuevo")
                confirm = input("¿Continuar? (y/N): ")
                if confirm.lower() == 'y':
                    try:
                        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                        backup_path = log_info['main_log'].parent / f"BrowserLock_{timestamp}.log.gz"

                        # Comprimir el log actual
                        subprocess.run(['gzip', '-c', str(log_info['main_log'])],
                                     stdout=open(backup_path, 'wb'))

                        # Truncar el log original
                        with open(log_info['main_log'], 'w') as f:
                            pass

                        print(f"✅ Log rotado a: {backup_path}")
                        self.actions_log.append(f"BrowserLock: Log rotado - {datetime.now()}")
                    except Exception as e:
                        print(f"❌ Error: {e}")
                input("\n⏸️  Presiona Enter para continuar...")

            elif choice == "5":
                self.clear_screen()
                print("📁 ABRIR DIRECTORIO DE LOGS")
                print("=" * 40)
                try:
                    subprocess.run(['open', str(log_info['log_dir'])])
                    print(f"✅ Abriendo: {log_info['log_dir']}")
                except Exception:
                    print(f"📁 Directorio: {log_info['log_dir']}")
                input("\n⏸️  Presiona Enter para continuar...")

            elif choice == "6":
                self.clear_screen()
                print("📋 GENERANDO REPORTE BROWSERLOCK...")
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                report_file = Path.home() / f"browserlock_report_{timestamp}.txt"

                with open(report_file, 'w') as f:
                    f.write(f"BrowserLock Report - {datetime.now()}\n")
                    f.write("=" * 50 + "\n\n")
                    f.write(f"Main log size: {self.format_bytes(log_info.get('main_log_size', 0))}\n")
                    f.write(f"Total lines: {log_info.get('total_lines', 'N/A')}\n")
                    f.write(f"Log file: {log_info.get('main_log')}\n\n")

                    if log_info.get('sample_lines'):
                        f.write("Recent log entries:\n")
                        for line in log_info['sample_lines'][-20:]:
                            f.write(f"{line}")

                print(f"✅ Reporte guardado en: {report_file}")
                input("\n⏸️  Presiona Enter para continuar...")

            elif choice == "0":
                break
            else:
                print("❌ Opción inválida")
                time.sleep(1)

    def main_detective_menu(self):
        """Menú principal del detective de almacenamiento"""
        while True:
            self.clear_screen()
            print("🕵️ STORAGE DETECTIVE - ANÁLISIS INTERACTIVO")
            print("=" * 60)
            print("Analiza en profundidad los hallazgos de almacenamiento")
            print()
            print("🔍 HALLAZGOS PRINCIPALES:")
            print("1. 🐳 Docker (200GB) - Docker.raw y contenedores")
            print("2. 🤖 Ollama (12.8GB) - Modelos de IA")
            print("3. 🔒 BrowserLock (8.3GB) - Logs masivos")
            print("4. 🌐 Microsoft Edge - Múltiples versiones")
            print("5. 🏗️  Terraform - Providers descargados")
            print("6. 📁 Library/Caches (10.4GB) - Cachés del sistema")
            print("7. 📂 Library/Application Support (17GB)")
            print()
            print("🛠️  OPCIONES:")
            print("8. 📊 Resumen ejecutivo de hallazgos")
            print("9. 📋 Ver log de acciones realizadas")
            print("0. 🚪 Salir")
            print()

            choice = input("Selecciona un hallazgo para investigar: ").strip()

            if choice == "1":
                print("🔍 Analizando Docker...")
                docker_info = self.analyze_docker_usage()
                self.docker_detective_menu(docker_info)

            elif choice == "2":
                print("🔍 Analizando Ollama...")
                ollama_info = self.analyze_ollama_models()
                self.ollama_detective_menu(ollama_info)

            elif choice == "3":
                print("🔍 Analizando BrowserLock...")
                log_info = self.analyze_browserlock_logs()
                self.browserlock_detective_menu(log_info)

            elif choice == "4":
                print("🔍 Analizando Microsoft Edge...")
                edge_info = self.analyze_edge_versions()
                self.edge_detective_menu(edge_info)

            elif choice == "5":
                print("🔍 Analizando Terraform...")
                terraform_info = self.analyze_terraform_providers()
                self.terraform_detective_menu(terraform_info)

            elif choice == "6":
                print("🔍 Analizando Library/Caches...")
                cache_info = self.analyze_library_caches()
                self.library_detective_menu(cache_info, "Caches")

            elif choice == "7":
                print("🔍 Analizando Library/Application Support...")
                cache_info = self.analyze_library_caches()
                self.library_detective_menu(cache_info, "Application Support")

            elif choice == "8":
                self.show_executive_summary()

            elif choice == "9":
                self.show_actions_log()

            elif choice == "0":
                break

            else:
                print("❌ Opción inválida")
                time.sleep(1)

    def edge_detective_menu(self, edge_info: Dict):
        """Menú detective para Microsoft Edge"""
        while True:
            self.clear_screen()
            print("🌐 MICROSOFT EDGE DETECTIVE")
            print("=" * 60)
            print(f"📁 Tamaño total: {self.format_bytes(edge_info.get('total_size', 0))}")
            print()

            print("📋 Versiones encontradas:")
            for i, version in enumerate(edge_info.get('versions', []), 1):
                date_str = version['date'].strftime('%Y-%m-%d')
                print(f"  {i:2d}. {version['version']:<15} {version['size_human']:>8} ({date_str})")
            print()

            print("ACCIONES DISPONIBLES:")
            print("1. 🗑️  Eliminar versiones antiguas")
            print("2. 📁 Abrir directorio de Edge")
            print("3. 📊 Análisis detallado de versiones")
            print("4. 🧹 Limpieza de caché de Edge")
            print("0. ⬅️  Volver")
            print()

            choice = input("Selecciona una acción: ").strip()

            if choice == "1":
                self.clear_screen()
                print("🗑️  ELIMINAR VERSIONES ANTIGUAS")
                print("=" * 40)
                versions = edge_info.get('versions', [])
                if len(versions) > 1:
                    print("Versiones disponibles (la más reciente se mantendrá):")
                    for i, version in enumerate(versions[1:], 1):  # Skip most recent
                        print(f"  {i}. {version['version']} - {version['size_human']}")

                    to_delete = input("Números de versiones a eliminar (ej: 1,2,3): ").strip()
                    if to_delete:
                        try:
                            indices = [int(x.strip()) for x in to_delete.split(',')]
                            confirm = input(f"¿Confirmar eliminación de {len(indices)} versiones? (y/N): ")
                            if confirm.lower() == 'y':
                                deleted_size = 0
                                for idx in indices:
                                    if 1 <= idx <= len(versions) - 1:
                                        version = versions[idx]  # indices are offset by 1
                                        try:
                                            shutil.rmtree(version['path'])
                                            deleted_size += version['size']
                                            print(f"✅ Eliminada versión {version['version']}")
                                        except Exception as e:
                                            print(f"❌ Error eliminando {version['version']}: {e}")

                                if deleted_size > 0:
                                    self.actions_log.append(f"Edge: {self.format_bytes(deleted_size)} liberados - {datetime.now()}")
                        except ValueError:
                            print("❌ Formato inválido")
                else:
                    print("Solo hay una versión instalada")
                input("\n⏸️  Presiona Enter para continuar...")

            elif choice == "2":
                try:
                    subprocess.run(['open', str(edge_info['base_dir'])])
                    print(f"✅ Abriendo: {edge_info['base_dir']}")
                except Exception:
                    print(f"📁 Directorio: {edge_info['base_dir']}")
                input("\n⏸️  Presiona Enter para continuar...")

            elif choice == "3":
                self.clear_screen()
                print("📊 ANÁLISIS DETALLADO DE VERSIONES")
                print("=" * 60)
                for version in edge_info.get('versions', []):
                    print(f"Versión: {version['version']}")
                    print(f"  Tamaño: {version['size_human']}")
                    print(f"  Fecha: {version['date'].strftime('%Y-%m-%d %H:%M:%S')}")
                    print(f"  Ruta: {version['path']}")
                    print()
                input("\n⏸️  Presiona Enter para continuar...")

            elif choice == "4":
                print("🧹 Funcionalidad de limpieza de caché en desarrollo...")
                input("\n⏸️  Presiona Enter para continuar...")

            elif choice == "0":
                break
            else:
                print("❌ Opción inválida")
                time.sleep(1)

    def terraform_detective_menu(self, terraform_info: Dict):
        """Menú detective para Terraform"""
        while True:
            self.clear_screen()
            print("🏗️  TERRAFORM DETECTIVE")
            print("=" * 60)
            print(f"📁 Tamaño total: {self.format_bytes(terraform_info.get('total_size', 0))}")
            print()

            print("📋 Providers encontrados:")
            for i, provider in enumerate(terraform_info.get('providers', []), 1):
                print(f"  {i:2d}. {provider['project']:<20} {provider['size_human']:>8}")
            print()

            print("ACCIONES DISPONIBLES:")
            print("1. 🗑️  Limpiar providers específicos")
            print("2. 🧹 Limpiar todos los .terraform")
            print("3. 📁 Explorar proyectos")
            print("4. 🔄 Reinicializar proyecto específico")
            print("0. ⬅️  Volver")
            print()

            choice = input("Selecciona una acción: ").strip()

            if choice == "1":
                self.clear_screen()
                print("🗑️  LIMPIAR PROVIDERS ESPECÍFICOS")
                print("=" * 40)
                providers = terraform_info.get('providers', [])
                if providers:
                    for i, provider in enumerate(providers, 1):
                        print(f"  {i}. {provider['project']} - {provider['size_human']}")

                    to_delete = input("Números de providers a eliminar (ej: 1,2): ").strip()
                    if to_delete:
                        try:
                            indices = [int(x.strip()) for x in to_delete.split(',')]
                            confirm = input(f"¿Confirmar eliminación? (y/N): ")
                            if confirm.lower() == 'y':
                                for idx in indices:
                                    if 1 <= idx <= len(providers):
                                        provider = providers[idx - 1]
                                        try:
                                            shutil.rmtree(provider['path'])
                                            print(f"✅ Eliminado: {provider['project']}")
                                            self.actions_log.append(f"Terraform: {provider['project']} limpiado - {datetime.now()}")
                                        except Exception as e:
                                            print(f"❌ Error: {e}")
                        except ValueError:
                            print("❌ Formato inválido")
                else:
                    print("No hay providers para eliminar")
                input("\n⏸️  Presiona Enter para continuar...")

            elif choice == "2":
                self.clear_screen()
                print("🧹 LIMPIAR TODOS LOS .terraform")
                print("=" * 40)
                print("⚠️  ADVERTENCIA: Esto eliminará todos los directorios .terraform")
                print("Tendrás que ejecutar 'terraform init' en cada proyecto")
                confirm = input("¿Estás SEGURO? Escribe 'LIMPIAR': ")
                if confirm == 'LIMPIAR':
                    total_cleaned = 0
                    for provider in terraform_info.get('providers', []):
                        try:
                            terraform_dir = Path(provider['path']).parent
                            shutil.rmtree(terraform_dir)
                            total_cleaned += provider['size']
                            print(f"✅ Limpiado: {provider['project']}")
                        except Exception as e:
                            print(f"❌ Error en {provider['project']}: {e}")

                    if total_cleaned > 0:
                        self.actions_log.append(f"Terraform: {self.format_bytes(total_cleaned)} liberados - {datetime.now()}")
                input("\n⏸️  Presiona Enter para continuar...")

            elif choice == "3":
                self.clear_screen()
                print("📁 EXPLORAR PROYECTOS")
                print("=" * 40)
                try:
                    subprocess.run(['open', str(self.home / "arheanja")])
                    print(f"✅ Abriendo: {self.home / 'arheanja'}")
                except Exception:
                    print(f"📁 Directorio: {self.home / 'arheanja'}")
                input("\n⏸️  Presiona Enter para continuar...")

            elif choice == "4":
                print("🔄 Funcionalidad de reinicialización en desarrollo...")
                input("\n⏸️  Presiona Enter para continuar...")

            elif choice == "0":
                break
            else:
                print("❌ Opción inválida")
                time.sleep(1)

    def library_detective_menu(self, cache_info: Dict, mode: str):
        """Menú detective para Library (Caches o Application Support)"""
        data_key = 'caches' if mode == 'Caches' else 'app_support'
        size_key = 'total_cache_size' if mode == 'Caches' else 'total_app_support_size'

        while True:
            self.clear_screen()
            print(f"📁 LIBRARY/{mode.upper()} DETECTIVE")
            print("=" * 60)
            print(f"📁 Tamaño total: {self.format_bytes(cache_info.get(size_key, 0))}")
            print()

            print(f"📋 Top aplicaciones por tamaño:")
            for i, item in enumerate(cache_info.get(data_key, [])[:10], 1):
                print(f"  {i:2d}. {item['app']:<30} {item['size_human']:>8}")
            print()

            print("ACCIONES DISPONIBLES:")
            print("1. 🗑️  Eliminar cachés específicos")
            print("2. 🧹 Limpieza masiva (PRECAUCIÓN)")
            print("3. 📁 Explorar directorio")
            print("4. 📊 Análisis detallado por aplicación")
            print("0. ⬅️  Volver")
            print()

            choice = input("Selecciona una acción: ").strip()

            if choice == "1":
                self.clear_screen()
                print(f"🗑️  ELIMINAR {mode.upper()} ESPECÍFICOS")
                print("=" * 40)
                items = cache_info.get(data_key, [])
                if items:
                    for i, item in enumerate(items[:15], 1):  # Show top 15
                        print(f"  {i:2d}. {item['app']:<25} {item['size_human']:>8}")

                    to_delete = input("Números a eliminar (ej: 1,2,3): ").strip()
                    if to_delete:
                        try:
                            indices = [int(x.strip()) for x in to_delete.split(',')]
                            print("\nElementos seleccionados:")
                            total_size = 0
                            for idx in indices:
                                if 1 <= idx <= len(items):
                                    item = items[idx - 1]
                                    print(f"  - {item['app']} ({item['size_human']})")
                                    total_size += item['size']

                            confirm = input(f"\n¿Confirmar eliminación de {self.format_bytes(total_size)}? (y/N): ")
                            if confirm.lower() == 'y':
                                deleted_size = 0
                                for idx in indices:
                                    if 1 <= idx <= len(items):
                                        item = items[idx - 1]
                                        try:
                                            shutil.rmtree(item['path'])
                                            deleted_size += item['size']
                                            print(f"✅ Eliminado: {item['app']}")
                                        except Exception as e:
                                            print(f"❌ Error eliminando {item['app']}: {e}")

                                if deleted_size > 0:
                                    self.actions_log.append(f"Library/{mode}: {self.format_bytes(deleted_size)} liberados - {datetime.now()}")
                        except ValueError:
                            print("❌ Formato inválido")
                else:
                    print("No hay elementos para eliminar")
                input("\n⏸️  Presiona Enter para continuar...")

            elif choice == "2":
                self.clear_screen()
                print(f"🧹 LIMPIEZA MASIVA DE {mode.upper()}")
                print("=" * 40)
                print("⚠️  ADVERTENCIA: Esto puede afectar el rendimiento de aplicaciones")
                print("Las aplicaciones regenerarán los cachés cuando sea necesario")
                confirm = input("¿Estás SEGURO? Escribe 'LIMPIAR': ")
                if confirm == 'LIMPIAR':
                    # Implementar limpieza masiva con excepciones para cachés críticos
                    critical_apps = {'com.apple.dock', 'com.apple.finder', 'com.apple.spotlight'}
                    total_deleted = 0

                    for item in cache_info.get(data_key, []):
                        if item['app'] not in critical_apps:
                            try:
                                shutil.rmtree(item['path'])
                                total_deleted += item['size']
                                print(f"✅ Eliminado: {item['app']}")
                            except Exception as e:
                                print(f"❌ Error eliminando {item['app']}: {e}")

                    if total_deleted > 0:
                        self.actions_log.append(f"Library/{mode}: Limpieza masiva {self.format_bytes(total_deleted)} - {datetime.now()}")
                input("\n⏸️  Presiona Enter para continuar...")

            elif choice == "3":
                dir_key = 'caches_dir' if mode == 'Caches' else 'app_support_dir'
                try:
                    subprocess.run(['open', str(cache_info[dir_key])])
                    print(f"✅ Abriendo: {cache_info[dir_key]}")
                except Exception:
                    print(f"📁 Directorio: {cache_info[dir_key]}")
                input("\n⏸️  Presiona Enter para continuar...")

            elif choice == "4":
                self.clear_screen()
                print(f"📊 ANÁLISIS DETALLADO DE {mode.upper()}")
                print("=" * 60)
                for item in cache_info.get(data_key, [])[:20]:
                    print(f"App: {item['app']}")
                    print(f"  Tamaño: {item['size_human']}")
                    print(f"  Ruta: {item['path']}")
                    print()
                input("\n⏸️  Presiona Enter para continuar...")

            elif choice == "0":
                break
            else:
                print("❌ Opción inválida")
                time.sleep(1)

    def show_executive_summary(self):
        """Muestra un resumen ejecutivo de todos los hallazgos"""
        self.clear_screen()
        print("📊 RESUMEN EJECUTIVO DE HALLAZGOS")
        print("=" * 60)
        print()

        # Calcular totales aproximados
        docker_size = 200 * 1024**3  # 200GB
        ollama_size = 12.8 * 1024**3  # 12.8GB
        browserlock_size = 8.3 * 1024**3  # 8.3GB
        edge_size = 2 * 1024**3  # ~2GB
        terraform_size = 703 * 1024**2  # 703MB
        cache_size = 10.4 * 1024**3  # 10.4GB
        app_support_size = 17 * 1024**3  # 17GB

        total_identifiable = (docker_size + ollama_size + browserlock_size +
                            edge_size + terraform_size + cache_size + app_support_size)

        print("🎯 OPORTUNIDADES DE LIMPIEZA:")
        print(f"  🐳 Docker:                {self.format_bytes(docker_size):>10} (Crítico)")
        print(f"  📂 Application Support:   {self.format_bytes(app_support_size):>10} (Alto)")
        print(f"  🤖 Ollama:                {self.format_bytes(ollama_size):>10} (Alto)")
        print(f"  📁 Cachés:                {self.format_bytes(cache_size):>10} (Medio)")
        print(f"  🔒 BrowserLock:           {self.format_bytes(browserlock_size):>10} (Medio)")
        print(f"  🌐 Edge:                  {self.format_bytes(edge_size):>10} (Bajo)")
        print(f"  🏗️  Terraform:            {self.format_bytes(terraform_size):>10} (Bajo)")
        print("  " + "─" * 40)
        print(f"  📊 Total identificado:    {self.format_bytes(total_identifiable):>10}")
        print()

        print("💡 RECOMENDACIONES POR PRIORIDAD:")
        print()
        print("🔴 PRIORIDAD ALTA (Impacto inmediato):")
        print("  • Docker: Ejecutar 'docker system prune -a' (~150GB)")
        print("  • Application Support: Revisar aplicaciones no usadas")
        print()
        print("🟡 PRIORIDAD MEDIA:")
        print("  • Ollama: Eliminar modelos no utilizados")
        print("  • BrowserLock: Rotar/comprimir logs")
        print("  • Cachés: Limpieza selectiva de aplicaciones")
        print()
        print("🟢 PRIORIDAD BAJA:")
        print("  • Edge: Eliminar versiones antiguas")
        print("  • Terraform: Limpiar providers no usados")
        print()

        print("📈 POTENCIAL DE RECUPERACIÓN:")
        print(f"  Conservador (50%): {self.format_bytes(total_identifiable * 0.5):>10}")
        print(f"  Moderado (70%):    {self.format_bytes(total_identifiable * 0.7):>10}")
        print(f"  Agresivo (85%):    {self.format_bytes(total_identifiable * 0.85):>10}")

        input("\n⏸️  Presiona Enter para continuar...")

    def show_actions_log(self):
        """Muestra el log de acciones realizadas"""
        self.clear_screen()
        print("📋 LOG DE ACCIONES REALIZADAS")
        print("=" * 60)

        if self.actions_log:
            for i, action in enumerate(self.actions_log, 1):
                print(f"{i:2d}. {action}")
        else:
            print("No se han realizado acciones aún")

        print()
        print("💾 Las acciones se registran durante esta sesión")
        print("Para un log permanente, considera usar los reportes individuales")

        input("\n⏸️  Presiona Enter para continuar...")

def main():
    detective = StorageDetective()
    try:
        detective.main_detective_menu()
    except KeyboardInterrupt:
        print("\n👋 Storage Detective terminado")
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")

if __name__ == "__main__":
    main()