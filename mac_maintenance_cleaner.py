#!/usr/bin/env python3
"""
Script de mantenimiento y limpieza para Mac M1
Limpia cachés, logs, archivos temporales y optimiza el sistema
"""

import os
import subprocess
import shutil
import time
import argparse
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple, Optional

class MacCleaner:
    def __init__(self):
        self.home = Path.home()
        self.cleaned_size = 0
        self.cleaned_files = 0
        self.errors = []

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

    def clean_system_caches(self, dry_run: bool = True) -> Dict:
        """Limpia cachés del sistema"""
        cache_dirs = [
            self.home / "Library/Caches",
            self.home / "Library/Application Support/CrashReporter",
            self.home / "Library/WebKit",
            Path("/System/Library/Caches"),
            Path("/Library/Caches"),
        ]

        results = []
        total_cleaned = 0

        for cache_dir in cache_dirs:
            if not cache_dir.exists():
                continue

            try:
                initial_size = self.get_directory_size(cache_dir)

                # Excepciones: no borrar estos cachés importantes
                skip_dirs = {'com.apple.dock', 'com.apple.finder', 'com.apple.spotlight'}

                files_to_clean = []
                for item in cache_dir.iterdir():
                    if item.name not in skip_dirs:
                        if item.is_file() or (item.is_dir() and item.name.startswith('com.')):
                            files_to_clean.append(item)

                cleaned_size = 0
                if not dry_run:
                    for item in files_to_clean:
                        try:
                            if item.is_file():
                                cleaned_size += item.stat().st_size
                                item.unlink()
                            elif item.is_dir():
                                shutil.rmtree(item)
                        except (OSError, PermissionError) as e:
                            self.errors.append(f"Error limpiando {item}: {e}")

                results.append({
                    'path': str(cache_dir),
                    'initial_size': initial_size,
                    'cleaned_size': cleaned_size,
                    'files_found': len(files_to_clean)
                })
                total_cleaned += cleaned_size

            except PermissionError:
                self.errors.append(f"Sin permisos para acceder a {cache_dir}")

        return {
            'total_cleaned': total_cleaned,
            'results': results
        }

    def clean_logs(self, days_old: int = 7, dry_run: bool = True) -> Dict:
        """Limpia archivos de log antiguos"""
        log_dirs = [
            self.home / "Library/Logs",
            Path("/var/log"),
            Path("/Library/Logs"),
        ]

        results = []
        total_cleaned = 0
        cutoff_date = datetime.now() - timedelta(days=days_old)

        for log_dir in log_dirs:
            if not log_dir.exists():
                continue

            try:
                cleaned_size = 0
                cleaned_count = 0

                for log_file in log_dir.rglob('*.log*'):
                    if log_file.is_file():
                        try:
                            file_time = datetime.fromtimestamp(log_file.stat().st_mtime)
                            if file_time < cutoff_date:
                                file_size = log_file.stat().st_size
                                if not dry_run:
                                    log_file.unlink()
                                cleaned_size += file_size
                                cleaned_count += 1
                        except (OSError, PermissionError):
                            continue

                results.append({
                    'path': str(log_dir),
                    'cleaned_size': cleaned_size,
                    'files_cleaned': cleaned_count
                })
                total_cleaned += cleaned_size

            except PermissionError:
                self.errors.append(f"Sin permisos para acceder a {log_dir}")

        return {
            'total_cleaned': total_cleaned,
            'results': results
        }

    def clean_downloads_duplicates(self, dry_run: bool = True) -> Dict:
        """Encuentra y elimina duplicados en Downloads"""
        downloads_dir = self.home / "Downloads"
        if not downloads_dir.exists():
            return {'total_cleaned': 0, 'duplicates': []}

        # Buscar archivos con patrones de duplicados
        duplicate_patterns = [
            ' (1)', ' (2)', ' (3)', ' copy', ' Copy',
            '-1', '-2', '-3', '_copy', '_Copy'
        ]

        duplicates = []
        total_size = 0

        try:
            for file_path in downloads_dir.iterdir():
                if file_path.is_file():
                    filename = file_path.name
                    for pattern in duplicate_patterns:
                        if pattern in filename:
                            try:
                                size = file_path.stat().st_size
                                duplicates.append({
                                    'path': str(file_path),
                                    'size': size,
                                    'name': filename
                                })
                                total_size += size

                                if not dry_run:
                                    file_path.unlink()
                            except (OSError, PermissionError):
                                continue
                            break

        except PermissionError:
            self.errors.append(f"Sin permisos para acceder a {downloads_dir}")

        return {
            'total_cleaned': total_size,
            'duplicates': duplicates
        }

    def clean_trash(self, dry_run: bool = True) -> Dict:
        """Vacía la papelera"""
        trash_dir = self.home / ".Trash"
        if not trash_dir.exists():
            return {'total_cleaned': 0, 'files_count': 0}

        try:
            initial_size = self.get_directory_size(trash_dir)
            files_count = len(list(trash_dir.iterdir()))

            if not dry_run:
                for item in trash_dir.iterdir():
                    try:
                        if item.is_file():
                            item.unlink()
                        elif item.is_dir():
                            shutil.rmtree(item)
                    except (OSError, PermissionError):
                        continue

            return {
                'total_cleaned': initial_size if not dry_run else 0,
                'files_count': files_count,
                'estimated_size': initial_size
            }

        except PermissionError:
            self.errors.append("Sin permisos para vaciar la papelera")
            return {'total_cleaned': 0, 'files_count': 0}

    def clean_browser_data(self, dry_run: bool = True) -> Dict:
        """Limpia datos de navegadores (cachés, historiales antiguos)"""
        browser_paths = {
            'Chrome': self.home / "Library/Application Support/Google/Chrome/Default/Service Worker",
            'Safari': self.home / "Library/Caches/com.apple.Safari",
            'Firefox': self.home / "Library/Application Support/Firefox/Profiles",
            'Edge': self.home / "Library/Application Support/Microsoft Edge/Default/Service Worker",
        }

        results = []
        total_cleaned = 0

        for browser, path in browser_paths.items():
            if path.exists():
                try:
                    initial_size = self.get_directory_size(path)
                    cleaned_size = 0

                    if not dry_run and path.name in ['Service Worker', 'com.apple.Safari']:
                        try:
                            if path.is_dir():
                                shutil.rmtree(path)
                                cleaned_size = initial_size
                        except (OSError, PermissionError):
                            pass

                    results.append({
                        'browser': browser,
                        'path': str(path),
                        'initial_size': initial_size,
                        'cleaned_size': cleaned_size
                    })
                    total_cleaned += cleaned_size

                except PermissionError:
                    self.errors.append(f"Sin permisos para limpiar {browser}")

        return {
            'total_cleaned': total_cleaned,
            'results': results
        }

    def optimize_storage(self) -> Dict:
        """Ejecuta comandos de optimización del sistema"""
        commands = [
            (['sudo', 'purge'], "Purgar memoria y cachés"),
            (['sudo', 'periodic', 'daily'], "Ejecutar mantenimiento diario"),
            (['sudo', 'periodic', 'weekly'], "Ejecutar mantenimiento semanal"),
            (['sudo', 'periodic', 'monthly'], "Ejecutar mantenimiento mensual"),
        ]

        results = []
        for cmd, description in commands:
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
                results.append({
                    'command': ' '.join(cmd),
                    'description': description,
                    'success': result.returncode == 0,
                    'output': result.stdout[:100] if result.stdout else "Completado"
                })
            except (subprocess.TimeoutExpired, subprocess.SubprocessError) as e:
                results.append({
                    'command': ' '.join(cmd),
                    'description': description,
                    'success': False,
                    'output': str(e)
                })

        return {'results': results}

    def find_large_files(self, min_size_mb: int = 500) -> List[Dict]:
        """Encuentra archivos grandes que pueden ser eliminados"""
        large_files = []
        min_size = min_size_mb * 1024 * 1024

        search_paths = [
            self.home / "Downloads",
            self.home / "Desktop",
            self.home / "Documents",
            self.home / "Movies",
            self.home / "Library" / "Application Support",
        ]

        for search_path in search_paths:
            if search_path.exists():
                try:
                    for file_path in search_path.rglob('*'):
                        if file_path.is_file():
                            try:
                                size = file_path.stat().st_size
                                if size >= min_size:
                                    # Identificar tipos que pueden ser seguros de eliminar
                                    potentially_safe = any(ext in file_path.suffix.lower()
                                                         for ext in ['.log', '.tmp', '.cache', '.old', '.bak'])

                                    large_files.append({
                                        'path': str(file_path),
                                        'size': size,
                                        'size_mb': size / (1024 * 1024),
                                        'potentially_safe': potentially_safe,
                                        'extension': file_path.suffix.lower()
                                    })
                            except (OSError, FileNotFoundError):
                                continue
                except PermissionError:
                    continue

        return sorted(large_files, key=lambda x: x['size'], reverse=True)

    def generate_cleanup_report(self, results: Dict) -> str:
        """Genera un reporte detallado de la limpieza"""
        report = []
        report.append("🧹 REPORTE DE LIMPIEZA MAC M1")
        report.append("=" * 50)
        report.append(f"📅 Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")

        total_cleaned = 0

        # Cachés del sistema
        if 'caches' in results:
            cache_size = results['caches']['total_cleaned']
            total_cleaned += cache_size
            report.append(f"📂 Cachés del sistema: {self.format_bytes(cache_size)}")

        # Logs
        if 'logs' in results:
            log_size = results['logs']['total_cleaned']
            total_cleaned += log_size
            report.append(f"📋 Archivos de log: {self.format_bytes(log_size)}")

        # Duplicados
        if 'duplicates' in results:
            dup_size = results['duplicates']['total_cleaned']
            total_cleaned += dup_size
            report.append(f"📄 Archivos duplicados: {self.format_bytes(dup_size)}")

        # Papelera
        if 'trash' in results:
            trash_size = results['trash']['total_cleaned']
            total_cleaned += trash_size
            report.append(f"🗑️  Papelera: {self.format_bytes(trash_size)}")

        # Navegadores
        if 'browsers' in results:
            browser_size = results['browsers']['total_cleaned']
            total_cleaned += browser_size
            report.append(f"🌐 Datos de navegadores: {self.format_bytes(browser_size)}")

        report.append("")
        report.append(f"💾 TOTAL LIBERADO: {self.format_bytes(total_cleaned)}")
        report.append("")

        # Errores
        if self.errors:
            report.append("⚠️  ERRORES ENCONTRADOS:")
            for error in self.errors[:5]:  # Solo primeros 5 errores
                report.append(f"   {error}")
            if len(self.errors) > 5:
                report.append(f"   ... y {len(self.errors) - 5} errores más")

        return "\n".join(report)

