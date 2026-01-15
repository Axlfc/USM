# lamp_manager/platform/detector.py

import platform
import sys

def detect_platform() -> str:
    """
    Detecta la plataforma actual.

    Returns:
        'windows', 'linux', o 'unsupported'
    """
    system = platform.system().lower()

    if system == 'windows':
        return 'windows'
    elif system == 'linux':
        return 'linux'
    elif system == 'darwin':
        return 'unsupported'  # macOS no soportado (por ahora)
    else:
        return 'unsupported'


def get_linux_distribution() -> tuple[str, str]:
    """
    Obtiene información de la distribución Linux.

    Returns:
        (id, version) ej: ('ubuntu', '22.04')
    """
    if platform.system() != 'Linux':
        return ('unknown', 'unknown')

    try:
        with open('/etc/os-release') as f:
            info = {}
            for line in f:
                if '=' in line:
                    key, value = line.strip().split('=', 1)
                    info[key] = value.strip('"')

            return (
                info.get('ID', 'unknown'),
                info.get('VERSION_ID', 'unknown')
            )
    except FileNotFoundError:
        return ('unknown', 'unknown')
