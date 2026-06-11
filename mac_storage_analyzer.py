#!/usr/bin/env python3
"""
Analizador de almacenamiento para Mac M1
Proporciona información detallada sobre el uso del disco y directorios más pesados
"""

import os
import subprocess
import json
from pathlib import Path
import argparse
from typing import Dict, List, Tuple

def get_disk_usage():
    """Obtiene información de uso del disco"""
    try:
        result = subprocess.run(['df', '-h'], capture_output=True, text=True)
        return result.stdout
    except subprocess.SubprocessError as e:
        return f"Error obteniendo uso del disco: {e}"

def get_directory_size(path: str) -> int:
    """Calcula el tamaño de un directorio en bytes"""
    total_size = 0
    try:
        for dirpath, dirnames, filenames in os.walk(path):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                try:
                    total_size += os.path.getsize(filepath)
                except (OSError, FileNotFoundError):
                    continue
    except PermissionError:
        pass
    return total_size

def format_bytes(bytes_size: int) -> str:
    """Convierte bytes a formato legible"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.1f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.1f} PB"

def analyze_directory(directory: str, max_depth: int = 1) -> List[Tuple[str, int]]:
    """Analiza los subdirectorios de un directorio dado"""
    items = []
    try:
        path = Path(directory)
        if not path.exists() or not path.is_dir():
            return items

        for item in path.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                size = get_directory_size(str(item))
                items.append((str(item), size))
    except PermissionError:
        pass

    return sorted(items, key=lambda x: x[1], reverse=True)

def get_system_storage_info():
    """Obtiene información del almacenamiento del sistema usando system_profiler"""
    try:
        result = subprocess.run(['system_profiler', 'SPStorageDataType', '-json'],
                              capture_output=True, text=True)
        if result.returncode == 0:
            data = json.loads(result.stdout)
            return data
    except (subprocess.SubprocessError, json.JSONDecodeError):
        pass
    return None

def analyze_large_files(directory: str, min_size_mb: int = 100) -> List[Tuple[str, int]]:
    """Encuentra archivos grandes en un directorio"""
    large_files = []
    min_size_bytes = min_size_mb * 1024 * 1024

    try:
        for root, dirs, files in os.walk(directory):
            for file in files:
                filepath = os.path.join(root, file)
                try:
                    size = os.path.getsize(filepath)
                    if size >= min_size_bytes:
                        large_files.append((filepath, size))
                except (OSError, FileNotFoundError):
                    continue
    except PermissionError:
        pass

    return sorted(large_files, key=lambda x: x[1], reverse=True)

def main():
    parser = argparse.ArgumentParser(description='Analizador de almacenamiento para Mac M1')
    parser.add_argument('--directory', '-d', default=os.path.expanduser('~'),
                       help='Directorio a analizar (por defecto: directorio home)')
    parser.add_argument('--large-files', '-f', type=int, default=100,
                       help='Tamaño mínimo en MB para archivos grandes (por defecto: 100)')
    parser.add_argument('--top', '-t', type=int, default=10,
                       help='Número de elementos a mostrar (por defecto: 10)')

    args = parser.parse_args()

    print("🔍 ANALIZADOR DE ALMACENAMIENTO MAC M1")
    print("=" * 50)

    # Información general del disco
    print("\n📊 USO GENERAL DEL DISCO:")
    print(get_disk_usage())

    # Información del sistema
    storage_info = get_system_storage_info()
    if storage_info:
        print("\n💾 INFORMACIÓN DEL ALMACENAMIENTO:")
        for storage in storage_info.get('SPStorageDataType', []):
            print(f"  Dispositivo: {storage.get('_name', 'N/A')}")
            print(f"  Capacidad: {storage.get('size_in_bytes', 'N/A')}")
            if 'free_space_in_bytes' in storage:
                free_gb = int(storage['free_space_in_bytes']) / (1024**3)
                print(f"  Espacio libre: {free_gb:.1f} GB")

    # Análisis de directorios principales
    print(f"\n📁 DIRECTORIOS MÁS PESADOS EN {args.directory}:")
    directories = analyze_directory(args.directory)
    for i, (dir_path, size) in enumerate(directories[:args.top]):
        print(f"  {i+1:2d}. {format_bytes(size):>10} - {dir_path}")

    # Directorios específicos importantes en Mac
    important_dirs = [
        "~/Library",
        "~/Downloads",
        "~/Documents",
        "~/Desktop",
        "~/Movies",
        "~/Music",
        "~/Pictures"
    ]

    print("\n🏠 ANÁLISIS DE DIRECTORIOS IMPORTANTES:")
    for dir_name in important_dirs:
        expanded_dir = os.path.expanduser(dir_name)
        if os.path.exists(expanded_dir):
            size = get_directory_size(expanded_dir)
            print(f"  {format_bytes(size):>10} - {dir_name}")

    # Archivos grandes
    print(f"\n📄 ARCHIVOS GRANDES (>{args.large_files}MB) EN {args.directory}:")
    large_files = analyze_large_files(args.directory, args.large_files)
    for i, (filepath, size) in enumerate(large_files[:args.top]):
        print(f"  {i+1:2d}. {format_bytes(size):>10} - {filepath}")

    # Cachés y archivos temporales comunes
    cache_dirs = [
        "~/Library/Caches",
        "~/Library/Application Support",
        "~/Library/Logs",
        "/tmp",
        "/var/tmp"
    ]

    print("\n🗑️  CACHÉS Y ARCHIVOS TEMPORALES:")
    for cache_dir in cache_dirs:
        expanded_cache = os.path.expanduser(cache_dir)
        if os.path.exists(expanded_cache):
            size = get_directory_size(expanded_cache)
            print(f"  {format_bytes(size):>10} - {cache_dir}")

    print("\n✅ Análisis completado")

if __name__ == "__main__":
    main()