def main():
    parser = argparse.ArgumentParser(description='Limpiador y mantenimiento para Mac M1')
    parser.add_argument('--dry-run', '-n', action='store_true',
                       help='Solo mostrar qué se limpiaría sin hacer cambios')
    parser.add_argument('--caches', '-c', action='store_true',
                       help='Limpiar cachés del sistema')
    parser.add_argument('--logs', '-l', action='store_true',
                       help='Limpiar archivos de log antiguos')
    parser.add_argument('--duplicates', '-d', action='store_true',
                       help='Limpiar archivos duplicados en Downloads')
    parser.add_argument('--trash', '-t', action='store_true',
                       help='Vaciar papelera')
    parser.add_argument('--browsers', '-b', action='store_true',
                       help='Limpiar datos de navegadores')
    parser.add_argument('--all', '-a', action='store_true',
                       help='Ejecutar todas las limpiezas')
    parser.add_argument('--optimize', '-o', action='store_true',
                       help='Optimizar sistema')
    parser.add_argument('--find-large', '-f', type=int, default=500,
                       help='Encontrar archivos grandes (MB, por defecto: 500)')
    parser.add_argument('--report', '-r', type=str,
                       help='Guardar reporte en archivo')
    parser.add_argument('--log-days', type=int, default=7,
                       help='Días de antigüedad para logs (por defecto: 7)')

    args = parser.parse_args()

    cleaner = MacCleaner()
    results = {}

    if args.dry_run:
        print("🔍 MODO SIMULACIÓN - No se realizarán cambios reales")
        print("=" * 50)

    # Ejecutar limpiezas seleccionadas
    if args.all or args.caches:
        print("🧹 Limpiando cachés del sistema...")
        results['caches'] = cleaner.clean_system_caches(args.dry_run)
        print(f"   Cachés: {cleaner.format_bytes(results['caches']['total_cleaned'])}")

    if args.all or args.logs:
        print("📋 Limpiando archivos de log...")
        results['logs'] = cleaner.clean_logs(args.log_days, args.dry_run)
        print(f"   Logs: {cleaner.format_bytes(results['logs']['total_cleaned'])}")

    if args.all or args.duplicates:
        print("📄 Buscando archivos duplicados...")
        results['duplicates'] = cleaner.clean_downloads_duplicates(args.dry_run)
        print(f"   Duplicados: {cleaner.format_bytes(results['duplicates']['total_cleaned'])}")

    if args.all or args.trash:
        print("🗑️  Vaciando papelera...")
        results['trash'] = cleaner.clean_trash(args.dry_run)
        print(f"   Papelera: {cleaner.format_bytes(results['trash']['total_cleaned'])}")

    if args.all or args.browsers:
        print("🌐 Limpiando datos de navegadores...")
        results['browsers'] = cleaner.clean_browser_data(args.dry_run)
        print(f"   Navegadores: {cleaner.format_bytes(results['browsers']['total_cleaned'])}")

    if args.optimize:
        print("⚙️  Optimizando sistema...")
        results['optimization'] = cleaner.optimize_storage()
        optimizations = len([r for r in results['optimization']['results'] if r['success']])
        print(f"   Optimizaciones exitosas: {optimizations}")

    # Buscar archivos grandes
    if args.find_large:
        print(f"\n🔍 ARCHIVOS GRANDES (>{args.find_large}MB):")
        large_files = cleaner.find_large_files(args.find_large)
        for i, file_info in enumerate(large_files[:10]):
            safe_indicator = "🟡" if file_info['potentially_safe'] else "🔴"
            print(f"  {i+1:2d}. {safe_indicator} {file_info['size_mb']:>8.1f}MB - {file_info['path']}")

        if len(large_files) > 10:
            remaining_size = sum(f['size'] for f in large_files[10:])
            print(f"      ... y {len(large_files)-10} archivos más ({cleaner.format_bytes(remaining_size)})")

    # Generar reporte
    if results:
        report = cleaner.generate_cleanup_report(results)
        print(f"\n{report}")

        if args.report:
            with open(args.report, 'w') as f:
                f.write(report)
                f.write(f"\n\nDetalles completos:\n{json.dumps(results, indent=2, default=str)}")
            print(f"\n💾 Reporte guardado en: {args.report}")

    # Mostrar recomendaciones específicas basadas en los resultados del análisis previo
    print(f"\n💡 RECOMENDACIONES ESPECÍFICAS:")
    print("   🐳 Docker consume 200GB - considera: docker system prune -a")
    print("   📋 Log de BrowserLock (8.3GB) - revisar configuración de logging")
    print("   🤖 Modelos Ollama (12.8GB) - eliminar modelos no utilizados")
    print("   🌐 Múltiples versiones de Edge - limpiar versiones antiguas")
    print("   📂 17GB en Application Support - revisar aplicaciones no utilizadas")

if __name__ == "__main__":
    main()