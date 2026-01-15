# unified_stack_manager/platform/detector.py

import platform
import sys
from enum import Enum
from typing import Optional
from pathlib import Path
import os

class PlatformEnum(Enum):
    """Plataformas soportadas"""
    WINDOWS = "windows"
    LINUX = "linux"
    MACOS = "macos"
    UNKNOWN = "unknown"

class LinuxDistribution(Enum):
    """Distribuciones Linux soportadas"""
    UBUNTU = "ubuntu"
    DEBIAN = "debian"
    RHEL = "rhel"
    CENTOS = "centos"
    ROCKY = "rocky"
    FEDORA = "fedora"
    UNKNOWN = "unknown"

class PlatformInfo:
    """Información detallada de la plataforma"""

    def __init__(self):
        self.os = self._detect_os()
        self.distribution = self._detect_distribution()
        self.version = self._detect_version()
        self.architecture = platform.machine()
        self.is_admin = self._check_admin_privileges()

    def _detect_os(self) -> PlatformEnum:
        """Detecta el sistema operativo"""
        system = platform.system().lower()

        if system == 'windows':
            return PlatformEnum.WINDOWS
        elif system == 'linux':
            return PlatformEnum.LINUX
        elif system == 'darwin':
            return PlatformEnum.MACOS
        else:
            return PlatformEnum.UNKNOWN

    def _detect_distribution(self) -> Optional[LinuxDistribution]:
        """Detecta la distribución Linux (si aplica)"""
        if self.os != PlatformEnum.LINUX:
            return None

        try:
            with open('/etc/os-release') as f:
                for line in f:
                    if line.startswith('ID='):
                        distro_id = line.split('=')[1].strip().strip('"').lower()

                        if distro_id == 'ubuntu':
                            return LinuxDistribution.UBUNTU
                        elif distro_id == 'debian':
                            return LinuxDistribution.DEBIAN
                        elif distro_id in ['rhel', 'redhat']:
                            return LinuxDistribution.RHEL
                        elif distro_id == 'centos':
                            return LinuxDistribution.CENTOS
                        elif distro_id == 'rocky':
                            return LinuxDistribution.ROCKY
                        elif distro_id == 'fedora':
                            return LinuxDistribution.FEDORA
        except FileNotFoundError:
            pass

        return LinuxDistribution.UNKNOWN

    def _detect_version(self) -> str:
        """Detecta la versión del OS"""
        if self.os == PlatformEnum.WINDOWS:
            return platform.release()  # '10', '11', etc.
        elif self.os == PlatformEnum.LINUX:
            try:
                with open('/etc/os-release') as f:
                    for line in f:
                        if line.startswith('VERSION_ID='):
                            return line.split('=')[1].strip().strip('"')
            except FileNotFoundError:
                pass

        return 'unknown'

    def _check_admin_privileges(self) -> bool:
        """Verifica si se ejecuta con privilegios de administrador"""
        if self.os == PlatformEnum.WINDOWS:
            try:
                import ctypes
                return ctypes.windll.shell32.IsUserAnAdmin() != 0
            except:
                return False
        else:  # Linux/Unix
            return os.geteuid() == 0

    def is_supported(self) -> bool:
        """Verifica si la plataforma está soportada"""
        if self.os == PlatformEnum.WINDOWS:
            return True
        elif self.os == PlatformEnum.LINUX:
            return self.distribution in [
                LinuxDistribution.UBUNTU,
                LinuxDistribution.DEBIAN,
                LinuxDistribution.RHEL,
                LinuxDistribution.CENTOS,
                LinuxDistribution.ROCKY,
            ]
        return False

    def get_config_path(self) -> Path:
        """Retorna el path de configuración según el OS"""
        if self.os == PlatformEnum.WINDOWS:
            return Path(os.environ.get('PROGRAMDATA', 'C:\\ProgramData')) / 'UnifiedStackManager'
        else:
            return Path('/etc/unified-stack-manager')

    def get_data_path(self) -> Path:
        """Retorna el path de datos según el OS"""
        if self.os == PlatformEnum.WINDOWS:
            return Path(os.environ.get('PROGRAMDATA', 'C:\\ProgramData')) / 'UnifiedStackManager' / 'data'
        else:
            return Path('/var/lib/unified-stack-manager')

    def get_log_path(self) -> Path:
        """Retorna el path de logs según el OS"""
        if self.os == PlatformEnum.WINDOWS:
            return Path(os.environ.get('PROGRAMDATA', 'C:\\ProgramData')) / 'UnifiedStackManager' / 'logs'
        else:
            return Path('/var/log/unified-stack-manager')

    def __str__(self) -> str:
        """Representación legible"""
        if self.os == PlatformEnum.LINUX:
            return f"{self.os.value} ({self.distribution.value} {self.version})"
        return f"{self.os.value} {self.version}"


# Instancia global para uso conveniente
platform_info = PlatformInfo()
