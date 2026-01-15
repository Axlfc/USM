# tests/test_config.py

import unittest
from unittest.mock import patch, mock_open
from pathlib import Path
import yaml
from lamp_manager.core.config import LAMPConfig

class TestConfig(unittest.TestCase):

    def test_default_config_loading(self):
        """Test that default config is loaded when no file is present."""
        with patch('pathlib.Path.exists') as mock_exists:
            mock_exists.return_value = False
            config = LAMPConfig()
            self.assertEqual(config.get('apache.default_php_version'), '8.2')
            self.assertEqual(config.get('security.require_sudo'), True)

    def test_user_config_overrides_defaults(self):
        """Test that a user YAML file correctly overrides default values."""
        mock_yaml_content = """
apache:
    default_php_version: '8.1'
security:
    require_sudo: false
"""
        with patch('pathlib.Path.exists') as mock_exists:
            mock_exists.return_value = True
            with patch('builtins.open', mock_open(read_data=mock_yaml_content)):
                config = LAMPConfig(config_file=Path('/fake/path/config.yml'))
                # Test overridden values
                self.assertEqual(config.get('apache.default_php_version'), '8.1')
                self.assertEqual(config.get('security.require_sudo'), False)
                # Test that non-overridden default values are still present
                self.assertEqual(config.get('mysql.default_charset'), 'utf8mb4')

    def test_get_with_dot_notation(self):
        """Test the .get() method with dot notation."""
        with patch('pathlib.Path.exists') as mock_exists:
            mock_exists.return_value = False
            config = LAMPConfig()
            self.assertEqual(config.get('mysql.default_collation'), 'utf8mb4_unicode_ci')

    def test_get_with_default_value(self):
        """Test that .get() returns the default value for a non-existent key."""
        with patch('pathlib.Path.exists') as mock_exists:
            mock_exists.return_value = False
            config = LAMPConfig()
            self.assertEqual(config.get('non.existent.key', 'default_val'), 'default_val')

if __name__ == '__main__':
    unittest.main()
