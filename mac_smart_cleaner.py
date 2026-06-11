#!/usr/bin/env python3
"""
Mac Smart Cleaner - Limpiador Inteligente y Amigable
Versión simplificada y robusta del storage detective con mejor UX
"""

import os
import subprocess
import json
import time
import shutil
import signal
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

class SmartCleaner:
    def __init__(self):
        self.home = Path.home()
        self.session_log = []
        self.total_freed = 0

    def log_action(self, action: str, size_freed: int = 0):
        """Registra una acción realizada"""
        self.session_log.append({
            'timestamp': datetime.now().strftime('%H:%M:%S'),
            'action': action,
            'size_freed': size_freed
        })
        self.total_freed += size_freed

    def format_bytes(self, bytes_size: int) -> str:
        """Convierte bytes a formato legible"""
        if bytes_size == 0:
            return "0 B"
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_size < 1024.0:
                return f"{bytes_size:.1f} {unit}"
            bytes_size /= 1024.0
        return f"{bytes_size:.1f} PB"

    def safe_run_command(self, cmd: List[str], description: str = "", timeout: int = 30) -> Dict:
        """Ejecuta un comando de forma segura con manejo de errores"""
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False
            )
            return {
                'success': result.returncode == 0,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'returncode': result.returncode
            }
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': f"Comando expiró después de {timeout}s",
                'stdout': '',
                'stderr': ''
            }
        except FileNotFoundError:
            return {
                'success': False,
                'error': f"Comando no encontrado: {cmd[0]}",
                'stdout': '',
                'stderr': ''
            }
        except Exception as e:
            return {
                'success': False,
                'error': f"Error inesperado: {str(e)}",
                'stdout': '',
                'stderr': ''
            }

    def print_header(self, title: str):
        """Imprime un header formateado"""
        print("\n" + "🔧" + "=" * 58 + "🔧")
        print(f"           {title}")
        print("🔧" + "=" * 58 + "🔧")

    def print_success(self, message: str):
        """Imprime mensaje de éxito"""
        print(f"✅ {message}")

    def print_error(self, message: str):
        """Imprime mensaje de error"""
        print(f"❌ {message}")

    def print_warning(self, message: str):
        """Imprime mensaje de advertencia"""
        print(f"⚠️  {message}")

    def print_info(self, message: str):
        """Imprime mensaje informativo"""
        print(f"ℹ️  {message}")

    def confirm_action(self, message: str, danger_level: str = "normal") -> bool:
        """Solicita confirmación del usuario"""
        if danger_level == "high":
            print(f"\n🚨 ACCIÓN PELIGROSA: {message}")
            response = input("Escribe 'CONFIRMO' para continuar: ").strip()
            return response == "CONFIRMO"
        elif danger_level == "medium":
            print(f"\n⚠️  {message}")
            response = input("¿Continuar? (s/N): ").strip().lower()
            return response in ['s', 'si', 'sí', 'y', 'yes']
        else:
            print(f"\n{message}")
            response = input("¿Continuar? (s/N): ").strip().lower()
            return response in ['s', 'si', 'sí', 'y', 'yes']

    def wait_for_user(self, message: str = "Presiona Enter para continuar..."):
        """Espera input del usuario"""
        try:
            input(f"\n⏸️  {message}")
        except KeyboardInterrupt:
            print("\n👋 Operación cancelada por el usuario")
            return False
        return True

    # ==================== DOCKER FUNCTIONS ====================

    def docker_status(self) -> Dict:
        """Obtiene el estado completo de Docker"""
        status = {
            'installed': False,
            'running': False,
            'containers': {'total': 0, 'running': 0, 'stopped': 0},
            'images': {'total': 0, 'size': 0},
            'volumes': {'total': 0, 'size': 0},
            'networks': {'total': 0},
            'disk_usage': {},
            'docker_raw_size': 0
        }

        # Verificar Docker Desktop
        docker_raw = self.home / "Library/Containers/com.docker.docker/Data/vms/0/data/Docker.raw"
        if docker_raw.exists():
            status['docker_raw_size'] = docker_raw.stat().st_size

        # Verificar si Docker está instalado y corriendo
        result = self.safe_run_command(['docker', 'version'], "Verificar Docker")
        if not result['success']:
            return status

        status['installed'] = True

        # Verificar si Docker daemon está corriendo
        result = self.safe_run_command(['docker', 'info'], "Info de Docker")
        if result['success']:
            status['running'] = True

            # Obtener información detallada
            self._get_docker_containers(status)
            self._get_docker_images(status)
            self._get_docker_volumes(status)
            self._get_docker_networks(status)
            self._get_docker_disk_usage(status)

        return status

    def _get_docker_containers(self, status: Dict):
        """Obtiene información de contenedores"""
        result = self.safe_run_command(['docker', 'ps', '-a', '--format', 'json'])
        if result['success'] and result['stdout'].strip():
            containers = [json.loads(line) for line in result['stdout'].strip().split('\n')]
            status['containers']['total'] = len(containers)
            status['containers']['running'] = len([c for c in containers if 'Up' in c.get('Status', '')])
            status['containers']['stopped'] = status['containers']['total'] - status['containers']['running']

    def _get_docker_images(self, status: Dict):
        """Obtiene información de imágenes"""
        result = self.safe_run_command(['docker', 'images', '--format', 'json'])
        if result['success'] and result['stdout'].strip():
            images = [json.loads(line) for line in result['stdout'].strip().split('\n')]
            status['images']['total'] = len(images)

    def _get_docker_volumes(self, status: Dict):
        """Obtiene información de volúmenes"""
        result = self.safe_run_command(['docker', 'volume', 'ls', '--format', 'json'])
        if result['success'] and result['stdout'].strip():
            volumes = [json.loads(line) for line in result['stdout'].strip().split('\n')]
            status['volumes']['total'] = len(volumes)

    def _get_docker_networks(self, status: Dict):
        """Obtiene información de redes"""
        result = self.safe_run_command(['docker', 'network', 'ls', '--format', 'json'])
        if result['success'] and result['stdout'].strip():
            networks = [json.loads(line) for line in result['stdout'].strip().split('\n')]
            status['networks']['total'] = len(networks)

    def _get_docker_disk_usage(self, status: Dict):
        """Obtiene uso de disco de Docker"""
        result = self.safe_run_command(['docker', 'system', 'df', '--format', 'json'])
        if result['success'] and result['stdout'].strip():
            try:
                status['disk_usage'] = json.loads(result['stdout'])
            except json.JSONDecodeError:
                pass

    def docker_menu(self):
        """Menú principal de Docker"""
        while True:
            os.system('clear')
            self.print_header("🐳 DOCKER MANAGER")

            status = self.docker_status()

            print(f"\n📊 ESTADO:")
            if not status['installed']:
                self.print_error("Docker no está instalado")
                self.wait_for_user()
                break
            elif not status['running']:
                self.print_warning("Docker está instalado pero no está corriendo")
                print("Inicia Docker Desktop y vuelve a intentar")
                self.wait_for_user()
                break
            else:
                self.print_success("Docker está corriendo")

            print(f"\n📁 RECURSOS:")
            print(f"   Docker.raw: {self.format_bytes(status['docker_raw_size'])}")
            print(f"   Contenedores: {status['containers']['total']} (🟢{status['containers']['running']} activos, 🔴{status['containers']['stopped']} parados)")
            print(f"   Imágenes: {status['images']['total']}")
            print(f"   Volúmenes: {status['volumes']['total']}")
            print(f"   Redes: {status['networks']['total']}")

            print(f"\n🛠️  ACCIONES DISPONIBLES:")
            print("1. 📊 Ver uso detallado del disco (docker system df)")
            print("2. 📋 Listar contenedores")
            print("3. 🖼️  Listar imágenes")
            print("4. 💾 Listar volúmenes")
            print("5. 🌐 Listar redes")
            print()
            print("🧹 LIMPIEZA:")
            print("6. 🗑️  Eliminar contenedores parados")
            print("7. 🖼️  Eliminar imágenes sin usar")
            print("8. 💾 Eliminar volúmenes sin usar")
            print("9. 🌐 Eliminar redes sin usar")
            print("10. 🧹 Limpieza completa (todo lo anterior)")
            print("11. 🚨 Limpieza agresiva (incluye imágenes con tag)")
            print()
            print("⚙️  GESTIÓN:")
            print("12. 🔄 Reiniciar Docker")
            print("13. ⏹️  Parar todos los contenedores")
            print("14. 📊 Ver logs de contenedor específico")
            print("15. 🔍 Inspeccionar contenedor/imagen")
            print()
            print("0. ⬅️  Volver")

            try:
                choice = input("\n🎯 Selecciona una opción: ").strip()
            except KeyboardInterrupt:
                break

            if choice == "1":
                self._docker_disk_usage()
            elif choice == "2":
                self._docker_list_containers()
            elif choice == "3":
                self._docker_list_images()
            elif choice == "4":
                self._docker_list_volumes()
            elif choice == "5":
                self._docker_list_networks()
            elif choice == "6":
                self._docker_clean_containers()
            elif choice == "7":
                self._docker_clean_images()
            elif choice == "8":
                self._docker_clean_volumes()
            elif choice == "9":
                self._docker_clean_networks()
            elif choice == "10":
                self._docker_clean_all()
            elif choice == "11":
                self._docker_clean_aggressive()
            elif choice == "12":
                self._docker_restart()
            elif choice == "13":
                self._docker_stop_all()
            elif choice == "14":
                self._docker_logs()
            elif choice == "15":
                self._docker_inspect()
            elif choice == "0":
                break
            else:
                self.print_error("Opción inválida")
                time.sleep(1)

    def _docker_disk_usage(self):
        """Muestra uso de disco de Docker"""
        print("\n📊 USO DE DISCO DE DOCKER:")
        result = self.safe_run_command(['docker', 'system', 'df', '-v'])
        if result['success']:
            print(result['stdout'])
        else:
            self.print_error(f"Error: {result.get('error', 'Comando falló')}")
        self.wait_for_user()

    def _docker_list_containers(self):
        """Lista contenedores"""
        print("\n📋 CONTENEDORES:")
        result = self.safe_run_command(['docker', 'ps', '-a'])
        if result['success']:
            print(result['stdout'])
        else:
            self.print_error(f"Error: {result.get('error', 'Comando falló')}")
        self.wait_for_user()

    def _docker_list_images(self):
        """Lista imágenes"""
        print("\n🖼️  IMÁGENES:")
        result = self.safe_run_command(['docker', 'images'])
        if result['success']:
            print(result['stdout'])
        else:
            self.print_error(f"Error: {result.get('error', 'Comando falló')}")
        self.wait_for_user()

    def _docker_list_volumes(self):
        """Lista volúmenes"""
        print("\n💾 VOLÚMENES:")
        result = self.safe_run_command(['docker', 'volume', 'ls'])
        if result['success']:
            print(result['stdout'])
        else:
            self.print_error(f"Error: {result.get('error', 'Comando falló')}")
        self.wait_for_user()

    def _docker_list_networks(self):
        """Lista redes"""
        print("\n🌐 REDES:")
        result = self.safe_run_command(['docker', 'network', 'ls'])
        if result['success']:
            print(result['stdout'])
        else:
            self.print_error(f"Error: {result.get('error', 'Comando falló')}")
        self.wait_for_user()

    def _docker_clean_containers(self):
        """Limpia contenedores parados"""
        if not self.confirm_action("Eliminar todos los contenedores parados"):
            return

        print("\n🗑️  Eliminando contenedores parados...")
        result = self.safe_run_command(['docker', 'container', 'prune', '-f'])
        if result['success']:
            self.print_success("Contenedores parados eliminados")
            print(result['stdout'])
            self.log_action("Docker: Contenedores parados eliminados")
        else:
            self.print_error(f"Error: {result.get('error', 'Comando falló')}")
        self.wait_for_user()

    def _docker_clean_images(self):
        """Limpia imágenes sin usar"""
        if not self.confirm_action("Eliminar imágenes sin usar (dangling)"):
            return

        print("\n🖼️  Eliminando imágenes sin usar...")
        result = self.safe_run_command(['docker', 'image', 'prune', '-f'])
        if result['success']:
            self.print_success("Imágenes sin usar eliminadas")
            print(result['stdout'])
            self.log_action("Docker: Imágenes sin usar eliminadas")
        else:
            self.print_error(f"Error: {result.get('error', 'Comando falló')}")
        self.wait_for_user()

    def _docker_clean_volumes(self):
        """Limpia volúmenes sin usar"""
        if not self.confirm_action("Eliminar volúmenes sin usar", "medium"):
            return

        print("\n💾 Eliminando volúmenes sin usar...")
        result = self.safe_run_command(['docker', 'volume', 'prune', '-f'])
        if result['success']:
            self.print_success("Volúmenes sin usar eliminados")
            print(result['stdout'])
            self.log_action("Docker: Volúmenes sin usar eliminados")
        else:
            self.print_error(f"Error: {result.get('error', 'Comando falló')}")
        self.wait_for_user()

    def _docker_clean_networks(self):
        """Limpia redes sin usar"""
        if not self.confirm_action("Eliminar redes sin usar"):
            return

        print("\n🌐 Eliminando redes sin usar...")
        result = self.safe_run_command(['docker', 'network', 'prune', '-f'])
        if result['success']:
            self.print_success("Redes sin usar eliminadas")
            print(result['stdout'])
            self.log_action("Docker: Redes sin usar eliminadas")
        else:
            self.print_error(f"Error: {result.get('error', 'Comando falló')}")
        self.wait_for_user()

    def _docker_clean_all(self):
        """Limpieza completa de Docker"""
        if not self.confirm_action("Ejecutar limpieza completa (contenedores, imágenes dangling, volúmenes, redes)", "medium"):
            return

        print("\n🧹 Ejecutando limpieza completa...")
        result = self.safe_run_command(['docker', 'system', 'prune', '-f'])
        if result['success']:
            self.print_success("Limpieza completa ejecutada")
            print(result['stdout'])
            self.log_action("Docker: Limpieza completa ejecutada")
        else:
            self.print_error(f"Error: {result.get('error', 'Comando falló')}")
        self.wait_for_user()

    def _docker_clean_aggressive(self):
        """Limpieza agresiva de Docker"""
        if not self.confirm_action("ELIMINAR TODO: contenedores, imágenes, volúmenes, redes, cache de build", "high"):
            return

        print("\n🚨 Ejecutando limpieza agresiva...")
        result = self.safe_run_command(['docker', 'system', 'prune', '-a', '-f', '--volumes'])
        if result['success']:
            self.print_success("Limpieza agresiva ejecutada")
            print(result['stdout'])
            self.log_action("Docker: Limpieza agresiva ejecutada")
        else:
            self.print_error(f"Error: {result.get('error', 'Comando falló')}")
        self.wait_for_user()

    def _docker_restart(self):
        """Reinicia Docker"""
        if not self.confirm_action("Reiniciar Docker Desktop"):
            return

        print("\n🔄 Reiniciando Docker...")
        # En macOS, reiniciar Docker Desktop
        result = self.safe_run_command(['osascript', '-e', 'tell application "Docker Desktop" to quit'])
        if result['success']:
            time.sleep(3)
            result = self.safe_run_command(['open', '/Applications/Docker.app'])
            if result['success']:
                self.print_success("Docker reiniciado")
            else:
                self.print_error("Error al iniciar Docker Desktop")
        else:
            self.print_error("Error al cerrar Docker Desktop")
        self.wait_for_user()

    def _docker_stop_all(self):
        """Para todos los contenedores"""
        if not self.confirm_action("Parar todos los contenedores activos", "medium"):
            return

        print("\n⏹️  Parando todos los contenedores...")
        result = self.safe_run_command(['docker', 'stop', '$(docker', 'ps', '-q)'], timeout=60)
        if result['success']:
            self.print_success("Todos los contenedores parados")
            self.log_action("Docker: Todos los contenedores parados")
        else:
            # Intentar método alternativo
            containers_result = self.safe_run_command(['docker', 'ps', '-q'])
            if containers_result['success'] and containers_result['stdout'].strip():
                container_ids = containers_result['stdout'].strip().split('\n')
                for container_id in container_ids:
                    stop_result = self.safe_run_command(['docker', 'stop', container_id])
                    if stop_result['success']:
                        print(f"✅ Contenedor {container_id} parado")
                    else:
                        print(f"❌ Error parando contenedor {container_id}")
            else:
                self.print_info("No hay contenedores activos")
        self.wait_for_user()

    def _docker_logs(self):
        """Muestra logs de un contenedor"""
        print("\n📊 LOGS DE CONTENEDOR:")

        # Listar contenedores disponibles
        result = self.safe_run_command(['docker', 'ps', '-a', '--format', 'table {{.Names}}\t{{.Status}}'])
        if not result['success']:
            self.print_error("No se pudieron listar los contenedores")
            self.wait_for_user()
            return

        print("Contenedores disponibles:")
        print(result['stdout'])

        container_name = input("\nNombre del contenedor: ").strip()
        if not container_name:
            return

        lines = input("Número de líneas (Enter para 50): ").strip()
        lines = lines if lines.isdigit() else "50"

        print(f"\n📋 Últimas {lines} líneas del contenedor {container_name}:")
        result = self.safe_run_command(['docker', 'logs', '--tail', lines, container_name])
        if result['success']:
            print(result['stdout'])
        else:
            self.print_error(f"Error: {result.get('error', 'Comando falló')}")
        self.wait_for_user()

    def _docker_inspect(self):
        """Inspecciona un contenedor o imagen"""
        print("\n🔍 INSPECCIONAR CONTENEDOR/IMAGEN:")

        resource_type = input("¿Contenedor o imagen? (c/i): ").strip().lower()
        if resource_type not in ['c', 'i', 'contenedor', 'imagen']:
            self.print_error("Opción inválida")
            self.wait_for_user()
            return

        if resource_type in ['c', 'contenedor']:
            result = self.safe_run_command(['docker', 'ps', '-a', '--format', 'table {{.Names}}\t{{.Image}}'])
            if result['success']:
                print("Contenedores disponibles:")
                print(result['stdout'])
        else:
            result = self.safe_run_command(['docker', 'images', '--format', 'table {{.Repository}}\t{{.Tag}}'])
            if result['success']:
                print("Imágenes disponibles:")
                print(result['stdout'])

        name = input(f"\nNombre del {'contenedor' if resource_type in ['c', 'contenedor'] else 'imagen'}: ").strip()
        if not name:
            return

        print(f"\n🔍 Inspeccionando {name}:")
        result = self.safe_run_command(['docker', 'inspect', name])
        if result['success']:
            try:
                data = json.loads(result['stdout'])
                print(json.dumps(data, indent=2))
            except json.JSONDecodeError:
                print(result['stdout'])
        else:
            self.print_error(f"Error: {result.get('error', 'Comando falló')}")
        self.wait_for_user()

    # ==================== OLLAMA FUNCTIONS ====================

    def ollama_status(self) -> Dict:
        """Obtiene el estado de Ollama"""
        status = {
            'installed': False,
            'running': False,
            'models': [],
            'models_size': 0,
            'models_dir': self.home / ".ollama"
        }

        # Verificar si Ollama está instalado
        result = self.safe_run_command(['ollama', '--version'])
        if not result['success']:
            return status

        status['installed'] = True

        # Verificar si está corriendo (intentar listar modelos)
        result = self.safe_run_command(['ollama', 'list'])
        if result['success']:
            status['running'] = True
            self._parse_ollama_models(result['stdout'], status)

        # Calcular tamaño total de modelos
        if status['models_dir'].exists():
            status['models_size'] = self._calculate_ollama_size(status['models_dir'])

        return status

    def _parse_ollama_models(self, output: str, status: Dict):
        """Parsea la salida de ollama list"""
        lines = output.strip().split('\n')[1:]  # Skip header
        for line in lines:
            if line.strip():
                parts = line.split()
                if len(parts) >= 3:
                    name = parts[0]
                    tag = parts[1] if len(parts) > 1 else "latest"
                    size = parts[-1] if len(parts) > 2 else "Unknown"
                    status['models'].append({
                        'name': name,
                        'tag': tag,
                        'size': size,
                        'full_name': f"{name}:{tag}"
                    })

    def _calculate_ollama_size(self, ollama_dir: Path) -> int:
        """Calcula el tamaño total de Ollama"""
        total_size = 0
        try:
            for item in ollama_dir.rglob('*'):
                if item.is_file():
                    try:
                        total_size += item.stat().st_size
                    except (OSError, FileNotFoundError):
                        continue
        except PermissionError:
            pass
        return total_size

    def ollama_menu(self):
        """Menú principal de Ollama"""
        while True:
            os.system('clear')
            self.print_header("🤖 OLLAMA MANAGER")

            status = self.ollama_status()

            print(f"\n📊 ESTADO:")
            if not status['installed']:
                self.print_error("Ollama no está instalado")
                print("Instala Ollama desde: https://ollama.ai")
                self.wait_for_user()
                break
            elif not status['running']:
                self.print_warning("Ollama está instalado pero no responde")
                print("Verifica que el servicio esté corriendo")
                self.wait_for_user()
                break
            else:
                self.print_success("Ollama está funcionando")

            print(f"\n📁 RECURSOS:")
            print(f"   Directorio: {status['models_dir']}")
            print(f"   Tamaño total: {self.format_bytes(status['models_size'])}")
            print(f"   Modelos instalados: {len(status['models'])}")

            if status['models']:
                print(f"\n📋 MODELOS INSTALADOS:")
                for i, model in enumerate(status['models'][:5], 1):
                    print(f"   {i}. {model['full_name']} ({model['size']})")
                if len(status['models']) > 5:
                    print(f"   ... y {len(status['models']) - 5} más")

            print(f"\n🛠️  ACCIONES DISPONIBLES:")
            print("1. 📋 Listar todos los modelos")
            print("2. 📥 Descargar un modelo")
            print("3. 🗑️  Eliminar un modelo")
            print("4. 🧹 Limpieza inteligente (modelos sin usar)")
            print("5. 🔄 Actualizar un modelo")
            print("6. 💬 Probar un modelo")
            print("7. 📊 Ver información detallada de modelo")
            print("8. 📁 Explorar directorio de modelos")
            print("9. 🚨 Eliminar todos los modelos")
            print()
            print("0. ⬅️  Volver")

            try:
                choice = input("\n🎯 Selecciona una opción: ").strip()
            except KeyboardInterrupt:
                break

            if choice == "1":
                self._ollama_list_models()
            elif choice == "2":
                self._ollama_pull_model()
            elif choice == "3":
                self._ollama_remove_model(status)
            elif choice == "4":
                self._ollama_smart_cleanup(status)
            elif choice == "5":
                self._ollama_update_model(status)
            elif choice == "6":
                self._ollama_test_model(status)
            elif choice == "7":
                self._ollama_model_info(status)
            elif choice == "8":
                self._ollama_explore_directory(status)
            elif choice == "9":
                self._ollama_remove_all(status)
            elif choice == "0":
                break
            else:
                self.print_error("Opción inválida")
                time.sleep(1)

    def _ollama_list_models(self):
        """Lista todos los modelos de Ollama"""
        print("\n📋 MODELOS DE OLLAMA:")
        result = self.safe_run_command(['ollama', 'list'])
        if result['success']:
            print(result['stdout'])
        else:
            self.print_error(f"Error: {result.get('error', 'Comando falló')}")
        self.wait_for_user()

    def _ollama_pull_model(self):
        """Descarga un modelo de Ollama"""
        print("\n📥 DESCARGAR MODELO:")
        print("Modelos populares: llama2, codellama, mistral, neural-chat, starcode")

        model_name = input("Nombre del modelo a descargar: ").strip()
        if not model_name:
            return

        if self.confirm_action(f"Descargar el modelo '{model_name}' (puede ser varios GB)"):
            print(f"\n📥 Descargando {model_name}...")
            result = self.safe_run_command(['ollama', 'pull', model_name], timeout=600)  # 10 min timeout
            if result['success']:
                self.print_success(f"Modelo {model_name} descargado exitosamente")
                self.log_action(f"Ollama: Modelo {model_name} descargado")
            else:
                self.print_error(f"Error descargando {model_name}: {result.get('error', 'Comando falló')}")
        self.wait_for_user()

    def _ollama_remove_model(self, status: Dict):
        """Elimina un modelo específico"""
        if not status['models']:
            self.print_info("No hay modelos instalados")
            self.wait_for_user()
            return

        print("\n🗑️  ELIMINAR MODELO:")
        print("Modelos disponibles:")
        for i, model in enumerate(status['models'], 1):
            print(f"   {i}. {model['full_name']} ({model['size']})")

        try:
            choice = int(input("\nNúmero del modelo a eliminar (0 para cancelar): "))
            if choice == 0:
                return
            if 1 <= choice <= len(status['models']):
                model = status['models'][choice - 1]
                if self.confirm_action(f"Eliminar el modelo '{model['full_name']}'", "medium"):
                    print(f"\n🗑️  Eliminando {model['full_name']}...")
                    result = self.safe_run_command(['ollama', 'rm', model['full_name']])
                    if result['success']:
                        self.print_success(f"Modelo {model['full_name']} eliminado")
                        self.log_action(f"Ollama: Modelo {model['full_name']} eliminado")
                    else:
                        self.print_error(f"Error: {result.get('error', 'Comando falló')}")
            else:
                self.print_error("Selección inválida")
        except ValueError:
            self.print_error("Entrada inválida")
        self.wait_for_user()

    def _ollama_smart_cleanup(self, status: Dict):
        """Limpieza inteligente de modelos"""
        print("\n🧹 LIMPIEZA INTELIGENTE:")
        print("Esta función buscaría modelos duplicados, versiones antiguas, etc.")
        print("(Funcionalidad en desarrollo)")

        # Por ahora, mostrar modelos y permitir selección múltiple
        if not status['models']:
            self.print_info("No hay modelos para limpiar")
            self.wait_for_user()
            return

        print("\nModelos disponibles:")
        for i, model in enumerate(status['models'], 1):
            print(f"   {i}. {model['full_name']} ({model['size']})")

        models_to_remove = input("\nNúmeros de modelos a eliminar (ej: 1,3,5) o 'all' para todos: ").strip()

        if models_to_remove.lower() == 'all':
            if self.confirm_action("Eliminar TODOS los modelos", "high"):
                self._remove_all_ollama_models(status)
        elif models_to_remove:
            try:
                indices = [int(x.strip()) - 1 for x in models_to_remove.split(',')]
                models_selected = [status['models'][i] for i in indices if 0 <= i < len(status['models'])]

                if models_selected:
                    print("\nModelos seleccionados:")
                    for model in models_selected:
                        print(f"   - {model['full_name']}")

                    if self.confirm_action(f"Eliminar {len(models_selected)} modelos", "medium"):
                        for model in models_selected:
                            result = self.safe_run_command(['ollama', 'rm', model['full_name']])
                            if result['success']:
                                self.print_success(f"Eliminado: {model['full_name']}")
                                self.log_action(f"Ollama: Modelo {model['full_name']} eliminado")
                            else:
                                self.print_error(f"Error eliminando {model['full_name']}")
            except (ValueError, IndexError):
                self.print_error("Selección inválida")

        self.wait_for_user()

    def _ollama_update_model(self, status: Dict):
        """Actualiza un modelo"""
        if not status['models']:
            self.print_info("No hay modelos para actualizar")
            self.wait_for_user()
            return

        print("\n🔄 ACTUALIZAR MODELO:")
        print("Modelos disponibles:")
        for i, model in enumerate(status['models'], 1):
            print(f"   {i}. {model['full_name']}")

        try:
            choice = int(input("\nNúmero del modelo a actualizar (0 para cancelar): "))
            if choice == 0:
                return
            if 1 <= choice <= len(status['models']):
                model = status['models'][choice - 1]
                if self.confirm_action(f"Actualizar el modelo '{model['full_name']}'"):
                    print(f"\n🔄 Actualizando {model['full_name']}...")
                    result = self.safe_run_command(['ollama', 'pull', model['full_name']], timeout=600)
                    if result['success']:
                        self.print_success(f"Modelo {model['full_name']} actualizado")
                        self.log_action(f"Ollama: Modelo {model['full_name']} actualizado")
                    else:
                        self.print_error(f"Error: {result.get('error', 'Comando falló')}")
            else:
                self.print_error("Selección inválida")
        except ValueError:
            self.print_error("Entrada inválida")
        self.wait_for_user()

    def _ollama_test_model(self, status: Dict):
        """Prueba un modelo con una consulta simple"""
        if not status['models']:
            self.print_info("No hay modelos para probar")
            self.wait_for_user()
            return

        print("\n💬 PROBAR MODELO:")
        print("Modelos disponibles:")
        for i, model in enumerate(status['models'], 1):
            print(f"   {i}. {model['full_name']}")

        try:
            choice = int(input("\nNúmero del modelo a probar (0 para cancelar): "))
            if choice == 0:
                return
            if 1 <= choice <= len(status['models']):
                model = status['models'][choice - 1]

                prompt = input(f"\nPrompt para {model['full_name']} (Enter para usar 'Hello, how are you?'): ").strip()
                if not prompt:
                    prompt = "Hello, how are you?"

                print(f"\n💬 Probando {model['full_name']} con: '{prompt}'")
                print("(Esto puede tomar unos segundos...)")

                result = self.safe_run_command(['ollama', 'run', model['full_name'], prompt], timeout=120)
                if result['success']:
                    print(f"\n🤖 Respuesta de {model['full_name']}:")
                    print(result['stdout'])
                else:
                    self.print_error(f"Error: {result.get('error', 'Comando falló')}")
            else:
                self.print_error("Selección inválida")
        except ValueError:
            self.print_error("Entrada inválida")
        self.wait_for_user()

    def _ollama_model_info(self, status: Dict):
        """Muestra información detallada de un modelo"""
        if not status['models']:
            self.print_info("No hay modelos disponibles")
            self.wait_for_user()
            return

        print("\n📊 INFORMACIÓN DE MODELO:")
        print("Modelos disponibles:")
        for i, model in enumerate(status['models'], 1):
            print(f"   {i}. {model['full_name']}")

        try:
            choice = int(input("\nNúmero del modelo (0 para cancelar): "))
            if choice == 0:
                return
            if 1 <= choice <= len(status['models']):
                model = status['models'][choice - 1]
                print(f"\n📊 Información de {model['full_name']}:")

                result = self.safe_run_command(['ollama', 'show', model['full_name']])
                if result['success']:
                    print(result['stdout'])
                else:
                    self.print_error(f"Error: {result.get('error', 'Comando falló')}")
            else:
                self.print_error("Selección inválida")
        except ValueError:
            self.print_error("Entrada inválida")
        self.wait_for_user()

    def _ollama_explore_directory(self, status: Dict):
        """Abre el directorio de modelos de Ollama"""
        print("\n📁 EXPLORAR DIRECTORIO:")

        if status['models_dir'].exists():
            try:
                result = self.safe_run_command(['open', str(status['models_dir'])])
                if result['success']:
                    self.print_success(f"Abriendo directorio: {status['models_dir']}")
                else:
                    print(f"📁 Directorio: {status['models_dir']}")
                    print("(No se pudo abrir automáticamente)")
            except Exception:
                print(f"📁 Directorio: {status['models_dir']}")
        else:
            self.print_warning("El directorio de Ollama no existe")

        self.wait_for_user()

    def _ollama_remove_all(self, status: Dict):
        """Elimina todos los modelos de Ollama"""
        if not status['models']:
            self.print_info("No hay modelos para eliminar")
            self.wait_for_user()
            return

        print(f"\n🚨 ELIMINAR TODOS LOS MODELOS ({len(status['models'])} modelos)")
        for model in status['models']:
            print(f"   - {model['full_name']}")

        if self.confirm_action("Eliminar TODOS los modelos de Ollama", "high"):
            self._remove_all_ollama_models(status)

        self.wait_for_user()

    def _remove_all_ollama_models(self, status: Dict):
        """Elimina todos los modelos (función auxiliar)"""
        total_removed = 0
        for model in status['models']:
            result = self.safe_run_command(['ollama', 'rm', model['full_name']])
            if result['success']:
                self.print_success(f"Eliminado: {model['full_name']}")
                total_removed += 1
                self.log_action(f"Ollama: Modelo {model['full_name']} eliminado")
            else:
                self.print_error(f"Error eliminando {model['full_name']}: {result.get('error', 'Error')}")

        if total_removed > 0:
            self.print_success(f"Total eliminados: {total_removed} modelos")

    # ==================== QUICK ACTIONS ====================

    def quick_cleanup_menu(self):
        """Menú de limpieza rápida"""
        while True:
            os.system('clear')
            self.print_header("🚀 LIMPIEZA RÁPIDA")

            print("\n🎯 ACCIONES RÁPIDAS Y SEGURAS:")
            print("1. 🗑️  Limpiar papelera")
            print("2. 🧹 Limpiar cachés básicos")
            print("3. 📋 Limpiar logs antiguos")
            print("4. 💾 Liberar memoria RAM")
            print("5. 🐳 Docker: limpieza básica")
            print("6. 🤖 Ollama: ver modelos")
            print()
            print("🔧 ANÁLISIS:")
            print("7. 📊 Resumen rápido del sistema")
            print("8. 📁 Top 10 archivos más grandes")
            print("9. 💿 Uso de disco por directorio")
            print()
            print("📋 SESIÓN:")
            print("10. 📝 Ver log de acciones")
            print("11. 💾 Generar reporte")
            print()
            print("0. ⬅️  Volver")

            try:
                choice = input("\n🎯 Selecciona una acción: ").strip()
            except KeyboardInterrupt:
                break

            if choice == "1":
                self._quick_empty_trash()
            elif choice == "2":
                self._quick_clean_caches()
            elif choice == "3":
                self._quick_clean_logs()
            elif choice == "4":
                self._quick_free_memory()
            elif choice == "5":
                self._quick_docker_cleanup()
            elif choice == "6":
                self._quick_ollama_status()
            elif choice == "7":
                self._quick_system_summary()
            elif choice == "8":
                self._quick_large_files()
            elif choice == "9":
                self._quick_disk_usage()
            elif choice == "10":
                self._show_session_log()
            elif choice == "11":
                self._generate_report()
            elif choice == "0":
                break
            else:
                self.print_error("Opción inválida")
                time.sleep(1)

    def _quick_empty_trash(self):
        """Vacía la papelera rápidamente"""
        trash_dir = self.home / ".Trash"

        if not trash_dir.exists():
            self.print_info("La papelera ya está vacía")
            self.wait_for_user()
            return

        try:
            items = list(trash_dir.iterdir())
            if not items:
                self.print_info("La papelera ya está vacía")
                self.wait_for_user()
                return

            total_size = sum(item.stat().st_size if item.is_file() else 0 for item in items)

            print(f"\n🗑️  PAPELERA:")
            print(f"   Elementos: {len(items)}")
            print(f"   Tamaño estimado: {self.format_bytes(total_size)}")

            if self.confirm_action("Vaciar la papelera"):
                for item in items:
                    try:
                        if item.is_file():
                            item.unlink()
                        elif item.is_dir():
                            shutil.rmtree(item)
                    except Exception as e:
                        self.print_error(f"Error eliminando {item.name}: {e}")

                self.print_success("Papelera vaciada")
                self.log_action(f"Papelera vaciada", total_size)
        except Exception as e:
            self.print_error(f"Error accediendo a la papelera: {e}")

        self.wait_for_user()

    def _quick_clean_caches(self):
        """Limpia cachés básicos de forma segura"""
        print("\n🧹 LIMPIEZA DE CACHÉS BÁSICOS:")

        cache_dirs = [
            ("Usuario", self.home / "Library/Caches"),
            ("Sistema", Path("/System/Library/Caches")),
            ("Logs", self.home / "Library/Logs")
        ]

        total_cleaned = 0

        for name, cache_dir in cache_dirs:
            if not cache_dir.exists():
                continue

            print(f"\n📁 Analizando cachés de {name}...")

            try:
                # Buscar directorios de caché seguros para limpiar
                safe_to_clean = []
                for item in cache_dir.iterdir():
                    if item.is_dir():
                        # Evitar cachés críticos del sistema
                        if not any(critical in item.name.lower() for critical in
                                 ['dock', 'finder', 'spotlight', 'kernel', 'system']):
                            safe_to_clean.append(item)

                if safe_to_clean:
                    print(f"   Encontrados {len(safe_to_clean)} directorios seguros para limpiar")

                    if self.confirm_action(f"Limpiar cachés seguros de {name}"):
                        for item in safe_to_clean:
                            try:
                                size_before = sum(f.stat().st_size for f in item.rglob('*') if f.is_file())
                                shutil.rmtree(item)
                                total_cleaned += size_before
                                print(f"   ✅ {item.name}")
                            except Exception as e:
                                print(f"   ❌ Error en {item.name}: {e}")
                else:
                    print(f"   No hay cachés seguros para limpiar en {name}")

            except PermissionError:
                print(f"   ⚠️  Sin permisos para acceder a {name}")
            except Exception as e:
                print(f"   ❌ Error: {e}")

        if total_cleaned > 0:
            self.print_success(f"Cachés limpiados: {self.format_bytes(total_cleaned)}")
            self.log_action("Cachés básicos limpiados", total_cleaned)
        else:
            self.print_info("No se liberó espacio adicional")

        self.wait_for_user()

    def _quick_clean_logs(self):
        """Limpia logs antiguos"""
        print("\n📋 LIMPIEZA DE LOGS ANTIGUOS:")

        log_dirs = [
            self.home / "Library/Logs",
            Path("/var/log"),
            Path("/Library/Logs")
        ]

        total_cleaned = 0
        cutoff_date = datetime.now().timestamp() - (7 * 24 * 3600)  # 7 días

        for log_dir in log_dirs:
            if not log_dir.exists():
                continue

            print(f"\n📁 Analizando logs en {log_dir}...")

            try:
                old_logs = []
                for log_file in log_dir.rglob('*.log*'):
                    if log_file.is_file():
                        try:
                            if log_file.stat().st_mtime < cutoff_date:
                                old_logs.append(log_file)
                        except OSError:
                            continue

                if old_logs:
                    total_size = sum(f.stat().st_size for f in old_logs)
                    print(f"   Encontrados {len(old_logs)} logs antiguos ({self.format_bytes(total_size)})")

                    if self.confirm_action(f"Eliminar logs de más de 7 días"):
                        for log_file in old_logs:
                            try:
                                size = log_file.stat().st_size
                                log_file.unlink()
                                total_cleaned += size
                            except Exception as e:
                                print(f"   ❌ Error en {log_file.name}: {e}")

                        self.print_success(f"Logs eliminados de {log_dir}")
                else:
                    print(f"   No hay logs antiguos para eliminar")

            except PermissionError:
                print(f"   ⚠️  Sin permisos para acceder a {log_dir}")
            except Exception as e:
                print(f"   ❌ Error: {e}")

        if total_cleaned > 0:
            self.print_success(f"Logs limpiados: {self.format_bytes(total_cleaned)}")
            self.log_action("Logs antiguos limpiados", total_cleaned)
        else:
            self.print_info("No se encontraron logs antiguos para eliminar")

        self.wait_for_user()

    def _quick_free_memory(self):
        """Libera memoria RAM"""
        print("\n💾 LIBERANDO MEMORIA RAM:")

        if self.confirm_action("Ejecutar comando de liberación de memoria (requiere sudo)"):
            print("🔄 Ejecutando purge...")
            result = self.safe_run_command(['sudo', 'purge'], timeout=60)

            if result['success']:
                self.print_success("Memoria liberada exitosamente")
                self.log_action("Memoria RAM liberada")
            else:
                self.print_error(f"Error: {result.get('error', 'Comando falló')}")

        self.wait_for_user()

    def _quick_docker_cleanup(self):
        """Limpieza rápida de Docker"""
        print("\n🐳 DOCKER LIMPIEZA RÁPIDA:")

        status = self.docker_status()
        if not status['installed']:
            self.print_error("Docker no está instalado")
            self.wait_for_user()
            return

        if not status['running']:
            self.print_warning("Docker no está corriendo")
            self.wait_for_user()
            return

        print(f"   Estado: Funcionando")
        print(f"   Contenedores parados: {status['containers']['stopped']}")
        print(f"   Total imágenes: {status['images']['total']}")

        if self.confirm_action("Ejecutar limpieza básica de Docker (contenedores parados + imágenes dangling)"):
            result = self.safe_run_command(['docker', 'system', 'prune', '-f'])
            if result['success']:
                self.print_success("Docker limpiado")
                print(result['stdout'])
                self.log_action("Docker: limpieza básica ejecutada")
            else:
                self.print_error(f"Error: {result.get('error', 'Comando falló')}")

        self.wait_for_user()

    def _quick_ollama_status(self):
        """Estado rápido de Ollama"""
        print("\n🤖 ESTADO DE OLLAMA:")

        status = self.ollama_status()

        if not status['installed']:
            self.print_error("Ollama no está instalado")
        elif not status['running']:
            self.print_warning("Ollama no responde")
        else:
            self.print_success("Ollama funcionando")
            print(f"   Modelos instalados: {len(status['models'])}")
            print(f"   Tamaño total: {self.format_bytes(status['models_size'])}")

            if status['models']:
                print(f"\n   📋 Modelos:")
                for model in status['models'][:3]:
                    print(f"      - {model['full_name']} ({model['size']})")
                if len(status['models']) > 3:
                    print(f"      ... y {len(status['models']) - 3} más")

        self.wait_for_user()

    def _quick_system_summary(self):
        """Resumen rápido del sistema"""
        print("\n📊 RESUMEN DEL SISTEMA:")

        # Uso de disco
        result = self.safe_run_command(['df', '-h', '/'])
        if result['success']:
            lines = result['stdout'].strip().split('\n')
            if len(lines) > 1:
                parts = lines[1].split()
                if len(parts) >= 4:
                    print(f"   💿 Disco: {parts[2]} usados de {parts[1]} ({parts[4]} de uso)")

        # Memoria
        try:
            import psutil
            memory = psutil.virtual_memory()
            print(f"   💾 Memoria: {memory.percent:.1f}% usada ({self.format_bytes(memory.used)}/{self.format_bytes(memory.total)})")
        except ImportError:
            print("   💾 Memoria: (psutil no disponible)")

        # Docker
        docker_status = self.docker_status()
        docker_emoji = "✅" if docker_status['running'] else "❌" if docker_status['installed'] else "⭕"
        print(f"   🐳 Docker: {docker_emoji} {'Corriendo' if docker_status['running'] else 'Parado' if docker_status['installed'] else 'No instalado'}")
        if docker_status['running']:
            print(f"      - {docker_status['containers']['total']} contenedores, {docker_status['images']['total']} imágenes")

        # Ollama
        ollama_status = self.ollama_status()
        ollama_emoji = "✅" if ollama_status['running'] else "❌" if ollama_status['installed'] else "⭕"
        print(f"   🤖 Ollama: {ollama_emoji} {'Corriendo' if ollama_status['running'] else 'Parado' if ollama_status['installed'] else 'No instalado'}")
        if ollama_status['running']:
            print(f"      - {len(ollama_status['models'])} modelos ({self.format_bytes(ollama_status['models_size'])})")

        self.wait_for_user()

    def _quick_large_files(self):
        """Encuentra archivos grandes rápidamente"""
        print("\n📁 TOP 10 ARCHIVOS MÁS GRANDES:")
        print("Buscando en directorios principales...")

        search_dirs = [
            self.home / "Downloads",
            self.home / "Desktop",
            self.home / "Documents",
            self.home / "Library"
        ]

        large_files = []

        for search_dir in search_dirs:
            if not search_dir.exists():
                continue

            print(f"   Buscando en {search_dir.name}...")

            try:
                for file_path in search_dir.rglob('*'):
                    if file_path.is_file():
                        try:
                            size = file_path.stat().st_size
                            if size > 100 * 1024 * 1024:  # > 100MB
                                large_files.append({
                                    'path': str(file_path),
                                    'size': size,
                                    'name': file_path.name
                                })
                        except (OSError, FileNotFoundError):
                            continue
            except PermissionError:
                print(f"   ⚠️  Sin permisos para {search_dir}")

        large_files.sort(key=lambda x: x['size'], reverse=True)

        print(f"\n📋 ARCHIVOS GRANDES ENCONTRADOS:")
        for i, file_info in enumerate(large_files[:10], 1):
            print(f"   {i:2d}. {self.format_bytes(file_info['size']):>8} - {file_info['name']}")
            print(f"       {file_info['path']}")

        if len(large_files) > 10:
            remaining_size = sum(f['size'] for f in large_files[10:])
            print(f"\n   ... y {len(large_files)-10} archivos más ({self.format_bytes(remaining_size)})")

        self.wait_for_user()

    def _quick_disk_usage(self):
        """Muestra uso de disco por directorio"""
        print("\n💿 USO DE DISCO POR DIRECTORIO:")

        home_dirs = [
            "Library", "Downloads", "Documents", "Desktop",
            "Movies", "Music", "Pictures", "Applications"
        ]

        print("   Analizando directorios principales...")

        dir_sizes = []
        for dir_name in home_dirs:
            dir_path = self.home / dir_name
            if dir_path.exists():
                try:
                    result = self.safe_run_command(['du', '-sh', str(dir_path)], timeout=30)
                    if result['success']:
                        size_str = result['stdout'].split()[0]
                        dir_sizes.append((dir_name, size_str))
                except Exception:
                    dir_sizes.append((dir_name, "Error"))

        print(f"\n📊 TAMAÑOS:")
        for dir_name, size in dir_sizes:
            print(f"   {dir_name:<15}: {size:>10}")

        self.wait_for_user()

    def _show_session_log(self):
        """Muestra el log de la sesión actual"""
        print(f"\n📝 LOG DE SESIÓN ACTUAL:")
        print(f"Total liberado: {self.format_bytes(self.total_freed)}")
        print()

        if self.session_log:
            for i, entry in enumerate(self.session_log, 1):
                freed_text = f" ({self.format_bytes(entry['size_freed'])})" if entry['size_freed'] > 0 else ""
                print(f"   {i:2d}. {entry['timestamp']} - {entry['action']}{freed_text}")
        else:
            print("   No se han realizado acciones en esta sesión")

        self.wait_for_user()

    def _generate_report(self):
        """Genera un reporte de la sesión"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = self.home / f"smart_cleaner_report_{timestamp}.txt"

        print(f"\n💾 GENERANDO REPORTE...")

        try:
            with open(report_file, 'w') as f:
                f.write(f"Mac Smart Cleaner - Reporte de Sesión\n")
                f.write(f"{'='*50}\n")
                f.write(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Total liberado: {self.format_bytes(self.total_freed)}\n")
                f.write(f"Acciones realizadas: {len(self.session_log)}\n\n")

                if self.session_log:
                    f.write("Historial de acciones:\n")
                    f.write("-" * 30 + "\n")
                    for entry in self.session_log:
                        freed_text = f" ({self.format_bytes(entry['size_freed'])})" if entry['size_freed'] > 0 else ""
                        f.write(f"{entry['timestamp']} - {entry['action']}{freed_text}\n")
                else:
                    f.write("No se realizaron acciones en esta sesión.\n")

                # Agregar estado del sistema
                f.write(f"\nEstado del sistema al finalizar:\n")
                f.write("-" * 30 + "\n")

                # Docker
                docker_status = self.docker_status()
                f.write(f"Docker: {'Corriendo' if docker_status['running'] else 'Parado/No instalado'}\n")
                if docker_status['running']:
                    f.write(f"  - Contenedores: {docker_status['containers']['total']} total, {docker_status['containers']['stopped']} parados\n")
                    f.write(f"  - Imágenes: {docker_status['images']['total']}\n")

                # Ollama
                ollama_status = self.ollama_status()
                f.write(f"Ollama: {'Corriendo' if ollama_status['running'] else 'Parado/No instalado'}\n")
                if ollama_status['running']:
                    f.write(f"  - Modelos: {len(ollama_status['models'])} ({self.format_bytes(ollama_status['models_size'])})\n")

            self.print_success(f"Reporte guardado: {report_file}")
        except Exception as e:
            self.print_error(f"Error generando reporte: {e}")

        self.wait_for_user()

    # ==================== MAIN MENU ====================

    def main_menu(self):
        """Menú principal simplificado"""
        while True:
            try:
                os.system('clear')
                self.print_header("🧹 MAC SMART CLEANER")

                print(f"\n💡 HERRAMIENTA INTELIGENTE Y SEGURA")
                print(f"📊 Sesión actual: {len(self.session_log)} acciones, {self.format_bytes(self.total_freed)} liberados")

                print(f"\n🎯 ¿QUÉ QUIERES HACER?")
                print("1. 🚀 Limpieza rápida (acciones seguras)")
                print("2. 🐳 Gestionar Docker (contenedores, imágenes, limpieza)")
                print("3. 🤖 Gestionar Ollama (modelos de IA)")
                print("4. 📊 Ver estado del sistema")
                print("5. 📝 Ver log de esta sesión")
                print()
                print("0. 🚪 Salir")

                choice = input("\n🎯 Selecciona una opción: ").strip()

                if choice == "1":
                    self.quick_cleanup_menu()
                elif choice == "2":
                    self.docker_menu()
                elif choice == "3":
                    self.ollama_menu()
                elif choice == "4":
                    self._quick_system_summary()
                elif choice == "5":
                    self._show_session_log()
                elif choice == "0":
                    print("\n👋 ¡Gracias por usar Mac Smart Cleaner!")
                    if self.session_log:
                        print(f"✅ Realizaste {len(self.session_log)} acciones y liberaste {self.format_bytes(self.total_freed)}")
                    break
                else:
                    self.print_error("Opción inválida")
                    time.sleep(1)

            except KeyboardInterrupt:
                print("\n\n👋 Salida por interrupción del usuario")
                break
            except Exception as e:
                self.print_error(f"Error inesperado: {e}")
                self.wait_for_user()

def main():
    def signal_handler(sig, frame):
        print('\n\n👋 Salida por señal del sistema')
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    cleaner = SmartCleaner()
    cleaner.main_menu()

if __name__ == "__main__":
    main()