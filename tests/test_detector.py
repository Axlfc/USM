# tests/test_detector.py

import unittest
from unittest.mock import patch
from lamp_manager.platform.detector import detect_platform

class TestDetector(unittest.TestCase):

    @patch('platform.system')
    def test_detect_platform_linux(self, mock_system):
        mock_system.return_value = 'Linux'
        self.assertEqual(detect_platform(), 'linux')

    @patch('platform.system')
    def test_detect_platform_windows(self, mock_system):
        mock_system.return_value = 'Windows'
        self.assertEqual(detect_platform(), 'windows')

    @patch('platform.system')
    def test_detect_platform_unsupported(self, mock_system):
        mock_system.return_value = 'Darwin'
        self.assertEqual(detect_platform(), 'unsupported')

if __name__ == '__main__':
    unittest.main()
