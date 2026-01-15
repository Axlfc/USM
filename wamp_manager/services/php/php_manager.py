# services/php/php_manager.py
import os
import subprocess
import requests
from typing import Dict, Optional
from ..base_service import BaseService

print("PHP")

class PHPManager(BaseService):
    def __init__(self, base_path: str = "C:\\"):
        super().__init__()
        self.base_path = base_path
        self.available_versions = {
            "7.4": f"{base_path}php7.4",
            "8.0": f"{base_path}php8.0",
            "8.1": f"{base_path}php8.1",
            "8.2": f"{base_path}php8.2",
            "8.3": f"{base_path}php8.3",
            "8.4": f"{base_path}php8.4",
        }

    def install_version(self, version: str, force: bool = False) -> bool:
        if version not in self.available_versions:
            self.print_colored(f"❌ Versión {version} no soportada", "red")
            return False

        php_path = self.available_versions[version]
        if os.path.exists(php_path) and not force:
            self.print_colored(f"✅ PHP {version} ya instalado", "green")
            return True

        url = self._get_download_url(version)
        if not url:
            return False

        zip_path = os.path.join(self.base_path, f"php-{version}.zip")
        if not self._download_file(url, zip_path):
            return False

        return self._extract_php(zip_path, php_path)

    def _get_download_url(self, version: str) -> Optional[str]:
        # Use web scraping or fallback
        # (Implement get_latest_php_versions_from_web logic here)
        pass

    def _download_file(self, url: str, dest: str) -> bool:
        try:
            with requests.get(url, stream=True) as r:
                r.raise_for_status()
                with open(dest, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
            return True
        except Exception as e:
            self.print_colored(f"❌ Error descargando: {e}", "red")
            return False

    def _extract_php(self, zip_path: str, php_path: str) -> bool:
        try:
            import zipfile
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(php_path)
            os.remove(zip_path)
            return bool(os.path.exists(os.path.join(php_path, "php.exe")))
        except Exception as e:
            self.print_colored(f"❌ Error al descomprimir: {e}", "red")
            return False

    def get_version(self, php_path: str) -> Optional[str]:
        try:
            result = subprocess.run(
                [os.path.join(php_path, "php.exe"), "-r", "echo PHP_VERSION;"],
                capture_output=True, text=True, check=True
            )
            return result.stdout.strip()
        except:
            return None