#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import hashlib
import os
import shlex
import sys
import json
import argparse
import subprocess
import urllib.request
import zipfile
import shutil
import re
from html.parser import HTMLParser
from pathlib import Path
import datetime
from typing import Optional, Dict
from urllib.error import URLError, HTTPError

from packaging import version

import requests
import tempfile


class PHPVersionManager:
    def __init__(self):
        self.base_php_path = "C:\\"
        self.apache_conf = "C:\\APACHE24\\conf\\httpd.conf"
        self.apache_bin = "C:\\APACHE24\\bin\\httpd.exe"
        self.apache_root = os.path.dirname(os.path.dirname(self.apache_bin))
        self.modules_path = os.path.join(self.apache_root, "modules")
        self.vhosts_path = "C:\\APACHE24\\conf\\extra\\httpd-vhosts.conf"
        self.mappings_file = "C:\\APACHE24\\conf\\php-mappings.json"

        # Versiones disponibles (Thread Safe)
        self.available_versions = {
            "7.1": "C:\\php7.1",
            "7.3": "C:\\php7.3",
            "7.4": "C:\\php7.4",
            "8.0": "C:\\php8.0",
            "8.1": "C:\\php8.1",
            "8.2": "C:\\php8.2",
            "8.3": "C:\\php8.3",
            "8.4": "C:\\php8.4",
            "xampp": "C:\\xampp\\php"
        }

        self.remote_php_versions = None

        # Composer
        self.default_composer_versions = {v: "2.8.10" for v in self.available_versions}

        # Extensiones necesarias
        self.required_extensions = ["openssl", "mbstring", "curl", "intl", "mysqli", "gd", "pdo_mysql"]

    def print_colored(self, text, color, end="\n"):
        """Imprime texto con color"""
        colors = {
            'red': '\033[91m',
            'green': '\033[92m',
            'yellow': '\033[93m',
            'blue': '\033[94m',
            'magenta': '\033[95m',
            'cyan': '\033[96m',
            'gray': '\033[90m',
            'dark_gray': '\033[2m',
            'reset': '\033[0m'
        }

        color_code = colors.get(color, colors['reset'])
        reset_code = colors['reset']
        print(f"{color_code}{text}{reset_code}", end=end)

    def show_help(self):
        """Muestra la ayuda completa del PHP Version Manager"""
        # Colores ANSI para terminal
        GREEN = '\033[92m'
        YELLOW = '\033[93m'
        RESET = '\033[0m'

        print(f"{GREEN}=== PHP Version Manager - Enhanced Multi-Version Support ==={RESET}")
        print("")
        print(f"{YELLOW}Uso básico:{RESET}")
        print("  python php_manager.py -v <version>             Cambiar CLI a una versión específica")
        print("  python php_manager.py -l                       Listar versiones disponibles")
        print("  python php_manager.py --info                   Mostrar información de PHP y Composer")
        print("  python php_manager.py --install -v <v>         Instalar una versión de PHP")
        print("  python php_manager.py --fix-ini -v <v>         Corregir php.ini (openssl, etc.)")
        print("  python php_manager.py --command '<cmd>'        Ejecutar comando PHP")
        print("")
        print(f"{YELLOW}Multi-versión Apache:{RESET}")
        print("  python php_manager.py --setup-multiversion     Configurar Apache para soporte multi-versión")
        print("  python php_manager.py -d <path> -v <v> -a <name>  Mapear directorio a PHP version")
        print("  python php_manager.py --show-mappings          Mostrar mappings actuales")
        print("  python php_manager.py --remove-mapping -a <name>  Eliminar mapping")
        print("")
        print(f"{YELLOW}Ejemplos:{RESET}")
        print("  # Configurar soporte multi-versión")
        print("  python php_manager.py --setup-multiversion")
        print("")
        print("  # Mapear directorios a versiones específicas")
        print("  python php_manager.py -d 'C:\\www\\project1' -v 8.1 -a project1")
        print("  python php_manager.py -d 'C:\\www\\legacy' -v 7.4 -a legacy")
        print("  python php_manager.py -d 'C:\\www\\latest' -v 8.3 -a latest")
        print("")
        print("  # Ver mappings actuales")
        print("  python php_manager.py --show-mappings")
        print("")
        print("  # Cambiar versión CLI")
        print("  python php_manager.py -v 8.1")

    def get_php_versions(self):
        """Lista todas las versiones de PHP disponibles con información detallada"""
        self.print_colored("=== Versiones de PHP Disponibles ===", "green")
        print()

        for version in sorted(self.available_versions.keys()):
            path = self.available_versions[version]
            php_exe = os.path.join(path, "php.exe")

            # Manejo especial para XAMPP
            if version == "xampp":
                try:
                    resolved_path = os.path.realpath(path)
                    php_exe = os.path.join(resolved_path, "php.exe")
                except:
                    pass

            if os.path.exists(php_exe):
                try:
                    # Obtener información de la versión de PHP
                    result = subprocess.run([php_exe, "-v"], capture_output=True, text=True, timeout=10,
                                            stderr=subprocess.DEVNULL)
                    if result.returncode == 0:
                        version_info = result.stdout.split('\n')[0]

                        # Mostrar versión y path
                        print("  ✓ ", end="")
                        self.print_colored(version, "green", end="")
                        self.print_colored(f" - {path}", "gray")
                        self.print_colored(f"    {version_info}", "dark_gray")

                        # Verificar Composer
                        composer_phar = os.path.join(path, "composer.phar")
                        if os.path.exists(composer_phar):
                            try:
                                comp_result = subprocess.run(
                                    [php_exe, composer_phar, "--version", "--no-ansi"],
                                    capture_output=True, text=True, timeout=10, stderr=subprocess.DEVNULL
                                )
                                if comp_result.returncode == 0 and comp_result.stdout.strip():
                                    composer_parts = comp_result.stdout.split()
                                    if len(composer_parts) > 2:
                                        cv = composer_parts[2]
                                        self.print_colored(f"    Composer: v{cv}", "cyan")
                                    else:
                                        self.print_colored("    Composer: instalado (versión no detectada)",
                                                           "dark_gray")
                                else:
                                    self.print_colored("    Composer: instalado (versión no detectada)", "dark_gray")
                            except:
                                self.print_colored("    Composer: instalado (versión no detectada)", "dark_gray")
                        else:
                            self.print_colored("    Composer: no instalado", "yellow")

                        # Verificar extensiones requeridas
                        enabled_extensions = self.get_enabled_extensions(path)
                        print("    Extensions: ", end="")
                        self.print_colored("Extensions: ", "yellow", end="")

                        for ext in self.required_extensions:
                            if ext in enabled_extensions:
                                self.print_colored(f"{ext} ✅ ", "green", end="")
                            else:
                                self.print_colored(f"{ext} ❌ ", "red", end="")
                        print()  # Nueva línea después de las extensiones

                    else:
                        print("  ✗ ", end="")
                        self.print_colored(version, "red", end="")
                        self.print_colored(f" - {path} (Error al ejecutar)", "gray")

                except subprocess.TimeoutExpired:
                    print("  ✗ ", end="")
                    self.print_colored(version, "red", end="")
                    self.print_colored(f" - {path} (Timeout)", "gray")
                except Exception as e:
                    print("  ✗ ", end="")
                    self.print_colored(version, "red", end="")
                    self.print_colored(f" - {path} (Error: {str(e)})", "gray")
            else:
                print("  ✗ ", end="")
                self.print_colored(version, "red", end="")
                self.print_colored(f" - {path} (No instalado)", "gray")

        print()

    def get_enabled_extensions(self, php_path):
        """Obtiene las extensiones habilitadas leyendo php.ini y usando php -m como fallback"""
        # Método 1: Leer php.ini (como en PowerShell)
        enabled_from_ini = self._get_extensions_from_ini(php_path)

        # Método 2: Usar php -m como fallback
        if not enabled_from_ini:
            enabled_from_php = self._get_extensions_from_php(php_path)
            return enabled_from_php

        return enabled_from_ini

    def _get_extensions_from_ini(self, php_path):
        """Lee extensiones desde php.ini"""
        ini_path = os.path.join(php_path, "php.ini")
        if not os.path.exists(ini_path):
            return []

        try:
            with open(ini_path, 'r', encoding='utf-8', errors='ignore') as file:
                lines = file.readlines()
        except:
            return []

        # Filtrar líneas que contienen extension=
        extension_lines = [line.strip() for line in lines
                           if line.strip() and 'extension' in line.lower() and '=' in line]

        enabled = []

        # Mapeo de extensiones a archivos DLL
        ext_to_dll = {
            "openssl": "php_openssl.dll",
            "mbstring": "php_mbstring.dll",
            "curl": "php_curl.dll",
            "intl": "php_intl.dll",
            "zip": "php_zip.dll",
            "gd": "php_gd2.dll",
            "xml": "php_xml.dll",
            "mysqli": "php_mysqli.dll",
            "fileinfo": "php_fileinfo.dll"
        }

        for ext in self.required_extensions:
            dll_name = ext_to_dll.get(ext, f"php_{ext}.dll")

            for line in extension_lines:
                # Saltar líneas comentadas
                if line.startswith(';'):
                    continue

                # Buscar la extensión por nombre de DLL o nombre de extensión
                line_lower = line.lower()
                if (dll_name.lower() in line_lower or
                        f'extension={ext}' in line_lower or
                        f'extension = {ext}' in line_lower):
                    if ext not in enabled:
                        enabled.append(ext)
                    break

        return enabled

    def _get_extensions_from_php(self, php_path):
        """Obtiene extensiones usando php -m como fallback"""
        php_exe = os.path.join(php_path, "php.exe")
        if not os.path.exists(php_exe):
            return []

        try:
            result = subprocess.run(
                [php_exe, "-m"],
                capture_output=True,
                text=True,
                timeout=10,
                stderr=subprocess.DEVNULL
            )
            if result.returncode == 0:
                extensions = []
                lines = result.stdout.strip().split('\n')
                capture_extensions = False

                for line in lines:
                    line = line.strip()
                    if line == "[PHP Modules]":
                        capture_extensions = True
                        continue
                    elif line == "[Zend Modules]":
                        break
                    elif capture_extensions and line and not line.startswith('['):
                        extensions.append(line.lower())

                # Filtrar solo las extensiones que nos interesan
                enabled = []
                for ext in self.required_extensions:
                    if ext.lower() in extensions:
                        enabled.append(ext)

                return enabled
        except:
            return []

    def initialize_php_mappings(self):
        """Inicializa el archivo de mappings de PHP"""
        if not os.path.exists(self.mappings_file):
            # Crear archivo inicial
            initial_mappings = {
                "mappings": {},
                "created": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "version": "1.0"
            }

            # Crear directorio si no existe
            os.makedirs(os.path.dirname(self.mappings_file), exist_ok=True)

            try:
                with open(self.mappings_file, 'w', encoding='utf-8') as f:
                    json.dump(initial_mappings, f, indent=2, ensure_ascii=False)
                self.print_colored(f"✅ Archivo de mappings inicializado: {self.mappings_file}", "green")
            except Exception as e:
                self.print_colored(f"❌ Error creando archivo de mappings: {e}", "red")
                return False
        else:
            # Verificar y corregir estructura del archivo existente
            try:
                with open(self.mappings_file, 'r', encoding='utf-8') as f:
                    content = f.read().strip()

                if not content:
                    raise ValueError("Archivo vacío")

                json_obj = json.loads(content)

                # Verificar si tiene la estructura correcta
                if not isinstance(json_obj, dict):
                    raise ValueError("Estructura incorrecta")

                # Asegurar que existe la propiedad 'mappings'
                if 'mappings' not in json_obj:
                    json_obj['mappings'] = {}
                    # Agregar metadatos si no existen
                    if 'created' not in json_obj:
                        json_obj['created'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    if 'version' not in json_obj:
                        json_obj['version'] = "1.0"

                    # Guardar archivo corregido
                    with open(self.mappings_file, 'w', encoding='utf-8') as f:
                        json.dump(json_obj, f, indent=2, ensure_ascii=False)

                    self.print_colored(f"✅ Estructura de mappings corregida: {self.mappings_file}", "green")

            except (json.JSONDecodeError, ValueError, FileNotFoundError) as e:
                # Si el archivo está corrupto, recrearlo
                self.print_colored(f"⚠️  Archivo de mappings corrupto, recreando...", "yellow")

                initial_mappings = {
                    "mappings": {},
                    "created": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "version": "1.0"
                }

                try:
                    with open(self.mappings_file, 'w', encoding='utf-8') as f:
                        json.dump(initial_mappings, f, indent=2, ensure_ascii=False)
                    self.print_colored(f"✅ Archivo de mappings recreado: {self.mappings_file}", "green")
                except Exception as write_error:
                    self.print_colored(f"❌ Error recreando archivo de mappings: {write_error}", "red")
                    return False
            except Exception as e:
                self.print_colored(f"❌ Error inesperado procesando mappings: {e}", "red")
                return False

        return True

    def get_php_mappings(self) -> Optional[Dict]:
        """Obtiene los mappings de PHP con validación completa de estructura"""
        self.initialize_php_mappings()

        try:
            with open(self.mappings_file, 'r', encoding='utf-8') as f:
                content = f.read().strip()

            if not content:
                self.print_colored("❌ Archivo de mappings vacío", "red")
                return None

            json_obj = json.loads(content)

            # Validar estructura básica
            if not isinstance(json_obj, dict):
                self.print_colored("❌ Estructura de mappings inválida", "red")
                return None

            # Crear estructura normalizada
            hash_structure = {
                "mappings": {},
                "created": json_obj.get("created", ""),
                "version": json_obj.get("version", "1.0"),
                "updated": json_obj.get("updated", None)
            }

            # Procesar mappings si existen
            mappings_data = json_obj.get("mappings", {})
            if isinstance(mappings_data, dict):
                for name, value in mappings_data.items():
                    if isinstance(value, dict):
                        # Validar campos requeridos
                        if all(key in value for key in ["directory", "version", "phpPath"]):
                            hash_structure["mappings"][name] = {
                                "directory": value.get("directory", ""),
                                "version": value.get("version", ""),
                                "phpPath": value.get("phpPath", ""),
                                "created": value.get("created", "")
                            }
                        else:
                            self.print_colored(f"⚠️  Mapping '{name}' incompleto, saltando...", "yellow")
                            continue
                    else:
                        self.print_colored(f"⚠️  Mapping '{name}' tiene formato incorrecto, saltando...", "yellow")
                        continue

            return hash_structure

        except json.JSONDecodeError as e:
            self.print_colored(f"❌ Error de formato JSON en mappings: {e}", "red")
            return None
        except FileNotFoundError:
            self.print_colored(f"❌ Archivo de mappings no encontrado: {self.mappings_file}", "red")
            return None
        except PermissionError:
            self.print_colored(f"❌ Sin permisos para leer archivo de mappings: {self.mappings_file}", "red")
            return None
        except Exception as e:
            self.print_colored(f"❌ Error inesperado leyendo mappings: {e}", "red")
            return None

    def save_php_mappings(self, mappings: Dict) -> bool:
        """Guarda los mappings de PHP con validación completa"""
        try:
            # Validar entrada
            if not isinstance(mappings, dict):
                self.print_colored("❌ Los mappings deben ser un diccionario", "red")
                return False

            # Crear copia para no modificar el original
            mappings_copy = mappings.copy()

            # Actualizar timestamp
            mappings_copy["updated"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Asegurar que la propiedad mappings existe y es un diccionario
            if "mappings" not in mappings_copy or not isinstance(mappings_copy["mappings"], dict):
                mappings_copy["mappings"] = {}

            # Validar estructura básica
            required_fields = ["created", "version"]
            for field in required_fields:
                if field not in mappings_copy:
                    if field == "created":
                        mappings_copy[field] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    elif field == "version":
                        mappings_copy[field] = "1.0"

            # Crear directorio padre si no existe
            mappings_dir = os.path.dirname(self.mappings_file)
            if mappings_dir and not os.path.exists(mappings_dir):
                os.makedirs(mappings_dir, exist_ok=True)

            # Crear archivo temporal primero para escritura atómica
            temp_file = self.mappings_file + ".tmp"

            try:
                # Escribir a archivo temporal
                with open(temp_file, 'w', encoding='utf-8') as f:
                    json.dump(mappings_copy, f, indent=2, ensure_ascii=False, sort_keys=True)

                # Mover archivo temporal al destino final (operación atómica)
                if os.path.exists(self.mappings_file):
                    if os.name == 'nt':  # Windows
                        os.replace(temp_file, self.mappings_file)
                    else:  # Unix/Linux
                        os.rename(temp_file, self.mappings_file)
                else:
                    os.rename(temp_file, self.mappings_file)

            except Exception as e:
                # Limpiar archivo temporal si algo sale mal
                if os.path.exists(temp_file):
                    try:
                        os.remove(temp_file)
                    except:
                        pass
                raise e

            return True

        except PermissionError:
            self.print_colored(f"❌ Error de permisos guardando mappings: {self.mappings_file}", "red")
            return False
        except FileNotFoundError:
            self.print_colored(f"❌ Directorio no encontrado: {os.path.dirname(self.mappings_file)}", "red")
            return False
        except json.JSONEncodeError as e:
            self.print_colored(f"❌ Error de formato JSON: {e}", "red")
            return False
        except OSError as e:
            self.print_colored(f"❌ Error del sistema guardando mappings: {e}", "red")
            return False
        except Exception as e:
            self.print_colored(f"❌ Error inesperado guardando mappings: {e}", "red")
            return False

    def backup_mappings(self) -> bool:
        """Crea un backup de los mappings actuales"""
        if not os.path.exists(self.mappings_file):
            return True  # No hay nada que respaldar

        try:
            backup_file = f"{self.mappings_file}.backup.{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"

            import shutil
            shutil.copy2(self.mappings_file, backup_file)

            # Mantener solo los últimos 5 backups
            self.cleanup_old_backups()

            return True
        except Exception as e:
            self.print_colored(f"⚠️  No se pudo crear backup: {e}", "yellow")
            return False

    def cleanup_old_backups(self, max_backups: int = 5):
        """Limpia backups antiguos manteniendo solo los más recientes"""
        try:
            backup_dir = os.path.dirname(self.mappings_file)
            backup_pattern = os.path.basename(self.mappings_file) + ".backup."

            backups = []
            for file in os.listdir(backup_dir):
                if file.startswith(backup_pattern):
                    backup_path = os.path.join(backup_dir, file)
                    backups.append((backup_path, os.path.getctime(backup_path)))

            # Ordenar por fecha de creación (más recientes primero)
            backups.sort(key=lambda x: x[1], reverse=True)

            # Eliminar backups antiguos
            for backup_path, _ in backups[max_backups:]:
                try:
                    os.remove(backup_path)
                except:
                    pass  # Ignorar errores al eliminar backups antiguos

        except:
            pass  # Ignorar errores en limpieza de backups

    def save_php_mappings_with_backup(self, mappings: Dict) -> bool:
        """Guarda mappings creando backup primero"""
        # Crear backup antes de guardar
        self.backup_mappings()

        # Guardar mappings
        return self.save_php_mappings(mappings)

    def add_directory_mapping(self, directory: str, version: str, alias: str) -> bool:
        """Agrega un mapping de directorio a una versión específica de PHP con validaciones completas"""

        # Validar que los parámetros no estén vacíos
        if not directory or not version or not alias:
            self.print_colored("❌ Todos los parámetros son requeridos (directorio, versión, alias)", "red")
            return False

        # Validar caracteres del alias
        if not alias.replace('_', '').replace('-', '').isalnum():
            self.print_colored("❌ El alias solo puede contener letras, números, guiones y guiones bajos", "red")
            return False

        # Normalizar el directorio (resolver path absoluto)
        try:
            directory = os.path.abspath(directory)
        except Exception as e:
            self.print_colored(f"❌ Path de directorio inválido: {e}", "red")
            return False

        # Validar que el directorio existe
        if not os.path.exists(directory):
            self.print_colored(f"❌ El directorio no existe: {directory}", "red")
            return False

        # Validar que es realmente un directorio
        if not os.path.isdir(directory):
            self.print_colored(f"❌ La ruta especificada no es un directorio: {directory}", "red")
            return False

        # Validar versión PHP
        if version not in self.available_versions:
            self.print_colored(f"❌ Versión PHP no reconocida: {version}", "red")
            available = ', '.join(sorted(self.available_versions.keys()))
            self.print_colored(f"   Versiones disponibles: {available}", "yellow")
            return False

        php_path = self.available_versions[version]
        php_exe = os.path.join(php_path, "php.exe")

        if not os.path.exists(php_exe):
            self.print_colored(f"❌ PHP {version} no está instalado: {php_path}", "red")
            return False

        # Cargar mappings existentes
        mappings = self.get_php_mappings()
        if not mappings:
            return False

        # Verificar si el alias ya existe
        if alias in mappings["mappings"]:
            existing = mappings["mappings"][alias]
            self.print_colored(f"⚠️  El alias '{alias}' ya existe:", "yellow")
            self.print_colored(f"   Directorio actual: {existing.get('directory', 'N/A')}", "gray")
            self.print_colored(f"   Versión actual: {existing.get('version', 'N/A')}", "gray")

            # Preguntar si desea sobrescribir (en un entorno interactivo)
            # Por ahora, simplemente sobrescribimos con advertencia
            self.print_colored(f"   Sobrescribiendo mapping existente...", "yellow")

        # Verificar si el directorio ya está mapeado con otro alias
        for existing_alias, mapping_data in mappings["mappings"].items():
            if (mapping_data.get("directory") == directory and
                    existing_alias != alias):
                self.print_colored(f"⚠️  El directorio ya está mapeado con el alias '{existing_alias}'", "yellow")
                break

        # Agregar nuevo mapping
        mappings["mappings"][alias] = {
            "directory": directory,
            "version": version,
            "phpPath": php_path,
            "created": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        # Guardar
        if not self.save_php_mappings(mappings):
            return False

        # Mostrar confirmación con el mismo formato que PowerShell
        self.print_colored("✅ Mapping agregado:", "green")
        self.print_colored(f"   Alias: {alias}", "cyan")
        self.print_colored(f"   Directorio: {directory}", "gray")
        self.print_colored(f"   PHP: {version} ({php_path})", "gray")

        return True

    def validate_alias(self, alias: str) -> bool:
        """Valida que el alias tenga un formato correcto"""
        if not alias:
            return False

        # Solo permitir caracteres alfanuméricos, guiones y guiones bajos
        import re
        if not re.match(r'^[a-zA-Z0-9_-]+$', alias):
            return False

        # No permitir que empiece o termine con guión
        if alias.startswith('-') or alias.endswith('-'):
            return False

        # Longitud razonable
        if len(alias) > 50:
            return False

        return True

    def show_available_versions(self):
        """Muestra las versiones PHP disponibles"""
        self.print_colored("Versiones PHP disponibles:", "yellow")
        for version in sorted(self.available_versions.keys()):
            path = self.available_versions[version]
            php_exe = os.path.join(path, "php.exe")
            if os.path.exists(php_exe):
                self.print_colored(f"  ✓ {version} ({path})", "green")
            else:
                self.print_colored(f"  ✗ {version} ({path}) - No instalado", "red")

    def remove_directory_mapping(self, alias: str) -> bool:
        """Elimina un mapping de directorio existente con información adicional"""

        # Validar entrada
        if not alias or not alias.strip():
            self.print_colored("❌ El alias no puede estar vacío", "red")
            return False

        alias = alias.strip()

        # Cargar mappings existentes
        mappings = self.get_php_mappings()
        if not mappings:
            return False

        # Verificar si el alias existe
        if alias not in mappings.get("mappings", {}):
            self.print_colored(f"❌ Alias no encontrado: {alias}", "red")

            # Mostrar aliases disponibles si hay alguno
            available_aliases = list(mappings.get("mappings", {}).keys())
            if available_aliases:
                self.print_colored("   Aliases disponibles:", "yellow")
                for available_alias in sorted(available_aliases):
                    self.print_colored(f"     - {available_alias}", "gray")
            else:
                self.print_colored("   No hay mappings configurados", "gray")

            return False

        # Mostrar información del mapping que se va a eliminar
        mapping_info = mappings["mappings"][alias]
        self.print_colored(f"Eliminando mapping:", "yellow")
        self.print_colored(f"   Alias: {alias}", "cyan")
        self.print_colored(f"   Directorio: {mapping_info.get('directory', 'N/A')}", "gray")
        self.print_colored(f"   Versión PHP: {mapping_info.get('version', 'N/A')}", "gray")
        self.print_colored(f"   Creado: {mapping_info.get('created', 'N/A')}", "gray")

        # Eliminar el mapping
        del mappings["mappings"][alias]

        # Guardar cambios
        if self.save_php_mappings(mappings):
            self.print_colored(f"✅ Mapping '{alias}' eliminado.", "green")
            return True
        else:
            self.print_colored(f"❌ Error guardando cambios", "red")
            return False

    def remove_multiple_mappings(self, aliases: list) -> bool:
        """Elimina múltiples mappings de una vez"""
        if not aliases:
            self.print_colored("❌ No se especificaron aliases para eliminar", "red")
            return False

        mappings = self.get_php_mappings()
        if not mappings:
            return False

        removed = []
        not_found = []

        for alias in aliases:
            alias = alias.strip()
            if alias in mappings.get("mappings", {}):
                del mappings["mappings"][alias]
                removed.append(alias)
            else:
                not_found.append(alias)

        if removed:
            if self.save_php_mappings(mappings):
                self.print_colored(f"✅ Eliminados {len(removed)} mappings:", "green")
                for alias in removed:
                    self.print_colored(f"   - {alias}", "gray")
            else:
                self.print_colored("❌ Error guardando cambios", "red")
                return False

        if not_found:
            self.print_colored(f"⚠️  No encontrados ({len(not_found)}):", "yellow")
            for alias in not_found:
                self.print_colored(f"   - {alias}", "gray")

        return len(removed) > 0

    def show_directory_mappings(self):
        """Muestra todos los mappings con información detallada y estadísticas"""

        mappings = self.get_php_mappings()
        if not mappings:
            self.print_colored("No se pudieron cargar los mappings.", "red")
            return

        self.print_colored("=== Mappings de Directorios a Versiones PHP ===", "green")
        print()

        mappings_data = mappings.get("mappings", {})

        if not mappings_data:
            self.print_colored("No hay mappings configurados.", "yellow")
            print()
            self._show_usage_examples()
            return

        # Calcular estadísticas
        stats = self._calculate_mapping_stats(mappings_data)
        self._show_statistics(stats)

        # Mostrar mappings detallados
        self._show_detailed_mappings(mappings_data)

        # Mostrar información del archivo
        self._show_file_info(mappings)

    def _show_usage_examples(self):
        """Muestra ejemplos de uso cuando no hay mappings"""
        self.print_colored("Uso:", "cyan")
        self.print_colored("  python php_manager.py -d 'C:\\www\\proyecto' -v 8.1 -a proyecto", "white")
        print()
        self.print_colored("Ejemplos:", "cyan")
        self.print_colored("  python php_manager.py -d 'C:\\www\\legacy' -v 7.4 -a legacy", "gray")
        self.print_colored("  python php_manager.py -d 'C:\\www\\modern' -v 8.3 -a modern", "gray")

    def _calculate_mapping_stats(self, mappings_data):
        """Calcula estadísticas de los mappings"""
        stats = {
            'total': len(mappings_data),
            'valid': 0,
            'invalid_dirs': 0,
            'invalid_php': 0,
            'permission_issues': 0,
            'php_execution_issues': 0
        }

        for alias, config in mappings_data.items():
            directory = config.get('directory', '')
            php_path = config.get('phpPath', '')

            # Verificar directorio
            dir_status = self._check_directory_status(directory)

            # Verificar PHP
            php_status = self._check_php_status(php_path)

            # Actualizar estadísticas
            if dir_status['exists'] and php_status['exists']:
                stats['valid'] += 1
            if not dir_status['exists']:
                stats['invalid_dirs'] += 1
            if not php_status['exists']:
                stats['invalid_php'] += 1
            if dir_status['permission_issue']:
                stats['permission_issues'] += 1
            if php_status['execution_issue']:
                stats['php_execution_issues'] += 1

        return stats

    def _check_directory_status(self, directory):
        """Verifica el estado de un directorio"""
        status = {
            'exists': False,
            'is_dir': False,
            'readable': False,
            'permission_issue': False
        }

        if not directory:
            return status

        status['exists'] = os.path.exists(directory)
        if status['exists']:
            status['is_dir'] = os.path.isdir(directory)
            if status['is_dir']:
                status['readable'] = os.access(directory, os.R_OK)
                status['permission_issue'] = not status['readable']

        return status

    def _check_php_status(self, php_path):
        """Verifica el estado de PHP"""
        status = {
            'exists': False,
            'executable': False,
            'version_info': None,
            'execution_issue': False
        }

        if not php_path:
            return status

        php_exe = os.path.join(php_path, "php.exe")
        status['exists'] = os.path.exists(php_exe)

        if status['exists']:
            try:
                result = subprocess.run([php_exe, "--version"],
                                        capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    status['executable'] = True
                    status['version_info'] = result.stdout.split('\n')[0]
                else:
                    status['execution_issue'] = True
            except Exception:
                status['execution_issue'] = True

        return status

    def _show_statistics(self, stats):
        """Muestra las estadísticas generales"""
        self.print_colored(f"📊 Estadísticas generales:", "yellow")
        self.print_colored(f"   Total mappings: {stats['total']}", "white")

        if stats['valid'] > 0:
            self.print_colored(f"   ✅ Válidos: {stats['valid']}", "green")

        if stats['invalid_dirs'] > 0:
            self.print_colored(f"   📁❌ Directorios no encontrados: {stats['invalid_dirs']}", "red")

        if stats['invalid_php'] > 0:
            self.print_colored(f"   🐘❌ PHP no encontrado: {stats['invalid_php']}", "red")

        if stats['permission_issues'] > 0:
            self.print_colored(f"   🔐 Problemas de permisos: {stats['permission_issues']}", "yellow")

        if stats['php_execution_issues'] > 0:
            self.print_colored(f"   ⚙️ Problemas de ejecución PHP: {stats['php_execution_issues']}", "yellow")

        print()

    def _show_detailed_mappings(self, mappings_data):
        """Muestra los mappings detallados ordenados por alias"""
        self.print_colored("📋 Mappings detallados:", "yellow")
        print()

        for alias in sorted(mappings_data.keys(), key=str.lower):
            config = mappings_data[alias]
            self._show_single_mapping(alias, config)

    def _show_single_mapping(self, alias, config):
        """Muestra un mapping individual con todas sus verificaciones"""
        self.print_colored(f"📁 {alias}", "cyan")

        # Información básica
        directory = config.get('directory', 'N/A')
        version = config.get('version', 'N/A')
        php_path = config.get('phpPath', 'N/A')
        created = config.get('created', 'N/A')

        self.print_colored(f"   📂 Directorio: {directory}", "gray")
        self.print_colored(f"   🐘 PHP: {version} ({php_path})", "gray")
        self.print_colored(f"   📅 Creado: {created}", "dark_gray")

        # Verificaciones detalladas
        dir_status = self._check_directory_status(directory)
        php_status = self._check_php_status(php_path)

        # Mostrar estado del directorio
        self._show_directory_status(dir_status, directory)

        # Mostrar estado de PHP
        self._show_php_status(php_status, php_path)

        # Estado general del mapping
        self._show_mapping_overall_status(dir_status, php_status)

        print()

    def _show_directory_status(self, dir_status, directory):
        """Muestra el estado detallado del directorio"""
        if not directory or directory == 'N/A':
            self.print_colored("   📂❌ Directorio no especificado", "red")
            return

        if not dir_status['exists']:
            self.print_colored("   📂❌ Directorio no encontrado", "red")
        elif not dir_status['is_dir']:
            self.print_colored("   📂⚠️  La ruta no es un directorio", "red")
        elif not dir_status['readable']:
            self.print_colored("   📂⚠️  Sin permisos de lectura en directorio", "yellow")
        else:
            self.print_colored("   📂✅ Directorio accesible", "green")

    def _show_php_status(self, php_status, php_path):
        """Muestra el estado detallado de PHP"""
        if not php_path or php_path == 'N/A':
            self.print_colored("   🐘❌ Ruta PHP no especificada", "red")
            return

        if not php_status['exists']:
            self.print_colored("   🐘❌ PHP no encontrado", "red")
        elif php_status['execution_issue']:
            self.print_colored("   🐘⚠️  Error verificando/ejecutando PHP", "yellow")
        elif php_status['executable'] and php_status['version_info']:
            self.print_colored(f"   🐘✅ {php_status['version_info']}", "green")
        else:
            self.print_colored("   🐘⚠️  PHP no ejecuta correctamente", "yellow")

    def _show_mapping_overall_status(self, dir_status, php_status):
        """Muestra el estado general del mapping"""
        if (dir_status['exists'] and dir_status['is_dir'] and dir_status['readable'] and
                php_status['exists'] and php_status['executable']):
            self.print_colored("   🎯 Mapping completamente funcional", "green")
        elif dir_status['exists'] and php_status['exists']:
            self.print_colored("   🔧 Mapping parcialmente funcional", "yellow")
        else:
            self.print_colored("   💥 Mapping no funcional", "red")

    def _show_file_info(self, mappings):
        """Muestra información sobre el archivo de mappings"""
        self.print_colored("📄 Información del archivo:", "yellow")
        self.print_colored(f"   📍 Ubicación: {self.mappings_file}", "gray")
        self.print_colored(f"   📅 Creado: {mappings.get('created', 'N/A')}", "gray")
        self.print_colored(f"   🔄 Actualizado: {mappings.get('updated', 'Nunca')}", "gray")
        self.print_colored(f"   📋 Versión: {mappings.get('version', 'N/A')}", "gray")

        # Información adicional del archivo
        try:
            file_stat = os.stat(self.mappings_file)
            file_size = file_stat.st_size
            last_modified = datetime.fromtimestamp(file_stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
            self.print_colored(f"   📏 Tamaño: {file_size} bytes", "gray")
            self.print_colored(f"   🕒 Última modificación: {last_modified}", "gray")
        except Exception:
            pass  # Si no se puede obtener info del archivo, no es crítico

    def install_mod_fcgid(self, apache_modules_path="C:\\APACHE24\\modules"):
        """Instala mod_fcgid automáticamente descargándolo desde ApacheLounge"""
        self.print_colored("📥 Instalando mod_fcgid automáticamente...", "yellow")

        if not os.path.exists(apache_modules_path):
            self.print_colored(f"❌ Directorio de módulos de Apache no encontrado: {apache_modules_path}", "red")
            return False

        mod_fcgid_path = os.path.join(apache_modules_path, "mod_fcgid.so")
        zip_filename = "mod_fcgid-2.3.10-win64-VS17.zip"
        temp_dir = None

        try:
            # ✅ URL CORRECTA
            download_url = "https://www.apachelounge.com/download/VS17/modules/mod_fcgid-2.3.10-win64-VS17.zip"

            # Directorio temporal
            temp_dir = tempfile.mkdtemp(prefix="mod_fcgid_")
            zip_path = os.path.join(temp_dir, zip_filename)

            # 1. Descargar
            if not self._download_mod_fcgid(download_url, zip_path):
                return False

            # 2. Descomprimir y encontrar mod_fcgid.so
            mod_fcgid_source = self._extract_and_find_mod_fcgid(zip_path, temp_dir)
            if not mod_fcgid_source:
                return False

            # 3. Copiar a Apache
            shutil.copy2(mod_fcgid_source, mod_fcgid_path)
            self.print_colored(f"✅ mod_fcgid.so copiado a: {mod_fcgid_path}", "green")

            # 4. Verificar instalación
            return self._verify_mod_fcgid_installation(mod_fcgid_path)

        except Exception as e:
            self.print_colored(f"❌ Error instalando mod_fcgid: {str(e)}", "red")
            return False
        finally:
            # Limpiar temporal
            if temp_dir and os.path.exists(temp_dir):
                try:
                    shutil.rmtree(temp_dir)
                except Exception:
                    pass

    def _download_mod_fcgid(self, url, zip_path):
        """Descarga el archivo mod_fcgid desde ApacheLounge"""

        # 🔒 Validación crítica: asegurarse de que la URL es externa
        if not url.startswith("http"):
            self.print_colored(f"❌ URL inválida: {url}", "red")
            return False

        if "localhost" in url or "127.0.0.1" in url:
            self.print_colored(f"❌ URL incorrecta: apunta a localhost. Usa: https://www.apachelounge.com/...", "red")
            return False

        self.print_colored("📥 Descargando mod_fcgid desde ApacheLounge...", "cyan")
        self.print_colored(f"   URL: {url}", "gray")

        try:
            # ⚠️ Añadir User-Agent (algunos servidores bloquean requests sin él)
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }

            response = requests.get(url, stream=True, headers=headers, timeout=30)
            response.raise_for_status()

            total_size = int(response.headers.get('content-length', 0))
            downloaded_size = 0

            # Crear directorio si no existe
            os.makedirs(os.path.dirname(zip_path), exist_ok=True)

            with open(zip_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)

                        if total_size > 0 and downloaded_size % (100 * 1024) == 0:
                            percent = (downloaded_size / total_size) * 100
                            self.print_colored(
                                f"\r   Progreso: {percent:.1f}% ({downloaded_size}/{total_size} bytes)", "cyan", end=""
                            )

            print()  # Nueva línea

            if not os.path.exists(zip_path):
                self.print_colored("❌ Error: No se creó el archivo ZIP", "red")
                return False

            file_size = os.path.getsize(zip_path)
            if file_size == 0:
                self.print_colored("❌ Error: El archivo descargado está vacío", "red")
                return False

            self.print_colored(f"✅ Descarga completada: {file_size:,} bytes", "green")
            return True

        except requests.exceptions.MissingSchema:
            self.print_colored("❌ URL inválida: falta esquema (http:// o https://)", "red")
            return False
        except requests.exceptions.ConnectionError as e:
            self.print_colored(f"❌ Error de conexión: {str(e)}", "red")
            self.print_colored("💡 Verifica tu conexión a internet o el firewall", "yellow")
            return False
        except requests.exceptions.Timeout:
            self.print_colored("❌ Tiempo de espera agotado durante la descarga", "red")
            return False
        except Exception as e:
            self.print_colored(f"❌ Error inesperado: {str(e)}", "red")
            return False

    def _extract_and_find_mod_fcgid(self, zip_path, temp_dir):
        """Descomprime el ZIP y busca el archivo mod_fcgid.so"""

        self.print_colored("📦 Descomprimiendo archivo...", "yellow")

        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)

            # Buscar mod_fcgid.so en la estructura descomprimida
            mod_fcgid_source = None
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    if file == "mod_fcgid.so":
                        mod_fcgid_source = os.path.join(root, file)
                        break
                if mod_fcgid_source:
                    break

            if not mod_fcgid_source:
                self.print_colored("❌ Error: mod_fcgid.so no encontrado en el archivo ZIP", "red")
                self.print_colored("📁 Contenido del ZIP:", "gray")
                self._show_zip_contents(temp_dir)
                return None

            self.print_colored(f"✅ mod_fcgid.so encontrado en: {mod_fcgid_source}", "green")
            return mod_fcgid_source

        except zipfile.BadZipFile:
            self.print_colored("❌ Error: El archivo descargado no es un ZIP válido", "red")
            return None
        except Exception as e:
            self.print_colored(f"❌ Error descomprimiendo archivo: {str(e)}", "red")
            return None

    def _show_zip_contents(self, temp_dir):
        """Muestra el contenido del directorio descomprimido para debugging"""

        try:
            for root, dirs, files in os.walk(temp_dir):
                level = root.replace(temp_dir, '').count(os.sep)
                indent = '  ' * level
                rel_path = os.path.relpath(root, temp_dir)
                if rel_path != '.':
                    self.print_colored(f"{indent}📁 {rel_path}/", "dark_gray")

                sub_indent = '  ' * (level + 1)
                for file in files:
                    file_path = os.path.join(root, file)
                    file_size = os.path.getsize(file_path)
                    self.print_colored(f"{sub_indent}📄 {file} ({file_size:,} bytes)", "dark_gray")
        except Exception:
            self.print_colored("   (No se pudo mostrar el contenido)", "dark_gray")

    def _copy_mod_fcgid(self, source_path, destination_path):
        """Copia mod_fcgid.so al directorio de módulos de Apache"""

        self.print_colored("📁 Copiando mod_fcgid.so a Apache modules...", "yellow")
        self.print_colored(f"   Origen: {source_path}", "gray")
        self.print_colored(f"   Destino: {destination_path}", "gray")

        try:
            # Verificar que el archivo origen existe
            if not os.path.exists(source_path):
                self.print_colored(f"❌ Error: Archivo origen no encontrado: {source_path}", "red")
                return False

            # Verificar permisos de escritura en el directorio destino
            dest_dir = os.path.dirname(destination_path)
            if not os.access(dest_dir, os.W_OK):
                self.print_colored(f"❌ Error: Sin permisos de escritura en: {dest_dir}", "red")
                self.print_colored("   💡 Ejecuta el script como administrador", "yellow")
                return False

            # Realizar la copia
            shutil.copy2(source_path, destination_path)

            return True

        except PermissionError:
            self.print_colored("❌ Error: Sin permisos para copiar el archivo", "red")
            self.print_colored("   💡 Ejecuta el script como administrador", "yellow")
            return False
        except Exception as e:
            self.print_colored(f"❌ Error copiando archivo: {str(e)}", "red")
            return False

    def _verify_mod_fcgid_installation(self, mod_fcgid_path):
        """Verifica que mod_fcgid.so se instaló correctamente"""

        if os.path.exists(mod_fcgid_path):
            file_size = os.path.getsize(mod_fcgid_path)
            self.print_colored(f"✅ mod_fcgid.so instalado correctamente ({file_size:,} bytes)", "green")

            # Verificaciones adicionales
            if file_size == 0:
                self.print_colored("⚠️  Advertencia: El archivo instalado está vacío", "yellow")
                return False

            # Verificar que es un archivo binario (debe contener bytes no ASCII)
            try:
                with open(mod_fcgid_path, 'rb') as f:
                    first_bytes = f.read(10)
                    if not any(b > 127 for b in first_bytes):
                        self.print_colored("⚠️  Advertencia: El archivo no parece ser un módulo binario válido",
                                           "yellow")
            except Exception:
                pass  # Ignorar errores de verificación

            return True
        else:
            self.print_colored("❌ Error: No se pudo copiar mod_fcgid.so", "red")
            return False

    def setup_apache_multiversion(self) -> bool:
        """
        Configura Apache para soporte multi-versión PHP usando FastCGI (Enhanced)

        Returns:
            bool: True si la configuración fue exitosa, False en caso contrario
        """

        self.print_colored("🔧 Configurando Apache para soporte multi-versión PHP (Enhanced)...", "yellow")

        # Verificar que Apache esté instalado
        if not self._verify_apache_installation():
            return False

        # Instalar mod_fcgid automáticamente si no existe
        if not self._ensure_mod_fcgid_installed():
            return False

        if not self.ensure_rewrite_module_enabled():
            return False

        # Crear backup de configuración
        backup_path = self._create_config_backup()
        if not backup_path:
            return False

        try:
            # Procesar configuración
            if not self._process_apache_configuration():
                return False

            # Verificar configuración
            if not self._verify_apache_configuration():
                return False

            # Crear/actualizar virtual hosts
            self.update_virtual_hosts()

            return True

        except Exception as e:
            self.print_colored(f"❌ Error configurando Apache: {str(e)}", "red")
            return False

    def _verify_apache_installation(self) -> bool:
        """Verifica que Apache esté instalado (solo archivos, sin conexión)"""
        if not os.path.exists(self.apache_bin):
            self.print_colored(f"❌ Apache no encontrado: {self.apache_bin}", "red")
            return False

        if not os.path.exists(self.apache_conf):
            self.print_colored(f"❌ httpd.conf no encontrado: {self.apache_conf}", "red")
            return False

        self.print_colored("✅ Instalación de Apache verificada", "green")
        return True

    def _ensure_mod_fcgid_installed(self) -> bool:
        """Asegura que mod_fcgid esté instalado"""

        # Obtener directorio de módulos de Apache
        apache_root = os.path.dirname(os.path.dirname(self.apache_bin))
        modules_path = os.path.join(apache_root, "modules")
        mod_fcgid_path = os.path.join(modules_path, "mod_fcgid.so")

        if not os.path.exists(mod_fcgid_path):
            self.print_colored("⚠️  mod_fcgid.so no encontrado. Instalando automáticamente...", "yellow")
            if not self.install_mod_fcgid(modules_path):
                self.print_colored("❌ No se pudo instalar mod_fcgid. Abortando configuración.", "red")
                return False
        else:
            self.print_colored(f"✅ mod_fcgid.so encontrado: {mod_fcgid_path}", "green")

        return True

    def _create_config_backup(self) -> str:
        """Crea un backup de la configuración actual"""

        timestamp = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
        backup_path = f"{self.apache_conf}.backup.{timestamp}"

        try:
            shutil.copy2(self.apache_conf, backup_path)
            self.print_colored(f"📋 Backup creado: {backup_path}", "gray")
            return backup_path
        except Exception as e:
            self.print_colored(f"❌ Error creando backup: {str(e)}", "red")
            return None

    def _process_apache_configuration(self) -> bool:
        """Procesa y actualiza la configuración de Apache"""

        try:
            # Leer configuración actual
            with open(self.apache_conf, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.readlines()

            # Procesar contenido
            new_content = self._remove_existing_php_config(content)
            new_content = self._add_fastcgi_configuration(new_content)
            new_content = self._enable_virtual_hosts(new_content)

            # Guardar nueva configuración
            with open(self.apache_conf, 'w', encoding='utf-8') as f:
                f.writelines(new_content)

            self.print_colored("✅ Configuración Apache actualizada para soporte multi-versión", "green")
            return True

        except Exception as e:
            self.print_colored(f"❌ Error procesando configuración: {str(e)}", "red")
            return False

    def _remove_existing_php_config(self, content: list) -> list:
        """Remueve configuración PHP anterior"""

        new_content = []
        skip_php_section = False

        for line in content:
            # Detectar secciones de configuración PHP
            if "# Configuración PHP multi-versión - INICIO" in line:
                skip_php_section = True
                continue

            if "# Configuración PHP multi-versión - FIN" in line:
                skip_php_section = False
                continue

            if not skip_php_section:
                # Remover líneas PHP sueltas usando expresiones regulares más precisas
                if (re.search(r'LoadModule\s+(php_module|php7_module|fcgid_module)', line) or
                        re.search(r'PHPIniDir', line) or
                        re.search(r'LoadFile.*php.*ts\.dll', line) or
                        re.search(r'AddType.*application/x-httpd-php', line) or
                        re.search(r'FcgidInitialEnv', line) or
                        re.search(r'FcgidWrapper', line) or
                        re.search(r'AddHandler\s+fcgid-script', line)):
                    continue

                new_content.append(line)

        return new_content

    def _add_fastcgi_configuration(self, content: list) -> list:
        """Añade configuración FastCGI optimizada"""

        # Añadir configuración FastCGI
        fastcgi_config = [
            "\n",
            "# Configuración PHP multi-versión - INICIO\n",
            "# Generado automáticamente por PHPVersionManager\n",
            f"# {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n",
            "\n",
            "LoadModule fcgid_module modules/mod_fcgid.so\n",
            "\n",
            "# Configuración FastCGI (basada en ApacheLounge)\n",
            'FcgidInitialEnv PATH "C:\\WINDOWS\\system32;C:\\WINDOWS;C:\\WINDOWS\\System32\\Wbem"\n',
            'FcgidInitialEnv SystemRoot "C:\\Windows"\n',
            'FcgidInitialEnv SystemDrive "C:"\n',
            'FcgidInitialEnv TEMP "C:\\WINDOWS\\Temp"\n',
            'FcgidInitialEnv TMP "C:\\WINDOWS\\Temp"\n',
            'FcgidInitialEnv windir "C:\\WINDOWS"\n',
            "FcgidIOTimeout 64\n",
            "FcgidConnectTimeout 16\n",
            "FcgidMaxRequestsPerProcess 1000\n",
            "FcgidMaxProcesses 50\n",
            "FcgidMaxRequestLen 8131072\n",
            "FcgidBusyTimeout 120\n",
            "\n"
        ]

        # Configurar PHP por defecto
        default_php_config = self._get_default_php_configuration()
        if default_php_config:
            fastcgi_config.extend(default_php_config)

        fastcgi_config.extend([
            "# Configuración PHP multi-versión - FIN\n",
            "\n"
        ])

        content.extend(fastcgi_config)
        return content

    def _get_default_php_configuration(self) -> list:
        """Obtiene configuración para PHP por defecto"""

        # Buscar PHP por defecto (8.3 preferido)
        preferred_versions = ["8.3", "8.2", "8.1", "8.0", "7.4", "7.1"]

        for version in preferred_versions:
            if version in self.available_versions:
                php_path = self.available_versions[version]
                php_cgi = os.path.join(php_path, "php-cgi.exe")

                if os.path.exists(php_cgi):
                    self.print_colored(f"✅ Configurando PHP {version} como versión por defecto", "green")

                    # ✅ Usa as_posix() para convertir ruta a formato con /
                    php_cgi_forward = Path(php_cgi).as_posix()

                    return [
                        f"# PHP por defecto ({version})\n",
                        f'# FcgidInitialEnv PHPRC "{php_path}"\n',
                        "FcgidInitialEnv PHP_FCGI_MAX_REQUESTS 1000\n",
                        '#<Files ~ "\\.php$">\n',
                        "#    AddHandler fcgid-script .php\n",
                        f'#    FcgidWrapper "{php_cgi_forward}" .php\n',
                        "#</Files>\n",
                        "\n"
                    ]
                else:
                    self.print_colored(f"⚠️  php-cgi.exe no encontrado para PHP {version} en: {php_cgi}", "yellow")

        self.print_colored("⚠️  No se encontró ninguna versión de PHP válida para configuración por defecto", "yellow")
        return []

    def _enable_virtual_hosts(self, content: list) -> list:
        """Habilita virtual hosts si no está habilitado"""

        vhost_line = "Include conf/extra/httpd-vhosts.conf"

        # Verificar si ya está habilitado
        for line in content:
            if re.search(rf'^{re.escape(vhost_line)}', line.strip()):
                return content  # Ya está habilitado

        # Buscar línea comentada y descomentarla
        for i, line in enumerate(content):
            if re.search(r'^#\s*Include\s+conf/extra/httpd-vhosts\.conf', line):
                content[i] = re.sub(r'^#\s*', '', line)
                self.print_colored("✅ Habilitado archivo de Virtual Hosts", "green")
                return content

        # Si no se encuentra comentada, añadir al final
        content.extend([
            "\n",
            "# Virtual Hosts habilitado por PHPVersionManager\n",
            f"{vhost_line}\n"
        ])
        self.print_colored("✅ Añadido archivo de Virtual Hosts", "green")

        return content

    def _verify_apache_configuration(self) -> bool:
        """Verifica que la configuración de Apache sea válida"""

        self.print_colored("🔍 Verificando configuración...", "yellow")

        try:
            # Ejecutar test de configuración de Apache
            result = subprocess.run(
                [self.apache_bin, "-t"],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                self.print_colored("✅ Configuración Apache válida", "green")

                # Mostrar información adicional si está disponible
                if result.stdout.strip():
                    self.print_colored("📋 Información adicional:", "gray")
                    for line in result.stdout.strip().split('\n'):
                        self.print_colored(f"   {line}", "dark_gray")

                return True
            else:
                self.print_colored("❌ Error en configuración Apache:", "red")

                # Mostrar errores detallados
                if result.stderr:
                    for line in result.stderr.strip().split('\n'):
                        self.print_colored(f"  {line}", "red")

                if result.stdout:
                    for line in result.stdout.strip().split('\n'):
                        self.print_colored(f"  {line}", "red")

                return False

        except subprocess.TimeoutExpired:
            self.print_colored("❌ Timeout verificando configuración Apache", "red")
            return False
        except FileNotFoundError:
            self.print_colored(f"❌ No se pudo ejecutar Apache: {self.apache_bin}", "red")
            return False
        except Exception as e:
            self.print_colored(f"❌ Error verificando configuración: {str(e)}", "red")
            return False

    def _show_configuration_summary(self) -> None:
        """Muestra un resumen de la configuración aplicada"""

        self.print_colored("\n📋 Resumen de configuración:", "yellow")
        self.print_colored(f"   📁 Archivo configurado: {self.apache_conf}", "gray")
        self.print_colored("   🔧 Módulos habilitados: mod_fcgid", "gray")
        self.print_colored("   🌐 Virtual Hosts: habilitado", "gray")

        # Mostrar PHP por defecto configurado
        for version in ["8.4", "8.3", "8.2", "8.1", "8.0", "7.4", "7.1"]:
            if version in self.available_versions:
                php_path = self.available_versions[version]
                php_cgi = os.path.join(php_path, "php-cgi.exe")
                if os.path.exists(php_cgi):
                    self.print_colored(f"   🐘 PHP por defecto: {version} ({php_path})", "gray")
                    break

        self.print_colored("\n💡 Siguiente paso: Configurar Virtual Hosts para proyectos específicos", "cyan")

    def update_virtual_hosts(self):
        """Actualiza los virtual hosts en un solo VirtualHost con Alias"""
        self.print_colored("🔧 Actualizando Virtual Hosts...", "yellow")
        mappings = self.get_php_mappings()
        if not mappings:
            return

        # Backup si existe
        if os.path.exists(self.vhosts_path):
            backup_vhost = f"{self.vhosts_path}.backup.{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}"
            try:
                shutil.copy2(self.vhosts_path, backup_vhost)
                self.print_colored(f"📋 Backup de vhosts creado: {backup_vhost}", "gray")
            except Exception as e:
                self.print_colored(f"⚠️ Error creando backup: {e}", "yellow")

        # Iniciar contenido
        vhost_content = [
            "# Virtual Hosts generados por PHPVersionManager",
            f"# {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "<VirtualHost *:80>",
            "    ServerName localhost",
            '    DocumentRoot "C:/APACHE24/htdocs"',
            "",
            '    <Directory "C:/APACHE24/htdocs">',
            "        Options Indexes FollowSymLinks",
            "        AllowOverride All",
            "        Require all granted",
            "    </Directory>"
        ]

        # Procesar cada mapping
        for alias, config in sorted(mappings["mappings"].items()):
            directory = config.get("directory", "")
            php_path = config.get("phpPath", "")
            version = config.get("version", "")

            if not directory or not os.path.exists(directory):
                self.print_colored(f"⚠️ Directorio no válido para {alias}: {directory}", "yellow")
                continue

            # Convertir rutas
            dir_fixed = directory.replace("\\", "/")

            # Alias
            vhost_content.append(f'    Alias /{alias} "{dir_fixed}"')

            # <Directory>
            vhost_content.append(f'    <Directory "{dir_fixed}">')
            vhost_content.append("        Options Indexes FollowSymLinks")
            vhost_content.append("        AllowOverride All")
            vhost_content.append("        Require all granted")

            # Configuración PHP si está disponible
            if php_path and version != "xampp":
                cgi_exe = os.path.join(php_path, "php-cgi.exe").replace("\\", "/")
                if os.path.exists(cgi_exe):
                    vhost_content.extend([
                        "        # Configuración PHP",
                        "        <FilesMatch \\.php$>",
                        "            SetHandler fcgid-script",
                        f'            FcgidWrapper "{cgi_exe}" .php',
                        "            Options +ExecCGI",
                        "        </FilesMatch>"
                    ])

            vhost_content.append("    </Directory>")

        # Logs generales
        vhost_content.extend([
            "    ErrorLog logs/vhosts_error.log",
            "    CustomLog logs/vhosts_access.log common",
            "</VirtualHost>"
        ])

        # Escribir archivo
        try:
            os.makedirs(os.path.dirname(self.vhosts_path), exist_ok=True)
            with open(self.vhosts_path, 'w', encoding='utf-8') as f:
                f.write("\n".join(vhost_content))
            self.print_colored(f"✅ Virtual Hosts actualizados: {self.vhosts_path}", "green")
        except Exception as e:
            self.print_colored(f"❌ Error escribiendo vhosts: {e}", "red")

    def _create_vhosts_backup(self) -> bool:
        """Crea backup del archivo de virtual hosts si existe"""

        if os.path.exists(self.vhosts_path):
            try:
                timestamp = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
                backup_path = f"{self.vhosts_path}.backup.{timestamp}"
                shutil.copy2(self.vhosts_path, backup_path)
                self.print_colored(f"📋 Backup VHosts creado: {backup_path}", "gray")
            except Exception as e:
                self.print_colored(f"⚠️  Error creando backup: {str(e)}", "yellow")
                # Continuar sin backup no es crítico

        return True

    def _generate_vhost_content(self, mappings: dict) -> list:
        """Genera el contenido completo de virtual hosts (un solo VirtualHost)"""
        vhost_content = []
        vhost_content.extend(self._get_vhost_header())

        vhost_content.append("<VirtualHost *:80>")
        vhost_content.append("    ServerName localhost")
        vhost_content.append('    DocumentRoot "C:/APACHE24/htdocs"')

        # Directorio raíz
        vhost_content.append('    <Directory "C:/APACHE24/htdocs">')
        vhost_content.append('        Options Indexes FollowSymLinks')
        vhost_content.append('        AllowOverride All')
        vhost_content.append('        Require all granted')
        vhost_content.append('    </Directory>')

        # Mappings (Alias + Directory)
        mappings_data = mappings.get("mappings", {})
        if mappings_data:
            vhost_content.extend(self._get_mappings_vhosts(mappings_data))
        else:
            self.print_colored("ℹ️ No hay mappings configurados", "cyan")

        # Logs generales
        vhost_content.append('    ErrorLog logs/vhosts_error.log')
        vhost_content.append('    CustomLog logs/vhosts_access.log common')
        vhost_content.append("</VirtualHost>")

        return vhost_content

    def _get_vhost_header(self) -> list:
        """Genera encabezado del archivo de virtual hosts"""

        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        return [
            "# Virtual Hosts generados automáticamente por PHPVersionManager\n",
            f"# {timestamp}\n",
            "#\n",
            "# Este archivo es generado automáticamente. Los cambios manuales se perderán.\n",
            "#\n",
            "\n"
        ]

    def _get_php_config_for_vhost(self, php_path: str, php_version: str) -> list:
        """Genera configuración PHP específica para un virtual host"""
        if not php_path or php_version == "xampp":
            return []

        php_cgi_exe = os.path.join(php_path, "php-cgi.exe")
        if not os.path.exists(php_cgi_exe):
            self.print_colored(f"⚠️ php-cgi.exe no encontrado: {php_cgi_exe}", "yellow")
            return []

        # ✅ Convertir ruta a formato con barras normales
        cgi_forward = php_cgi_exe.replace('\\', '/')

        return [
            f"        # PHP {php_version} para este proyecto",
            "        <FilesMatch \\.php$>",
            "            SetHandler fcgid-script",
            f'            FcgidWrapper "{cgi_forward}" .php',  # ✅ Aquí se arregla
            "            Options +ExecCGI",
            "        </FilesMatch>"
        ]

    def _write_vhost_file(self, content: list) -> bool:
        """Escribe el contenido al archivo de virtual hosts"""

        try:
            # Asegurar que el directorio existe
            vhost_dir = os.path.dirname(self.vhosts_path)
            os.makedirs(vhost_dir, exist_ok=True)

            # Escribir archivo
            with open(self.vhosts_path, 'w', encoding='utf-8') as f:
                f.writelines(content)

            return True

        except PermissionError:
            self.print_colored("❌ Error: Sin permisos para escribir archivo de Virtual Hosts", "red")
            self.print_colored("   💡 Ejecuta el script como administrador", "yellow")
            return False
        except Exception as e:
            self.print_colored(f"❌ Error escribiendo archivo VHosts: {str(e)}", "red")
            return False

    def _show_vhosts_summary(self, mappings: dict) -> None:
        """Muestra resumen de virtual hosts configurados"""

        mappings_data = mappings.get("mappings", {})

        if not mappings_data:
            self.print_colored("ℹ️  Solo se configuró el Virtual Host por defecto", "cyan")
            return

        self.print_colored("🌐 Virtual Hosts configurados:", "cyan")

        # Mostrar VHost por defecto
        self.print_colored("   http://localhost/ (por defecto)", "yellow")

        # Mostrar cada mapping
        for alias in sorted(mappings_data.keys(), key=str.lower):
            config = mappings_data[alias]
            php_version = config.get('version', 'N/A')
            directory = config.get('directory', 'N/A')

            self.print_colored(f"   http://localhost/{alias} (PHP {php_version})", "yellow")
            self.print_colored(f"     📁 {directory}", "gray")

            # Verificar estado del directorio
            if directory and directory != 'N/A':
                if os.path.exists(directory):
                    self.print_colored("     ✅ Directorio accesible", "green")
                else:
                    self.print_colored("     ❌ Directorio no encontrado", "red")

    def _validate_vhost_configuration(self) -> bool:
        """Valida la configuración de virtual hosts generada"""

        if not os.path.exists(self.vhosts_path):
            self.print_colored("❌ Archivo de Virtual Hosts no fue creado", "red")
            return False

        try:
            # Verificar que el archivo no esté vacío y tenga contenido válido
            with open(self.vhosts_path, 'r', encoding='utf-8') as f:
                content = f.read()

            if not content.strip():
                self.print_colored("❌ Archivo de Virtual Hosts está vacío", "red")
                return False

            # Verificaciones básicas de sintaxis
            if not ("<VirtualHost" in content and "</VirtualHost>" in content):
                self.print_colored("❌ Archivo de Virtual Hosts no contiene configuración válida", "red")
                return False

            file_size = os.path.getsize(self.vhosts_path)
            self.print_colored(f"✅ Archivo VHosts válido ({file_size} bytes)", "green")
            return True

        except Exception as e:
            self.print_colored(f"❌ Error validando VHosts: {str(e)}", "red")
            return False

    # Función auxiliar mejorada para el update completo
    def update_virtual_hosts_enhanced(self) -> bool:
        """
        Versión mejorada que incluye validación post-escritura
        """

        success = self.update_virtual_hosts()

        if success:
            # Validar configuración generada
            if self._validate_vhost_configuration():
                self.print_colored("🎯 Virtual Hosts actualizados y validados correctamente", "green")
                return True
            else:
                return False

        return False

    def show_php_info(self, php_path: str) -> bool:
        """
        Muestra información detallada de una instalación de PHP específica

        Args:
            php_path (str): Ruta al directorio de PHP

        Returns:
            bool: True si se pudo mostrar la información, False en caso contrario
        """

        php_exe = os.path.join(php_path, "php.exe")

        if not os.path.exists(php_exe):
            self.print_colored(f"❌ php.exe no encontrado en: {php_exe}", "red")
            return False

        self.print_colored("=== Información de PHP ===", "green")
        self.print_colored(f"📍 Ubicación: {php_path}", "gray")

        try:
            # Mostrar información básica de PHP
            self._show_php_version(php_exe)
            self._show_php_modules(php_exe)
            self._show_php_configuration(php_exe)
            self._show_php_extensions_status(php_exe)
            self._show_composer_info(php_path, php_exe)

            return True

        except Exception as e:
            self.print_colored(f"❌ Error mostrando información PHP: {str(e)}", "red")
            return False

    def _show_php_version(self, php_exe: str) -> None:
        """Muestra información de versión de PHP"""

        try:
            result = subprocess.run([php_exe, "-v"],
                                    capture_output=True, text=True, timeout=10)

            if result.returncode == 0 and result.stdout:
                version_lines = result.stdout.strip().split('\n')
                if version_lines:
                    # Primera línea contiene la versión principal
                    main_version = version_lines[0]
                    self.print_colored(f"🐘 Versión: {main_version}", "cyan")

                    # Mostrar información adicional si existe
                    if len(version_lines) > 1:
                        for line in version_lines[1:3]:  # Máximo 2 líneas adicionales
                            if line.strip():
                                self.print_colored(f"   {line.strip()}", "dark_gray")
            else:
                self.print_colored("⚠️  No se pudo obtener información de versión", "yellow")

        except subprocess.TimeoutExpired:
            self.print_colored("⚠️  Timeout obteniendo versión de PHP", "yellow")
        except Exception as e:
            self.print_colored(f"⚠️  Error obteniendo versión: {str(e)}", "yellow")

    def _show_php_modules(self, php_exe: str) -> None:
        """Muestra módulos/extensiones cargadas"""

        self.print_colored("\n📦 Módulos cargados:", "yellow")

        try:
            result = subprocess.run([php_exe, "-m"],
                                    capture_output=True, text=True, timeout=15)

            if result.returncode == 0 and result.stdout:
                modules = []
                core_modules = []

                for line in result.stdout.strip().split('\n'):
                    line = line.strip()
                    if not line or line.startswith('['):
                        continue

                    # Separar módulos core de extensiones
                    if line.lower() in ['core', 'standard', 'pcre', 'spl', 'reflection']:
                        core_modules.append(line)
                    else:
                        modules.append(line)

                # Mostrar módulos core
                if core_modules:
                    self.print_colored("   Core:", "cyan")
                    for module in sorted(core_modules):
                        self.print_colored(f"     • {module}", "dark_gray")

                # Mostrar extensiones
                if modules:
                    self.print_colored("   Extensiones:", "cyan")
                    # Mostrar en columnas para mejor visualización
                    modules_sorted = sorted(modules)
                    self._show_modules_in_columns(modules_sorted)

                total_modules = len(core_modules) + len(modules)
                self.print_colored(f"   📊 Total: {total_modules} módulos", "gray")

            else:
                self.print_colored("   ⚠️  No se pudieron cargar los módulos", "yellow")

        except subprocess.TimeoutExpired:
            self.print_colored("   ⚠️  Timeout obteniendo módulos", "yellow")
        except Exception as e:
            self.print_colored(f"   ⚠️  Error obteniendo módulos: {str(e)}", "yellow")

    def _show_modules_in_columns(self, modules: list, columns: int = 3) -> None:
        """Muestra módulos en columnas para mejor visualización"""

        if not modules:
            return

        # Calcular ancho de columna basado en el módulo más largo
        max_width = max(len(module) for module in modules) + 2

        for i in range(0, len(modules), columns):
            row_modules = modules[i:i + columns]
            row_text = ""

            for module in row_modules:
                row_text += f"• {module:<{max_width}}"

            self.print_colored(f"     {row_text}", "dark_gray")

    def _show_php_configuration(self, php_exe: str) -> None:
        """Muestra configuración importante de PHP"""

        self.print_colored("\n⚙️  Configuración importante:", "yellow")

        # Configuraciones importantes a mostrar
        important_configs = [
            'memory_limit',
            'max_execution_time',
            'upload_max_filesize',
            'post_max_size',
            'max_file_uploads',
            'date.timezone',
            'error_reporting',
            'display_errors'
        ]

        try:
            result = subprocess.run([php_exe, "-i"],
                                    capture_output=True, text=True, timeout=20)

            if result.returncode == 0 and result.stdout:
                config_found = {}

                for line in result.stdout.split('\n'):
                    for config in important_configs:
                        # Buscar configuración en formato "config => value"
                        pattern = rf'{re.escape(config)}\s*=>\s*(.+)'
                        match = re.search(pattern, line, re.IGNORECASE)

                        if match and config not in config_found:
                            value = match.group(1).strip()
                            config_found[config] = value

                # Mostrar configuraciones encontradas
                if config_found:
                    for config in important_configs:
                        if config in config_found:
                            value = config_found[config]
                            self._format_config_output(config, value)
                else:
                    self.print_colored("   ⚠️  No se pudieron obtener configuraciones", "yellow")

            else:
                self.print_colored("   ⚠️  Error ejecutando php -i", "yellow")

        except subprocess.TimeoutExpired:
            self.print_colored("   ⚠️  Timeout obteniendo configuración", "yellow")
        except Exception as e:
            self.print_colored(f"   ⚠️  Error obteniendo configuración: {str(e)}", "yellow")

    def _format_config_output(self, config: str, value: str) -> None:
        """Formatea la salida de configuración con colores apropiados"""

        # Limpiar valor (remover "no value" y similares)
        if "no value" in value.lower() or value == "":
            value = "no definido"
            color = "yellow"
        elif value.lower() in ["on", "1", "true"]:
            value = "activado"
            color = "green"
        elif value.lower() in ["off", "0", "false"]:
            value = "desactivado"
            color = "red"
        else:
            color = "white"

        # Formatear nombre de configuración
        config_display = config.replace('_', ' ').title()
        self.print_colored(f"   📋 {config_display}: ", "gray", end="")
        self.print_colored(value, color)

    def _show_php_extensions_status(self, php_exe: str) -> None:
        """Muestra estado de extensiones críticas"""

        self.print_colored("\n🔌 Estado de extensiones críticas:", "yellow")

        critical_extensions = [
            ('curl', 'Cliente HTTP/HTTPS'),
            ('openssl', 'Criptografía SSL'),
            ('mysqli', 'Bases de Datos SQL'),
            ('gd', 'Formatos PNG, JPEG, XPM además de tipos de letras (fonts) FreeType/ttf'),
            ('mbstring', 'Cadenas multibyte')
        ]

        try:
            result = subprocess.run([php_exe, "-m"],
                                    capture_output=True, text=True, timeout=10)

            if result.returncode == 0:
                loaded_modules = set(result.stdout.lower().split())

                for ext_name, description in critical_extensions:
                    if ext_name.lower() in loaded_modules:
                        self.print_colored(f"   ✅ {ext_name:<12} - {description}", "green")
                    else:
                        self.print_colored(f"   ❌ {ext_name:<12} - {description}", "red")

        except Exception:
            self.print_colored("   ⚠️  No se pudo verificar extensiones", "yellow")

    def _show_composer_info(self, php_path: str, php_exe: str) -> None:
        """Muestra información de Composer"""

        self.print_colored("\n=== Información de Composer ===", "green")

        # Buscar composer.phar en el directorio de PHP
        composer_phar = os.path.join(php_path, "composer.phar")

        if os.path.exists(composer_phar):
            self.print_colored(f"📍 Ubicación: {composer_phar}", "gray")

            try:
                result = subprocess.run([php_exe, composer_phar, "--version", "--no-ansi"],
                                        capture_output=True, text=True, timeout=10)

                if result.returncode == 0 and result.stdout:
                    version_info = result.stdout.strip()
                    self.print_colored(f"📦 {version_info}", "cyan")

                    # Verificar si hay actualizaciones disponibles
                    self._check_composer_updates(php_exe, composer_phar)

                else:
                    self.print_colored("⚠️  Error obteniendo versión de Composer", "yellow")
                    if result.stderr:
                        self.print_colored(f"   Error: {result.stderr.strip()}", "red")

            except subprocess.TimeoutExpired:
                self.print_colored("⚠️  Timeout verificando Composer", "yellow")
            except Exception as e:
                self.print_colored(f"❌ Error: {str(e)}", "red")
        else:
            self.print_colored("❌ Composer no instalado en este directorio PHP", "yellow")
            self.print_colored("💡 Para instalar Composer:", "cyan")
            self.print_colored("   Descarga https://getcomposer.org/composer.phar", "gray")
            self.print_colored(f"   Y colócalo en: {php_path}", "gray")

    def _check_composer_updates(self, php_exe: str, composer_phar: str) -> None:
        """Verifica si hay actualizaciones disponibles para Composer"""

        try:
            # Verificar actualizaciones (con timeout corto para no demorar)
            result = subprocess.run([php_exe, composer_phar, "self-update", "--dry-run"],
                                    capture_output=True, text=True, timeout=5)

            if result.returncode == 0:
                if "already using the latest" in result.stdout.lower():
                    self.print_colored("✅ Composer está actualizado", "green")
                elif "would be updated" in result.stdout.lower():
                    self.print_colored("⚡ Actualización disponible para Composer", "yellow")

        except subprocess.TimeoutExpired:
            pass  # Ignorar timeout en verificación de updates
        except Exception:
            pass  # Ignorar errores en verificación de updates

    # Función auxiliar para mostrar información de todas las versiones
    def show_all_php_info(self) -> None:
        """Muestra información de todas las versiones de PHP disponibles"""

        if not self.available_versions:
            self.print_colored("❌ No hay versiones de PHP configuradas", "red")
            return

        self.print_colored("🔍 Información de todas las versiones PHP disponibles:", "cyan")
        print()

        for version in sorted(self.available_versions.keys()):
            php_path = self.available_versions[version]

            self.print_colored(f"{'=' * 60}", "dark_gray")
            self.print_colored(f"PHP {version}", "yellow")
            self.print_colored(f"{'=' * 60}", "dark_gray")

            if self.show_php_info(php_path):
                print()
            else:
                self.print_colored(f"❌ No se pudo mostrar información para PHP {version}", "red")
                print()

    def install_composer(self, php_path: str, version: str = None):
        """
        Instala Composer en el directorio PHP especificado

        Args:
            php_path (str): Ruta al directorio que contiene php.exe
            version (str, optional): Versión específica de Composer a instalar

        Returns:
            bool: True si la instalación fue exitosa, False en caso contrario
        """
        php_exe = os.path.join(php_path, "php.exe")
        composer_phar = os.path.join(php_path, "composer.phar")

        # Verificar que PHP existe
        if not os.path.exists(php_exe):
            self.print_colored(f"❌ PHP no encontrado: {php_exe}", "red")
            return False

        # Verificar si Composer ya está instalado
        if os.path.exists(composer_phar):
            self.print_colored("ℹ️ Composer ya está presente", "gray")
            return True

        setup_file = "composer-setup.php"
        download_url = "https://getcomposer.org/installer"

        self.print_colored("📥 Descargando instalador de Composer...", "yellow")

        try:
            # Descargar el instalador
            urllib.request.urlretrieve(download_url, setup_file)

            # Verificar hash SHA384 del instalador (hash actualizado)
            expected_hash = "dac665fdc30fdd8ec78b38b9800061b4150413ff2e3b6f88543c636f7cd84f6db9189d43a81e5503cda447da73c7e5b6"

            with open(setup_file, 'rb') as f:
                file_content = f.read()
                actual_hash = hashlib.sha384(file_content).hexdigest().lower()

            if actual_hash != expected_hash.lower():
                self.print_colored("❌ Hash del instalador no coincide", "red")
                if os.path.exists(setup_file):
                    os.remove(setup_file)
                return False

            # Preparar argumentos para la instalación
            cmd = [
                php_exe,
                setup_file,
                "--quiet",
                f"--install-dir={php_path}",
                "--filename=composer.phar"
            ]

            # Agregar versión específica si se proporciona
            if version:
                cmd.append(f"--version={version}")

            version_text = f"v{version}" if version else "(última versión)"
            self.print_colored(f"🔧 Ejecutando instalador... {version_text}", "cyan")

            # Ejecutar el instalador
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)

            # Limpiar archivo temporal
            if os.path.exists(setup_file):
                os.remove(setup_file)

            # Verificar que Composer se instaló correctamente
            if os.path.exists(composer_phar):
                self.print_colored(f"✅ Composer instalado: {composer_phar}", "green")
                return True
            else:
                self.print_colored("❌ Error al instalar Composer", "red")
                return False

        except urllib.error.URLError as e:
            self.print_colored(f"❌ Error al descargar: {e}", "red")
            if os.path.exists(setup_file):
                os.remove(setup_file)
            return False

        except subprocess.CalledProcessError as e:
            self.print_colored(f"❌ Error al ejecutar instalador: {e}", "red")
            if e.stderr:
                self.print_colored(f"   Detalles: {e.stderr.strip()}", "red")
            if os.path.exists(setup_file):
                os.remove(setup_file)
            return False

        except Exception as e:
            self.print_colored(f"❌ Error inesperado: {e}", "red")
            if os.path.exists(setup_file):
                os.remove(setup_file)
            return False

    def initialize_php_ini(self, php_path: str):
        """
        Inicializa el archivo php.ini copiando desde php.ini-development o php.ini-production

        Args:
            php_path (str): Ruta al directorio PHP

        Returns:
            bool: True si php.ini existe o fue creado exitosamente, False en caso contrario
        """
        ini_path = os.path.join(php_path, "php.ini")

        # Verificar si php.ini ya existe
        if os.path.exists(ini_path):
            self.print_colored(f"✅ php.ini ya existe: {ini_path}", "green")
            return True

        # Rutas de los archivos template
        ini_dev = os.path.join(php_path, "php.ini-development")
        ini_prod = os.path.join(php_path, "php.ini-production")

        try:
            # Priorizar php.ini-development
            if os.path.exists(ini_dev):
                shutil.copy2(ini_dev, ini_path)
                self.print_colored("✅ php.ini creado desde php.ini-development", "green")
                return True

            # Usar php.ini-production como alternativa
            elif os.path.exists(ini_prod):
                shutil.copy2(ini_prod, ini_path)
                self.print_colored("✅ php.ini creado desde php.ini-production", "green")
                return True

            # Ningún template encontrado
            else:
                self.print_colored(f"❌ No se encontraron php.ini-development ni php.ini-production en {php_path}",
                                   "red")
                return False

        except PermissionError as e:
            self.print_colored(f"❌ Sin permisos para crear php.ini: {e}", "red")
            return False

        except FileNotFoundError as e:
            self.print_colored(f"❌ Archivo no encontrado: {e}", "red")
            return False

        except Exception as e:
            self.print_colored(f"❌ Error inesperado al crear php.ini: {e}", "red")
            return False

    def set_php_extension(self, php_path: str, extension: str, enable: bool = False, disable: bool = False):
        """
        Habilita o deshabilita una extensión PHP en el archivo php.ini, evitando duplicados.

        Args:
            php_path (str): Ruta al directorio PHP
            extension (str): Nombre de la extensión (ej: 'curl', 'mysqli')
            enable (bool): True para habilitar la extensión
            disable (bool): True para deshabilitar la extensión

        Returns:
            bool: True si la operación fue exitosa, False en caso contrario
        """
        ini_path = os.path.join(php_path, "php.ini")

        # Verificar que php.ini existe
        if not os.path.exists(ini_path):
            self.print_colored(f"❌ php.ini no encontrado: {ini_path}", "red")
            return False

        try:
            # Leer el contenido del archivo php.ini
            with open(ini_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            # Patrón para encontrar cualquier línea relacionada con 'extension=...' para esta extensión
            # Coincide con: extension=mysqli, extension=php_mysqli.dll, ;extension=mysqli, etc.
            pattern = re.compile(rf"^\s*;?\s*extension\s*=\s*{re.escape(extension)}(\.dll)?\s*$", re.IGNORECASE)
            # Patrón alternativo usando el nombre DLL (por compatibilidad)
            dll_name = f"php_{extension}.dll"
            pattern_dll = re.compile(rf"^\s*;?\s*extension\s*=\s*{re.escape(dll_name)}\s*$", re.IGNORECASE)

            # Listas para reconstruir el archivo
            new_lines = []
            found = False
            disabled_comment = ";"

            # Determinar estado deseado
            wanted_enabled = enable and not disable

            for line in lines:
                stripped = line.strip()

                # Si la línea coincide con cualquiera de los patrones de extensión
                if pattern.match(stripped) or pattern_dll.match(stripped):
                    # Ignorar esta línea; la reemplazaremos si es necesario
                    continue

                # Mantener todas las demás líneas
                new_lines.append(line)

            # Si queremos habilitar, agregar una sola entrada limpia
            if wanted_enabled:
                new_entry = f"extension={extension}\n"
                new_lines.append(new_entry)
                self.print_colored(f"✅ {extension} habilitada (única entrada)", "green")
                found = True
            else:
                # Si se deshabilitó, no agregamos nada
                self.print_colored(f"❌ {extension} deshabilitada/removida", "yellow")

            # Escribir el archivo actualizado
            with open(ini_path, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)

            self.print_colored(f"📝 php.ini actualizado: {ini_path}", "cyan")

            # Mensaje si no se encontró antes pero se agregó/eliminó
            if not found and not wanted_enabled:
                self.print_colored(f"ℹ️ {extension} ya estaba deshabilitada o no estaba presente", "gray")
            elif not found and wanted_enabled:
                self.print_colored(f"ℹ️ {extension} agregada por primera vez", "gray")

            return True

        except PermissionError as e:
            self.print_colored(f"❌ Sin permisos para modificar php.ini: {e}", "red")
            return False

        except UnicodeDecodeError as e:
            self.print_colored(f"❌ Error de codificación al leer php.ini: {e}", "red")
            return False

        except Exception as e:
            self.print_colored(f"❌ Error inesperado: {e}", "red")
            return False

    def get_latest_php_versions_from_web(self, scan_only: bool = False):
        """
        Obtiene las últimas versiones de PHP Thread Safe x64 desde windows.php.net

        Args:
            scan_only (bool): Si es True, solo escanea sin procesar (actualmente no usado)

        Returns:
            dict: Diccionario con versiones PHP disponibles o None si hay error
                  Formato: {'8.3': {'Version': '8.3.15', 'Url': 'https://...'}}
        """
        # base_url = "https://windows.php.net/downloads/releases/"
        base_url = "https://windows.php.net/downloads/releases/archives/"

        self.print_colored(f"🔍 Buscando versiones PHP Thread Safe x64 desde {base_url}...", "yellow")

        try:
            # Realizar petición HTTP
            with urllib.request.urlopen(base_url) as response:
                html_content = response.read().decode('utf-8')

            # Parsear HTML para extraer enlaces
            parser = PHPLinkParser()
            parser.feed(html_content)

        except URLError as e:
            self.print_colored(f"❌ No se pudo acceder a {base_url}: {e.reason}", "red")
            return None
        except HTTPError as e:
            self.print_colored(f"❌ Error HTTP {e.code}: {e.reason}", "red")
            return None
        except Exception as e:
            self.print_colored(f"❌ Error inesperado: {e}", "red")
            return None

        # Procesar enlaces encontrados
        candidates = []

        for href in parser.links:
            if '/php-' in href and href.endswith('.zip'):
                # Obtener nombre del archivo
                file_name = href.split('/')[-1]

                # Filtrar archivos no deseados
                excluded_patterns = ['debug-pack', 'devel-pack', 'src.zip', 'test-pack', 'nts']
                if not any(pattern in file_name for pattern in excluded_patterns):
                    # Construir URL completa
                    if href.startswith('http'):
                        full_url = href
                    else:
                        full_url = urllib.parse.urljoin("https://windows.php.net", href)

                    candidates.append({
                        'FileName': file_name,
                        'Url': full_url
                    })

        # Filtrar versiones Thread Safe x64
        ts64_pattern = r'^php-(\d+\.\d+\.\d+)-Win32-(vs|vc)\d{2}-x64\.zip$'
        available_versions = {}

        for candidate in candidates:
            file_name = candidate['FileName']
            match = re.match(ts64_pattern, file_name, re.IGNORECASE)

            if match:
                version_full = match.group(1)
                version_parts = version_full.split('.')

                if len(version_parts) >= 2:
                    version_short = f"{version_parts[0]}.{version_parts[1]}"

                    # Almacenar solo la versión más reciente de cada serie
                    if (version_short not in available_versions or
                            version.parse(version_full) > version.parse(available_versions[version_short]['Version'])):
                        available_versions[version_short] = {
                            'Version': version_full,
                            'Url': candidate['Url']
                        }

        # Mostrar resultados encontrados
        if available_versions:
            self.print_colored(f"✅ Encontradas {len(available_versions)} series de versiones PHP", "green")
            for ver_short in sorted(available_versions.keys(), key=lambda x: version.parse(x), reverse=True):
                ver_info = available_versions[ver_short]
                self.print_colored(f"   📦 PHP {ver_short}: v{ver_info['Version']}", "cyan")
        else:
            self.print_colored("⚠️ No se encontraron versiones válidas de PHP", "yellow")

        return available_versions if available_versions else None

    def set_php_version(self, version: str, show_info: bool = False):
        """
        Activa una versión específica de PHP para uso en CLI

        Args:
            version (str): Versión de PHP a activar (ej: '8.3', '8.2', 'xampp')
            show_info (bool): Si mostrar información detallada de PHP después de activar

        Returns:
            bool: True si la activación fue exitosa, False en caso contrario
        """
        # Verificar que la versión existe en las versiones disponibles
        if not hasattr(self, 'available_versions') or version not in self.available_versions:
            self.print_colored(f"❌ Versión '{version}' no reconocida.", "red")
            return False

        php_path = self.available_versions[version]
        php_exe = os.path.join(php_path, "php.exe")

        # Verificar que el ejecutable de PHP existe
        if not os.path.exists(php_exe):
            self.print_colored(f"❌ PHP {version} no está instalado: {php_path}", "red")
            return False

        try:
            # Establecer la versión activa de PHP
            self.active_php_version = version
            self.active_php_path = php_path
            self.active_php_exe = php_exe

            # Determinar versión de Composer recomendada
            target_composer_version = None

            # Verificar si hay una versión específica de Composer configurada
            if hasattr(self, 'composer_version') and self.composer_version:
                target_composer_version = self.composer_version
            # Usar versiones por defecto si están disponibles
            elif (hasattr(self, 'default_composer_versions') and
                  self.default_composer_versions and
                  version in self.default_composer_versions):
                target_composer_version = self.default_composer_versions[version]

            if not target_composer_version:
                self.print_colored(f"ℹ️ No hay recomendación para Composer en PHP {version}. Usando última versión.",
                                   "gray")

            # Verificar si Composer está disponible
            composer_phar = os.path.join(php_path, "composer.phar")
            if os.path.exists(composer_phar):
                self.active_composer_phar = composer_phar
                composer_version_text = f"v{target_composer_version}" if target_composer_version else "disponible"
                self.print_colored(f"✅ Composer listo ({composer_version_text})", "green")
            else:
                self.active_composer_phar = None
                self.print_colored(f"⚠️ Composer no está instalado. Usa install_composer() para instalarlo.", "yellow")

            # Obtener información de versión de PHP
            try:
                result = subprocess.run([php_exe, '-v'],
                                        capture_output=True,
                                        text=True,
                                        timeout=10)
                if result.returncode == 0:
                    php_version_line = result.stdout.split('\n')[0]
                else:
                    php_version_line = f"PHP {version} (error al obtener versión)"
            except (subprocess.TimeoutExpired, subprocess.SubprocessError, Exception):
                php_version_line = f"PHP {version} (error al obtener versión)"

            # Mostrar información de activación
            self.print_colored(f"🟢 PHP {version} activado para CLI", "green")
            self.print_colored(f"📁 {php_path}", "gray")
            self.print_colored(f"🔢 {php_version_line}", "cyan")

            # Mostrar información detallada si se solicita
            if show_info:
                self.print_colored("", "white")  # Línea en blanco
                self.show_php_info(php_path)

            return True

        except Exception as e:
            self.print_colored(f"❌ Error al activar PHP {version}: {e}", "red")
            return False

    def run_php(self, *args):
        """
        Ejecuta PHP con la versión activa

        Args:
            *args: Argumentos a pasar a PHP

        Returns:
            subprocess.CompletedProcess: Resultado de la ejecución
        """
        if not hasattr(self, 'active_php_exe') or not self.active_php_exe:
            self.print_colored("❌ No hay versión de PHP activa. Usa set_php_version() primero.", "red")
            return None

        try:
            return subprocess.run([self.active_php_exe] + list(args),
                                  capture_output=True,
                                  text=True)
        except Exception as e:
            self.print_colored(f"❌ Error al ejecutar PHP: {e}", "red")
            return None

    def run_composer(self, *args):
        """
        Ejecuta Composer con la versión activa de PHP

        Args:
            *args: Argumentos a pasar a Composer

        Returns:
            subprocess.CompletedProcess: Resultado de la ejecución
        """
        if not hasattr(self, 'active_php_exe') or not self.active_php_exe:
            self.print_colored("❌ No hay versión de PHP activa. Usa set_php_version() primero.", "red")
            return None

        if not hasattr(self, 'active_composer_phar') or not self.active_composer_phar:
            self.print_colored("❌ Composer no está disponible en la versión activa de PHP.", "red")
            return None

        try:
            return subprocess.run([self.active_php_exe, self.active_composer_phar] + list(args),
                                  capture_output=True,
                                  text=True)
        except Exception as e:
            self.print_colored(f"❌ Error al ejecutar Composer: {e}", "red")
            return None

    def get_active_php_info(self):
        """
        Obtiene información sobre la versión activa de PHP

        Returns:
            dict: Información de la versión activa o None si no hay versión activa
        """
        if not hasattr(self, 'active_php_version'):
            return None

        return {
            'version': getattr(self, 'active_php_version', None),
            'path': getattr(self, 'active_php_path', None),
            'exe': getattr(self, 'active_php_exe', None),
            'composer_available': hasattr(self, 'active_composer_phar') and self.active_composer_phar is not None
        }

    def execute_php_command(self, command: str, shell: bool = False, show_output: bool = True):
        """
        Ejecuta un comando PHP o del sistema con la versión activa de PHP

        Args:
            command (str): Comando a ejecutar
            shell (bool): Si ejecutar en shell (permite pipes, redirects, etc.)
            show_output (bool): Si mostrar la salida en tiempo real

        Returns:
            subprocess.CompletedProcess: Resultado de la ejecución o None si hay error
        """
        self.print_colored(f"▶️ Ejecutando: {command}", "yellow")

        try:
            if shell:
                # Ejecutar en shell (permite comandos complejos con pipes, etc.)
                result = subprocess.run(
                    command,
                    shell=True,
                    text=True,
                    capture_output=not show_output
                )
            else:
                # Parsear comando de forma segura
                cmd_parts = shlex.split(command)

                # Si el comando empieza con 'php', usar la versión activa
                if cmd_parts[0].lower() == 'php' and hasattr(self, 'active_php_exe'):
                    cmd_parts[0] = self.active_php_exe

                # Si el comando empieza con 'composer', usar la versión activa
                elif cmd_parts[0].lower() == 'composer':
                    if hasattr(self, 'active_php_exe') and hasattr(self, 'active_composer_phar'):
                        if self.active_composer_phar:
                            cmd_parts = [self.active_php_exe, self.active_composer_phar] + cmd_parts[1:]
                        else:
                            self.print_colored("❌ Composer no está disponible en la versión activa de PHP.", "red")
                            return None
                    else:
                        self.print_colored("❌ No hay versión de PHP activa.", "red")
                        return None

                result = subprocess.run(
                    cmd_parts,
                    text=True,
                    capture_output=not show_output
                )

            # Mostrar resultado si se capturó la salida
            if not show_output:
                if result.stdout:
                    print(result.stdout)
                if result.stderr:
                    self.print_colored(result.stderr, "red")

            # Mostrar código de salida si hay error
            if result.returncode != 0:
                self.print_colored(f"⚠️ Comando terminó con código de salida: {result.returncode}", "yellow")

            return result

        except FileNotFoundError as e:
            self.print_colored(f"❌ Comando no encontrado: {e}", "red")
            return None
        except subprocess.SubprocessError as e:
            self.print_colored(f"❌ Error al ejecutar comando: {e}", "red")
            return None
        except Exception as e:
            self.print_colored(f"❌ Error inesperado: {e}", "red")
            return None

    def execute_php_script(self, script_path: str, *args):
        """
        Ejecuta un script PHP específico con la versión activa

        Args:
            script_path (str): Ruta al script PHP
            *args: Argumentos adicionales para el script

        Returns:
            subprocess.CompletedProcess: Resultado de la ejecución
        """
        if not hasattr(self, 'active_php_exe') or not self.active_php_exe:
            self.print_colored("❌ No hay versión de PHP activa. Usa set_php_version() primero.", "red")
            return None

        if not os.path.exists(script_path):
            self.print_colored(f"❌ Script no encontrado: {script_path}", "red")
            return None

        cmd_parts = [self.active_php_exe, script_path] + list(args)
        command_str = ' '.join(f'"{part}"' if ' ' in part else part for part in cmd_parts)

        self.print_colored(f"▶️ Ejecutando script PHP: {command_str}", "yellow")

        try:
            result = subprocess.run(cmd_parts, text=True, capture_output=True)

            # Mostrar salida
            if result.stdout:
                print(result.stdout)
            if result.stderr:
                self.print_colored(result.stderr, "red")

            if result.returncode != 0:
                self.print_colored(f"⚠️ Script terminó con código de salida: {result.returncode}", "yellow")

            return result

        except Exception as e:
            self.print_colored(f"❌ Error al ejecutar script PHP: {e}", "red")
            return None

    def execute_composer_command(self, *args):
        """
        Ejecuta un comando de Composer con la versión activa

        Args:
            *args: Argumentos para Composer

        Returns:
            subprocess.CompletedProcess: Resultado de la ejecución
        """
        composer_cmd = 'composer ' + ' '.join(args)
        return self.execute_php_command(composer_cmd)

    def execute_interactive_php(self):
        """
        Inicia PHP en modo interactivo con la versión activa
        """
        if not hasattr(self, 'active_php_exe') or not self.active_php_exe:
            self.print_colored("❌ No hay versión de PHP activa. Usa set_php_version() primero.", "red")
            return

        self.print_colored("🔗 Iniciando PHP interactivo (Ctrl+C para salir)...", "cyan")

        try:
            subprocess.run([self.active_php_exe, '-a'], check=True)
        except KeyboardInterrupt:
            self.print_colored("\n👋 Saliendo de PHP interactivo", "gray")
        except Exception as e:
            self.print_colored(f"❌ Error en modo interactivo: {e}", "red")

    def validate_extension_dir(self, php_path: str):
        """
        Valida que el directorio de extensiones existe y está configurado correctamente

        Args:
            php_path (str): Ruta al directorio PHP

        Returns:
            dict: Información sobre el estado del directorio de extensiones
        """
        ini_path = os.path.join(php_path, "php.ini")
        ext_dir_path = os.path.join(php_path, "ext")

        result = {
            'ini_exists': os.path.exists(ini_path),
            'ext_dir_exists': os.path.exists(ext_dir_path),
            'configured_path': None,
            'correct_path': ext_dir_path.replace('\\', '/'),
            'is_correctly_configured': False,
            'needs_fix': False
        }

        if not result['ini_exists']:
            return result

        try:
            # Leer configuración actual
            with open(ini_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Buscar configuración de extension_dir
            pattern = r"^extension_dir\s*=\s*[\"']?([^\"'\n\r]+)[\"']?"
            match = re.search(pattern, content, re.MULTILINE | re.IGNORECASE)

            if match:
                result['configured_path'] = match.group(1).strip()
                # Normalizar rutas para comparación
                configured_normalized = result['configured_path'].replace('\\', '/')
                correct_normalized = result['correct_path']
                result['is_correctly_configured'] = configured_normalized == correct_normalized

            result['needs_fix'] = not result['is_correctly_configured']

        except Exception as e:
            result['error'] = str(e)

        return result

    def show_extension_dir_status(self, php_path: str):
        """
        Muestra el estado actual del directorio de extensiones

        Args:
            php_path (str): Ruta al directorio PHP
        """
        status = self.validate_extension_dir(php_path)

        self.print_colored("📂 Estado del directorio de extensiones:", "cyan")

        if not status['ini_exists']:
            self.print_colored("❌ php.ini no encontrado", "red")
            return

        if not status['ext_dir_exists']:
            self.print_colored(f"⚠️ Directorio 'ext' no existe: {status['correct_path']}", "yellow")

        if status['configured_path']:
            self.print_colored(f"📍 Configurado: {status['configured_path']}", "gray")
            self.print_colored(f"📍 Correcto:    {status['correct_path']}", "gray")

            if status['is_correctly_configured']:
                self.print_colored("✅ Configuración correcta", "green")
            else:
                self.print_colored("❌ Configuración incorrecta", "red")
                self.print_colored("💡 Usar fix_extension_dir() para corregir", "yellow")
        else:
            self.print_colored("⚠️ extension_dir no está configurado", "yellow")
            self.print_colored("💡 Usar fix_extension_dir() para configurar", "yellow")

    def scan_online_php_versions(self) -> Optional[Dict]:
        """Intenta escanear versiones online. Devuelve dict con {ver: {url: ...}} o None."""
        base_url = "https://windows.php.net/downloads/releases/"
        # base_url = "https://windows.php.net/downloads/releases/archives/"
        self.print_colored(f"🔍 Intentando escanear versiones desde {base_url}...", "yellow")

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }

        try:
            req = urllib.request.Request(base_url, headers=headers)
            with urllib.request.urlopen(req, timeout=10) as response:
                html = response.read().decode('utf-8', errors='ignore')

            # Buscar archivos PHP Thread Safe x64
            pattern = r'href="([^"]*php-\d+\.\d+\.\d+-Win32-vs\d+-x64\.zip)"'
            matches = re.findall(pattern, html)

            versions = {}
            for filename in matches:
                full_url = f"https://windows.php.net/downloads/releases/{filename}"
                ver_match = re.search(r'php-(\d+\.\d+)\.\d+', filename)
                if ver_match:
                    short_ver = ver_match.group(1)
                    versions[short_ver] = {"url": full_url}

            if versions:
                self.print_colored(f"✅ Versiones encontradas online: {', '.join(versions.keys())}", "green")
            return versions or {}

        except Exception as e:
            self.print_colored(f"❌ Scraping fallido (usando fallback): {e}", "red")
            return {}  # No None, para que fallback funcione

    def get_php_download_url(self, version: str) -> Optional[str]:
        """Obtiene la URL de descarga para una versión de PHP.
        Primero intenta con scraping en línea, luego con URLs estáticas."""

        # 1. Intentar con scraping online
        if self.remote_php_versions is None:
            self.remote_php_versions = self.get_latest_php_versions_from_web()

        if (self.remote_php_versions and
                version in self.remote_php_versions and
                'Url' in self.remote_php_versions[version]):
            url = self.remote_php_versions[version]['Url']
            self.print_colored(f"🌐 URL encontrada online para PHP {version}: {url}", "green")
            return url

        # 2. Fallback: URLs estáticas (por si el scraping falla)
        fallback_urls = {
            "7.1": "https://windows.php.net/downloads/releases/archives/php-7.1.9-Win32-VC14-x64.zip",
            "7.3": "https://windows.php.net/downloads/releases/archives/php-7.3.9-Win32-VC15-x64.zip",
            "7.4": "https://windows.php.net/downloads/releases/php-7.4.33-Win32-vs16-x64.zip",
            "8.0": "https://windows.php.net/downloads/releases/php-8.0.30-Win32-vs16-x64.zip",
            "8.1": "https://windows.php.net/downloads/releases/php-8.1.33-Win32-vs16-x64.zip",
            "8.2": "https://windows.php.net/downloads/releases/php-8.2.29-Win32-vs16-x64.zip",
            "8.3": "https://windows.php.net/downloads/releases/php-8.3.24-Win32-vs16-x64.zip",
            "8.4": "https://windows.php.net/downloads/releases/php-8.4.0-Win32-vs16-x64.zip"
        }

        if version in fallback_urls:
            url = fallback_urls[version]
            self.print_colored(f"⚠️ Usando URL estática para PHP {version} (scraping fallido o no soportado)", "yellow")
            return url

        self.print_colored(f"❌ No se encontró URL para PHP {version}", "red")
        return None

    def install_php_version(self, version: str, composer_version: Optional[str] = None) -> bool:
        """
        Instala una versión específica de PHP con Composer y configuración.

        Args:
            version (str): Versión de PHP a instalar (ej: "8.3")
            composer_version (str, optional): Versión específica de Composer

        Returns:
            bool: True si la instalación fue exitosa, False en caso contrario
        """
        # Validar versión disponible
        if version not in self.available_versions:
            self.print_colored(f"❌ Versión '{version}' no reconocida.", "red")
            return False

        # Manejar caso especial de XAMPP
        if version == "xampp":
            self.print_colored("⚠️  XAMPP debe instalarse manualmente.", "yellow")
            return False

        php_path = self.available_versions[version]
        zip_file = f"php-{version}.zip"

        # Obtener URL de descarga
        url = self.get_php_download_url(version)
        self.print_colored(f"🔍 Intentando descargar desde esta URL: {url}", "gray")

        if not url:
            self.print_colored(f"❌ No se pudo obtener la URL de descarga para PHP {version}.", "red")
            return False

        # Mostrar información de descarga
        self.print_colored(f"📥 Descargando PHP {version} (Thread Safe x64) desde:", "yellow")
        self.print_colored(f"   {url}", "gray")

        # Descargar archivo
        try:
            urllib.request.urlretrieve(url, zip_file)
        except Exception as e:
            self.print_colored(f"❌ Error al descargar: {str(e)}", "red")
            return False

        # Verificar que se descargó el archivo
        if not os.path.exists(zip_file):
            self.print_colored(f"❌ No se descargó el archivo: {zip_file}", "red")
            return False

        # Preparar directorio de instalación
        self.print_colored(f"📦 Descomprimiendo en {php_path}...", "yellow")
        if os.path.exists(php_path):
            shutil.rmtree(php_path)
        os.makedirs(php_path, exist_ok=True)

        # Descomprimir archivo
        try:
            with zipfile.ZipFile(zip_file, 'r') as zip_ref:
                zip_ref.extractall(php_path)
            os.remove(zip_file)
        except Exception as e:
            self.print_colored(f"❌ Error al descomprimir: {str(e)}", "red")
            return False

        # Verificar que php.exe existe
        php_exe = os.path.join(php_path, "php.exe")
        if not os.path.exists(php_exe):
            self.print_colored(f"❌ No se encontró php.exe en: {php_exe}", "red")
            return False

        self.print_colored(f"✅ PHP {version} instalado correctamente en {php_path}", "green")

        # Inicializar php.ini
        if not self.initialize_php_ini(php_path):
            return False

        # Corregir extension_dir
        if not self.fix_extension_dir(php_path):
            return False

        # Habilitar extensiones necesarias
        self.print_colored("🔧 Habilitando extensiones necesarias...", "yellow")
        for extension in self.required_extensions:
            self.set_php_extension(php_path, extension, enable=True)

        # Instalar Composer
        composer_phar = os.path.join(php_path, "composer.phar")
        target_version = composer_version

        if not target_version and version in self.default_composer_versions:
            target_version = self.default_composer_versions[version]

        if not target_version:
            target_version = "2.8.10"

        if not os.path.exists(composer_phar):
            self.print_colored(f"📦 Instalando Composer v{target_version}...", "yellow")
            self.install_composer(php_path, target_version)
        else:
            self.print_colored("ℹ️  Composer ya está presente.", "gray")

        return True

    def fix_extension_dir(self, php_path: str) -> bool:
        """Corrige el extension_dir en php.ini"""
        try:
            ini_file = os.path.join(php_path, "php.ini")
            if not os.path.exists(ini_file):
                self.print_colored("❌ No se encontró php.ini", "red")
                return False

            # Leer archivo php.ini
            with open(ini_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Corregir extension_dir (Windows)
            # extension_dir = os.path.join(php_path, "ext").replace("\\", "/")
            extension_dir = "ext"

            # Buscar y reemplazar extension_dir
            lines = content.split('\n')
            modified = False

            for i, line in enumerate(lines):
                if line.strip().startswith(';extension_dir') or line.strip().startswith('extension_dir'):
                    lines[i] = f'extension_dir = "{extension_dir}"'
                    modified = True
                    break

            if modified:
                # Escribir archivo modificado
                with open(ini_file, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(lines))

                self.print_colored(f"✅ extension_dir configurado a: {extension_dir}", "green")

            return True

        except Exception as e:
            self.print_colored(f"❌ Error al corregir extension_dir: {str(e)}", "red")
            return False

    def enable_required_extensions(self, php_path: str):
        ini_path = os.path.join(php_path, "php.ini")
        if not os.path.exists(ini_path): return
        with open(ini_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        for i, line in enumerate(lines):
            for ext in self.required_extensions:
                dll = f"php_{ext}.dll"
                if dll in line and line.strip().startswith(';'):
                    lines[i] = line.lstrip('; ').rstrip() + '\n'
                    self.print_colored(f"✅ {ext} habilitado", "green")
                    break
        with open(ini_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)

    def _escape_apache_path(self, path: str) -> str:
        """Convierte una ruta de Windows en formato seguro para Apache (usa / o \\ correctamente)"""
        # Opción 1: Usar barras normales (recomendado para Apache en Windows)
        return path.replace('\\', '/')

        # Opción 2: Usar dobles barras invertidas (también válido)
        # return path.replace('\\', '\\\\')

    def update_apache_config(php_path: str, apache_conf: str, apache_bin: str) -> bool:
        """
        Actualiza la configuración de Apache para usar una versión específica de PHP.
        Basado en el script PowerShell Update-ApacheConfig.
        """
        php_exe = os.path.join(php_path, "php.exe")

        # Verificar que PHP exista
        if not os.path.exists(php_exe):
            print(f"❌ PHP no encontrado en: {php_exe}")
            return False

        # Verificar que httpd.conf exista
        if not os.path.exists(apache_conf):
            print(f"❌ Archivo de configuración de Apache no encontrado: {apache_conf}")
            return False

        # Verificar que httpd.exe exista
        if not os.path.exists(apache_bin):
            print(f"❌ Ejecutable de Apache no encontrado: {apache_bin}")
            return False

        # Determinar versión de PHP (7.x o 8.x)
        try:
            result = subprocess.run(
                [php_exe, "-r", "echo substr(PHP_VERSION, 0, 3);"],
                capture_output=True, text=True, check=True
            )
            php_version = result.stdout.strip()
            is_php7 = php_version.startswith("7.")
        except subprocess.CalledProcessError as e:
            print(f"❌ No se pudo obtener la versión de PHP: {e}")
            return False

        # Definir nombres de archivos según versión
        sapi_dll = "php7apache2_4.dll" if is_php7 else "php8apache2_4.dll"
        ts_dll = "php7ts.dll" if is_php7 else "php8ts.dll"
        module_line = "php7_module" if is_php7 else "php_module"

        sapi_dll_path = os.path.join(php_path, sapi_dll)
        ts_dll_path = os.path.join(php_path, ts_dll)

        # Verificar que los archivos necesarios existan
        missing = []
        if not os.path.exists(sapi_dll_path):
            missing.append(sapi_dll)
        if not os.path.exists(ts_dll_path):
            missing.append(ts_dll)

        if missing:
            print(f"❌ Faltan archivos en {php_path}: {', '.join(missing)}")
            return False

        print(f"🔧 Actualizando configuración de Apache para PHP {php_version}...")

        # Archivo temporal
        temp_conf = f"{apache_conf}.tmp"

        try:
            # Leer configuración actual
            with open(apache_conf, 'r', encoding='utf-8') as f:
                content = f.readlines()

            # Filtrar líneas antiguas de PHP
            new_content = []
            skip_next = False  # Para manejar líneas en bloque si es necesario
            for line in content:
                line_stripped = line.strip()

                # Saltar líneas relacionadas con módulos PHP anteriores
                if any(pattern in line_stripped for pattern in [
                    "LoadModule php_module",
                    "LoadModule php7_module",
                    "PHPIniDir",
                    "AddType application/x-httpd-php",
                    "LoadFile"
                ]):
                    # Pero también verificar si contiene nombres específicos
                    if (sapi_dll in line or ts_dll in line or
                            "php_module" in line or "application/x-httpd-php" in line):
                        continue
                    # Si no es de la versión actual, igual la omitimos
                    continue

                new_content.append(line)

            # Añadir nueva configuración
            new_content.append("\n")
            new_content.append("# Configuración de PHP generada automáticamente\n")
            new_content.append(f'LoadModule {module_line} "{sapi_dll_path.replace("\\", "/")}"\n')
            new_content.append('AddType application/x-httpd-php .php\n')
            new_content.append(f'PHPIniDir "{php_path.replace("\\", "/")}"\n')
            new_content.append(f'LoadFile "{ts_dll_path.replace("\\", "/")}"\n')

            # Escribir archivo temporal
            with open(temp_conf, 'w', encoding='utf-8') as f:
                f.writelines(new_content)

            # Validar configuración de Apache
            print("🔍 Validando configuración de Apache...")
            result = subprocess.run([apache_bin, "-t"], capture_output=True, text=True)

            if result.returncode != 0:
                print("❌ Configuración de Apache inválida:")
                for line in result.stderr.splitlines():
                    print(f"  {line}")
                os.remove(temp_conf)
                return False

            # Reemplazar archivo original
            shutil.move(temp_conf, apache_conf)
            print("✅ Configuración de Apache actualizada.")

            # Reiniciar Apache
            print("🔄 Reiniciando Apache...")
            stop_result = subprocess.run(["net", "stop", "Apache2.4"], capture_output=True, text=True)
            subprocess.run(["timeout", "2"], shell=True)  # Espera 2 segundos
            start_result = subprocess.run(["net", "start", "Apache2.4"], capture_output=True, text=True)

            if start_result.returncode == 0:
                print("✅ Apache reiniciado correctamente.")
                return True
            else:
                print("❌ Error al reiniciar Apache. Verifica el servicio.")
                print(start_result.stderr)
                return False

        except Exception as e:
            print(f"❌ Error al actualizar Apache: {e}")
            if os.path.exists(temp_conf):
                try:
                    os.remove(temp_conf)
                except:
                    pass
            return False

    def ensure_rewrite_module_enabled(self):
        """Ensure mod_rewrite is enabled by uncommenting the LoadModule line in httpd.conf"""
        self.print_colored("🔧 Asegurando que mod_rewrite esté habilitado...", "yellow")

        if not os.path.exists(self.apache_conf):
            self.print_colored(f"❌ Archivo de configuración no encontrado: {self.apache_conf}", "red")
            return False

        try:
            with open(self.apache_conf, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            updated = False
            new_lines = []

            for line in lines:
                stripped = line.strip()
                # Detectar línea comentada de mod_rewrite
                if stripped.startswith("#LoadModule rewrite_module") and "mod_rewrite.so" in stripped:
                    new_lines.append("LoadModule rewrite_module modules/mod_rewrite.so\n")
                    updated = True
                    self.print_colored("✅ mod_rewrite habilitado", "green")
                else:
                    new_lines.append(line)

            # Solo guardar si se hizo un cambio
            if updated:
                with open(self.apache_conf, 'w', encoding='utf-8') as f:
                    f.writelines(new_lines)
                self.print_colored("💾 Cambios guardados en httpd.conf", "green")
            else:
                # Verificar si ya está habilitado
                if any("LoadModule rewrite_module modules/mod_rewrite.so" in line and not line.strip().startswith('#')
                       for line in lines):
                    self.print_colored("✅ mod_rewrite ya está habilitado", "green")
                else:
                    self.print_colored("❌ No se encontró la directiva LoadModule para mod_rewrite", "red")
                    return False

            return True

        except Exception as e:
            self.print_colored(f"❌ Error al modificar httpd.conf: {str(e)}", "red")
            return False


class PHPLinkParser(HTMLParser):
    """Parser HTML personalizado para extraer enlaces de archivos ZIP de PHP"""

    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() == 'a':
            for name, value in attrs:
                if name.lower() == 'href' and value and value.endswith('.zip'):
                    self.links.append(value)


def main():
    parser = argparse.ArgumentParser(description="PHP Version Manager", add_help=False)
    parser.add_argument("-v", "--version", help="Versión de PHP (para CLI o Info)")
    parser.add_argument("-l", "--list", action="store_true", help="Listar versiones disponibles")
    parser.add_argument("-i", "--info", action="store_true", help="Mostrar información detallada de PHP")
    parser.add_argument("--install", action="store_true", help="Instalar una versión de PHP")
    parser.add_argument("--fix-ini", action="store_true", help="Corregir php.ini (extensiones, extension_dir)")
    parser.add_argument("--setup-multiversion", action="store_true", help="Configurar Apache para multi-versión")
    parser.add_argument("-d", "--directory", help="Directorio para mapeo")
    parser.add_argument("-a", "--alias", help="Alias para el mapeo")
    parser.add_argument("--show-mappings", action="store_true", help="Mostrar mappings actuales")
    parser.add_argument("--remove-mapping", action="store_true", help="Eliminar un mapping por alias")
    parser.add_argument("--scan", action="store_true", help="Escanea versiones PHP disponibles online")
    parser.add_argument("--command", help="Ejecutar un comando PHP")
    parser.add_argument("--help", "-h", action="store_true", help="Mostrar ayuda")

    args = parser.parse_args()
    manager = PHPVersionManager()

    # Mostrar ayuda si no hay argumentos o si se pide explícitamente
    if len(sys.argv) == 1 or args.help:
        manager.show_help()
        return

    # === Lógica principal (ordenada como en el PS1) ===

    if args.list:
        manager.get_php_versions()
        return

    if args.setup_multiversion:
        manager.setup_apache_multiversion()
        return

    if args.directory and args.version and args.alias:
        if manager.add_directory_mapping(args.directory, args.version, args.alias):
            print("")
            manager.print_colored("🔧 Actualizando Virtual Hosts...", "yellow")
            manager.update_virtual_hosts()
            print("")
            manager.print_colored("✅ Configuración completada. Reinicia Apache para aplicar cambios:", "green")
            print("   net stop Apache2.4 && net start Apache2.4")
            print("")
            manager.print_colored(f"🌐 Accede a tu sitio en: http://localhost/{args.alias}", "yellow")
        return

    if args.show_mappings:
        manager.show_directory_mappings()
        return

    if args.remove_mapping and args.alias:
        if manager.remove_directory_mapping(args.alias):
            manager.print_colored("🔧 Actualizando Virtual Hosts...", "yellow")
            manager.update_virtual_hosts()
            manager.print_colored("✅ Reinicia Apache para aplicar cambios.", "green")
        return

    if args.install:
        if not args.version:
            manager.print_colored("❌ Usa: --install -v <versión>", "red")
            return
        manager.install_php_version(args.version)
        return

    if args.fix_ini:
        if not args.version:
            manager.print_colored("❌ Usa: --fix-ini -v <versión>", "red")
            return
        php_path = manager.available_versions.get(args.version)
        if not php_path:
            manager.print_colored(f"❌ Versión no reconocida: {args.version}", "red")
            return
        manager.print_colored(f"🔧 Corrigiendo php.ini para PHP {args.version}...", "yellow")
        manager.fix_extension_dir(php_path)
        manager.enable_required_extensions(php_path)
        return

    if args.version:
        php_path = manager.available_versions.get(args.version)
        if not php_path:
            manager.print_colored(f"❌ Versión no reconocida: {args.version}", "red")
            return
        php_exe = os.path.join(php_path, "php.exe")
        if not os.path.exists(php_exe):
            manager.print_colored(f"PHP {args.version} no está instalado. Instalando...", "yellow")
            if not manager.install_php_version(args.version):
                return  # Si falla la instalación, no continuamos

        # Simular cambio de versión CLI (solo informativo)
        manager.print_colored(f"🟢 PHP {args.version} listo para usar", "green")
        print(f"📁 Ruta: {php_path}")
        manager.print_colored("💡 Para usarlo en este terminal, ejecuta:", "gray")
        print(f"   set PATH={php_path};%PATH%")

        # Mensaje contextual si se quiere configurar Apache
        if not args.info and not args.command:
            print("")
            manager.print_colored("🔧 Nota: Para configurar Apache multi-versión, usa:", "yellow")
            print("   python php_manager.py --setup-multiversion")
            print(f"   python php_manager.py -d 'C:\\www\\proyecto' -v {args.version} -a proyecto")
        return

    if args.scan:
        manager.print_colored("🔍 Escaneando versiones PHP disponibles...", "cyan")
        versions = manager.scan_online_php_versions()

        # Si no hay resultados online, muestra el fallback
        if not versions:
            manager.print_colored("⚠️  Usando URLs estáticas (sin conexión)", "yellow")
            versions = {
                "7.1": {"url": "https://windows.php.net/downloads/releases/archives/php-7.1.9-Win32-VC14-x64.zip"},
                "7.3": {"url": "https://windows.php.net/downloads/releases/archives/php-7.3.9-Win32-VC15-x64.zip"},
                "7.4": {"url": "https://windows.php.net/downloads/releases/php-7.4.33-Win32-vs16-x64.zip"},
                "8.0": {"url": "https://windows.php.net/downloads/releases/php-8.0.30-Win32-vs16-x64.zip"},
                "8.1": {"url": "https://windows.php.net/downloads/releases/php-8.1.33-Win32-vs16-x64.zip"},
                "8.2": {"url": "https://windows.php.net/downloads/releases/php-8.2.29-Win32-vs16-x64.zip"},
                "8.3": {"url": "https://windows.php.net/downloads/releases/php-8.3.24-Win32-vs16-x64.zip"},
                "8.4": {"url": "https://windows.php.net/downloads/releases/php-8.4.0-Win32-vs16-x64.zip"}
            }

        print("\n📋 Resumen de versiones Thread Safe x64 disponibles:")
        for ver in sorted(versions.keys(), key=lambda v: [int(x) for x in v.split('.')]):
            data = versions[ver]
            print(f"  • PHP {ver}")
            print(f"    {data['url']}")
        return

    if args.info:
        if not args.version:
            manager.print_colored("❌ Usa -i -v <versión> para mostrar información.", "red")
            return
        php_path = manager.available_versions.get(args.version)
        if not php_path:
            manager.print_colored(f"❌ Versión no reconocida: {args.version}", "red")
            return
        php_exe = os.path.join(php_path, "php.exe")
        if not os.path.exists(php_exe):
            manager.print_colored(f"❌ PHP {args.version} no está instalado.", "red")
            return
        manager.show_php_info(php_path)
        return

    if args.command:
        manager.print_colored(f"▶️ Ejecutando: {args.command}", "cyan")
        os.system(args.command)
        return

    # Si llega aquí, comando no reconocido
    manager.show_help()


if __name__ == "__main__":
    main()
