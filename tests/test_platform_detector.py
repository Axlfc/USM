# tests/test_platform_detector.py

import pytest
from unittest.mock import MagicMock, patch
import platform

from unified_stack_manager.platform.detector import PlatformEnum, LinuxDistribution

# Mock de la clase PlatformInfo para no depender del sistema real donde se ejecutan los tests
@pytest.fixture
def mock_platform_info(monkeypatch):
    """Mockea las funciones de bajo nivel usadas por PlatformInfo."""
    monkeypatch.setattr('platform.system', MagicMock())
    monkeypatch.setattr('platform.release', MagicMock())
    monkeypatch.setattr('platform.machine', MagicMock(return_value='x86_64'))
    monkeypatch.setattr('os.geteuid', MagicMock(return_value=0)) # Simular admin

    # Mock para la lectura de /etc/os-release
    mock_open = patch('builtins.open', MagicMock())
    monkeypatch.setattr('builtins.open', mock_open.start())

    yield

    mock_open.stop()


def test_detect_os_windows(mock_platform_info):
    """Prueba que el detector identifica Windows correctamente."""
    from unified_stack_manager.platform.detector import PlatformInfo

    platform.system.return_value = 'Windows'
    platform.release.return_value = '10'

    info = PlatformInfo()

    assert info.os == PlatformEnum.WINDOWS
    assert info.version == '10'
    assert info.distribution is None

def test_detect_os_linux_ubuntu(mock_platform_info):
    """Prueba que el detector identifica Ubuntu correctamente."""
    from unified_stack_manager.platform.detector import PlatformInfo

    platform.system.return_value = 'Linux'

    # Simular el contenido de /etc/os-release para Ubuntu
    os_release_content = [
        'ID=ubuntu\n',
        'VERSION_ID="22.04"\n'
    ]
    open.return_value.__enter__.return_value = os_release_content

    info = PlatformInfo()

    assert info.os == PlatformEnum.LINUX
    assert info.distribution == LinuxDistribution.UBUNTU
    assert info.version == "22.04"

def test_detect_os_linux_rocky(mock_platform_info):
    """Prueba que el detector identifica Rocky Linux correctamente."""
    from unified_stack_manager.platform.detector import PlatformInfo

    platform.system.return_value = 'Linux'

    os_release_content = [
        'ID=rocky\n',
        'VERSION_ID="9"\n'
    ]
    open.return_value.__enter__.return_value = os_release_content

    info = PlatformInfo()

    assert info.os == PlatformEnum.LINUX
    assert info.distribution == LinuxDistribution.ROCKY
    assert info.version == "9"

def test_is_supported(mock_platform_info):
    """Prueba la lógica de la función is_supported."""
    from unified_stack_manager.platform.detector import PlatformInfo

    # Soportado en Windows
    platform.system.return_value = 'Windows'
    info = PlatformInfo()
    assert info.is_supported()

    # Soportado en Ubuntu
    platform.system.return_value = 'Linux'
    open.return_value.__enter__.return_value = ['ID=ubuntu\n']
    info = PlatformInfo()
    assert info.is_supported()

    # No soportado en una distribución desconocida de Linux
    open.return_value.__enter__.return_value = ['ID=arch\n']
    info = PlatformInfo()
    assert not info.is_supported()
