# unified_stack_manager/core/config.py

import yaml
from pathlib import Path
from typing import Optional, Dict, Any

from unified_stack_manager.platform.detector import platform_info, PlatformEnum

def deep_merge(source: Dict, destination: Dict) -> Dict:
    """
    Fusiona dos diccionarios de forma recursiva.
    """
    for key, value in source.items():
        if isinstance(value, dict):
            node = destination.setdefault(key, {})
            deep_merge(value, node)
        else:
            destination[key] = value
    return destination

class UnifiedConfig:
    """
    Gestión de configuración unificada y jerárquica.
    Carga y fusiona la configuración desde múltiples fuentes:
    1. default.yml (base)
    2. <os>.yml (específica de la plataforma)
    3. Archivo de usuario (opcional)
    """

    def __init__(self, config_file: Optional[Path] = None):
        self.platform = platform_info
        self.base_config_path = self._get_base_config_path()
        self.user_config_file = config_file
        self.config = self._load_config()

    def _get_base_config_path(self) -> Path:
        """Determina el directorio de configuración base (repo root o sistema)."""
        # Para desarrollo, usamos el directorio 'config/' en la raíz del repo.
        repo_config_path = Path(__file__).resolve().parents[2] / 'config'
        if repo_config_path.exists():
            return repo_config_path
        # Para producción, usamos la ruta del sistema.
        return self.platform.get_config_path()

    def _load_config(self) -> Dict[str, Any]:
        """Carga y fusiona las configuraciones."""
        # 1. Cargar config por defecto (default.yml)
        default_config_path = self.base_config_path / 'default.yml'
        config = self._read_yaml(default_config_path)

        # 2. Cargar config específica del OS (linux.yml o windows.yml)
        os_specific_config_path = self.base_config_path / f"{self.platform.os.value}.yml"
        os_config = self._read_yaml(os_specific_config_path)
        if os_config:
            config = deep_merge(os_config, config)

        # 3. Cargar config del usuario si se proporciona
        if self.user_config_file:
            user_config = self._read_yaml(self.user_config_file)
            if user_config:
                config = deep_merge(user_config, config)

        return config

    def _read_yaml(self, file_path: Path) -> Dict[str, Any]:
        """Lee un archivo YAML y devuelve su contenido."""
        if not file_path.exists():
            return {}
        try:
            with open(file_path, 'r') as f:
                return yaml.safe_load(f) or {}
        except (yaml.YAMLError, IOError) as e:
            print(f"Warning: Could not load or parse config file {file_path}. Skipping. Error: {e}")
            return {}

    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Obtiene un valor de la configuración usando notación de puntos.
        Ej: config.get('apache.sites_dir')
        """
        keys = key_path.split('.')
        value = self.config
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
                if value is None:
                    return default
            else:
                return default
        return value

    @property
    def is_windows(self) -> bool:
        return self.platform.os == PlatformEnum.WINDOWS

    @property
    def is_linux(self) -> bool:
        return self.platform.os == PlatformEnum.LINUX
