# lamp_manager/core/config.py

from pathlib import Path
import yaml
from typing import Optional

class LAMPConfig:
    """Gestión centralizada de configuración"""

    DEFAULT_CONFIG = {
        'apache': {
            'sites_dir': '/var/www',
            'vhosts_dir': '/etc/apache2/sites-available',
            'doc_root_subdir': 'web',  # Subdirectorio común para frameworks
            'default_php_version': '8.2',
            'enable_ssl': True,
        },
        'mysql': {
            'root_password': None,  # Debe configurarse
            'default_charset': 'utf8mb4',
            'default_collation': 'utf8mb4_unicode_ci',
        },
        'php': {
            'supported_versions': ['7.4', '8.1', '8.2', '8.3'],
            'ppa_repository': 'ppa:ondrej/php',
        },
        'drupal': {
            'default_profile': 'standard',
            'default_version': '^10',
            'composer_path': '/usr/local/bin/composer',
        },
        'security': {
            'require_sudo': True,
            'backup_before_changes': True,
            'dry_run_by_default': False,
        }
    }

    def __init__(self, config_file: Optional[Path] = None):
        self.config_file = config_file or Path('/etc/lamp-manager/config.yml')
        self.config = self._load_config()

    def _load_config(self) -> dict:
        """Carga configuración desde archivo o usa defaults"""
        if self.config_file.exists():
            try:
                with open(self.config_file) as f:
                    user_config = yaml.safe_load(f)
                    # Merge con defaults (simple merge, not deep)
                    merged_config = self.DEFAULT_CONFIG.copy()
                    if user_config:
                        for key, value in user_config.items():
                            if key in merged_config and isinstance(merged_config[key], dict):
                                merged_config[key].update(value)
                            else:
                                merged_config[key] = value
                    return merged_config
            except (yaml.YAMLError, IOError) as e:
                print(f"Warning: Could not load or parse config file {self.config_file}. Using defaults. Error: {e}")
                return self.DEFAULT_CONFIG.copy()
        return self.DEFAULT_CONFIG.copy()

    def get(self, key_path: str, default=None):
        """
        Obtiene valor de configuración usando dot notation.
        Ej: config.get('apache.default_php_version')
        """
        keys = key_path.split('.')
        value = self.config
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                return default
        return value if value is not None else default
