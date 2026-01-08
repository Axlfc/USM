# services/apache/apache_manager.py
import os
import subprocess
from typing import List, Optional
from ..base_service import BaseService

print("APACHE")

class ApacheManager(BaseService):
    def __init__(self, apache_root: str = "C:\\APACHE24"):
        super().__init__()
        self.apache_root = apache_root
        self.conf_path = os.path.join(apache_root, "conf", "httpd.conf")
        self.bin_path = os.path.join(apache_root, "bin", "httpd.exe")
        self.modules_path = os.path.join(apache_root, "modules")

    def verify_installation(self) -> bool:
        if not os.path.exists(self.bin_path):
            self.print_colored("❌ Apache no encontrado", "red")
            return False
        return True

    def create_backup(self) -> Optional[str]:
        import shutil
        from datetime import datetime
        backup = f"{self.conf_path}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        try:
            shutil.copy2(self.conf_path, backup)
            self.print_colored(f"📁 Backup creado: {backup}", "blue")
            return backup
        except Exception as e:
            self.print_colored(f"❌ No se pudo crear backup: {e}", "red")
            return None

    def update_php_module(self, php_path: str) -> bool:
        if not os.path.exists(self.conf_path):
            self.print_colored("❌ Archivo de configuración no encontrado", "red")
            return False

        try:
            with open(self.conf_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            new_lines = [line for line in lines if not self._is_php_line(line)]

            # Detect PHP version
            php_exe = os.path.join(php_path, "php.exe")
            is_php7 = "7." in (self._run_php_get_version(php_exe) or "")

            module_name = "php7_module" if is_php7 else "php_module"
            dll_name = "php7apache2_4.dll" if is_php7 else "php8apache2_4.dll"
            ts_name = "php7ts.dll" if is_php7 else "php8ts.dll"

            dll_path = os.path.join(php_path, dll_name)
            ts_path = os.path.join(php_path, ts_name)

            if not os.path.exists(dll_path):
                self.print_colored(f"❌ No se encontró {dll_name}", "red")
                return False

            new_lines.extend([
                "\n# Configuración PHP Automática\n",
                f'LoadModule {module_name} "{dll_path.replace("\\", "/")}"\n',
                'AddType application/x-httpd-php .php\n',
                f'PHPIniDir "{php_path.replace("\\", "/")}"\n',
                f'LoadFile "{ts_path.replace("\\", "/")}"\n'
            ])

            temp_path = self.conf_path + ".tmp"
            with open(temp_path, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)

            # Validate config
            result = subprocess.run([self.bin_path, "-t"], capture_output=True, text=True)
            if result.returncode != 0:
                self.print_colored(f"❌ Config inválida:\n{result.stderr}", "red")
                return False

            # Apply
            os.replace(temp_path, self.conf_path)
            self.print_colored("✅ Configuración de Apache actualizada", "green")
            return True

        except Exception as e:
            self.print_colored(f"❌ Error actualizando Apache: {e}", "red")
            return False

    def _is_php_line(self, line: str) -> bool:
        return any(x in line for x in ["LoadModule php_", "PHPIniDir", "AddType application/x-httpd-php", "LoadFile"])

    def _run_php_get_version(self, php_exe: str) -> Optional[str]:
        try:
            result = subprocess.run([php_exe, "-r", "echo substr(PHP_VERSION,0,3);"], capture_output=True, text=True)
            return result.stdout.strip()
        except:
            return None

    def restart(self) -> bool:
        try:
            subprocess.run(["net", "stop", "Apache2.4"], check=True, capture_output=True)
            subprocess.run(["net", "start", "Apache2.4"], check=True, capture_output=True)
            self.print_colored("✅ Apache reiniciado", "green")
            return True
        except subprocess.CalledProcessError as e:
            self.print_colored(f"❌ Error al reiniciar Apache: {e}", "red")
            return False