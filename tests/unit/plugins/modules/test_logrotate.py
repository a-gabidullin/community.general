# Copyright (c) 2026 Aleksandr Gabidullin <qualittv@gmail.com>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import sys
import os
import unittest
from unittest.mock import Mock, patch, mock_open, MagicMock
import tempfile
import shutil


class TestLogrotateConfig(unittest.TestCase):
    """Unit tests for the logrotate_config module."""

    @classmethod
    def setUpClass(cls):
        """Set up test environment."""
        # Create a temporary directory for test files
        cls.test_dir = tempfile.mkdtemp()
        
        # Mock ansible modules before importing the actual module
        cls.mock_ansible_basic = Mock()
        cls.mock_ansible_basic.AnsibleModule = Mock()
        
        cls.mock_converters = Mock()
        cls.mock_converters.to_native = lambda x: str(x)
        
        # Patch sys.modules before importing the module
        cls.patcher_basic = patch.dict('sys.modules', {
            'ansible.module_utils.basic': cls.mock_ansible_basic,
            'ansible.module_utils.common.text.converters': cls.mock_converters
        })
        cls.patcher_basic.start()

    @classmethod
    def tearDownClass(cls):
        """Clean up after all tests."""
        # Stop patchers
        cls.patcher_basic.stop()
        
        # Remove temporary directory
        if os.path.exists(cls.test_dir):
            shutil.rmtree(cls.test_dir)

    def setUp(self):
        """Set up test fixtures."""
        # Reset mocks
        self.mock_ansible_basic.AnsibleModule.reset_mock()
        
        # Create fresh module mock
        self.mock_module = Mock()
        self.mock_module.params = {}
        self.mock_module.fail_json = Mock(side_effect=Exception("fail_json called"))
        self.mock_module.exit_json = Mock()
        self.mock_module.check_mode = False
        self.mock_module.get_bin_path = Mock(return_value="/usr/sbin/logrotate")
        self.mock_module.atomic_move = Mock()
        self.mock_module.warn = Mock()
        self.mock_module.run_command = Mock(return_value=(0, "", ""))
        
        self.mock_ansible_basic.AnsibleModule.return_value = self.mock_module
        
        # Create test directories
        self.config_dir = os.path.join(self.test_dir, "logrotate.d")
        os.makedirs(self.config_dir, exist_ok=True)
        
        # Import the module (needs to be done after mocks are set up)
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        
        # Clear any existing import
        for module_name in list(sys.modules.keys()):
            if 'logrotate' in module_name or 'ansible_collections.community.general.plugins.modules' in module_name:
                del sys.modules[module_name]
        
        try:
            from ansible_collections.community.general.plugins.modules import logrotate as logrotate_module
            self.logrotate_module = logrotate_module
        except ImportError:
            # Fallback for local testing
            import logrotate as logrotate_module
            self.logrotate_module = logrotate_module

    def tearDown(self):
        """Clean up after test."""
        # Clean up sys.path
        if os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) in sys.path:
            sys.path.remove(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

    def _setup_module_params(self, **params):
        """Helper to set up module parameters."""
        default_params = {
            'name': 'test',
            'state': 'present',
            'config_dir': self.config_dir,
            'paths': ['/var/log/test/*.log'],
            'rotation_period': 'daily',
            'rotate_count': 7,
            'compress': True,
            'compression_method': 'gzip',
            'delaycompress': False,
            'missingok': True,
            'ifempty': False,
            'notifempty': True,
            'copytruncate': False,
            'dateext': False,
            'dateformat': '-%Y%m%d',
            'sharedscripts': False,
            'enabled': True,
            'backup': False,
        }
        default_params.update(params)
        self.mock_module.params = default_params

    def test_create_new_configuration(self):
        """Test creating a new logrotate configuration."""
        # Setup
        self._setup_module_params()
        
        # Mock file operations
        with patch('os.path.exists', return_value=False) as mock_exists, \
             patch('os.makedirs') as mock_makedirs, \
             patch('builtins.open', mock_open()) as mock_file, \
             patch('os.chmod') as mock_chmod:
            
            # Create LogrotateConfig instance
            config = self.logrotate_module.LogrotateConfig(self.mock_module)
            result = config.apply()
            
            # Assertions
            self.assertTrue(result['changed'])
            self.assertIn('config_file', result)
            self.assertIn('config_content', result)
            self.assertEqual(result['enabled_state'], True)
            
            # Verify file was written
            mock_file.assert_called_once()
            mock_chmod.assert_called_once()

    def test_update_existing_configuration(self):
        """Test updating an existing logrotate configuration."""
        # Setup
        self._setup_module_params(rotate_count=14)
        
        existing_content = """/var/log/test/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
}"""
        
        # Mock file operations
        with patch('os.path.exists', return_value=True) as mock_exists, \
             patch('builtins.open', mock_open(read_data=existing_content)) as mock_file, \
             patch('os.remove') as mock_remove, \
             patch('os.chmod') as mock_chmod:
            
            config = self.logrotate_module.LogrotateConfig(self.mock_module)
            result = config.apply()
            
            # Assertions
            self.assertTrue(result['changed'])
            self.assertIn('14', result['config_content'])  # New rotate count
            
            # Verify old file was removed and new written
            mock_remove.assert_called_once()
            mock_file.assert_called()
            mock_chmod.assert_called_once()

    def test_remove_configuration(self):
        """Test removing a logrotate configuration."""
        # Setup
        self._setup_module_params(state='absent')
        
        config_path = os.path.join(self.config_dir, 'test')
        disabled_path = config_path + '.disabled'
        
        def exists_side_effect(path):
            if path == config_path or path == disabled_path:
                return True
            return False
        
        # Mock file operations
        with patch('os.path.exists', side_effect=exists_side_effect) as mock_exists, \
             patch('os.remove') as mock_remove:
            
            config = self.logrotate_module.LogrotateConfig(self.mock_module)
            result = config.apply()
            
            # Assertions
            self.assertTrue(result['changed'])
            mock_remove.assert_called_once()

    def test_disable_configuration(self):
        """Test disabling a logrotate configuration."""
        # Setup
        self._setup_module_params(enabled=False)
        
        config_path = os.path.join(self.config_dir, 'test')
        disabled_path = config_path + '.disabled'
        
        existing_content = """/var/log/test/*.log {
    daily
    rotate 7
}"""
        
        def exists_side_effect(path):
            if path == config_path:
                return True
            if path == disabled_path:
                return False
            return False
        
        # Mock file operations
        with patch('os.path.exists', side_effect=exists_side_effect) as mock_exists, \
             patch('builtins.open', mock_open(read_data=existing_content)) as mock_file, \
             patch('os.remove') as mock_remove:
            
            config = self.logrotate_module.LogrotateConfig(self.mock_module)
            result = config.apply()
            
            # Assertions
            self.assertTrue(result['changed'])
            self.assertEqual(result['enabled_state'], False)
            self.assertTrue(result['config_file'].endswith('.disabled'))

    def test_enable_configuration(self):
        """Test enabling a disabled logrotate configuration."""
        # Setup
        self._setup_module_params(enabled=True)
        
        config_path = os.path.join(self.config_dir, 'test')
        disabled_path = config_path + '.disabled'
        
        existing_content = """/var/log/test/*.log {
    daily
    rotate 7
}"""
        
        def exists_side_effect(path):
            if path == config_path:
                return False
            if path == disabled_path:
                return True
            return False
        
        # Mock file operations
        with patch('os.path.exists', side_effect=exists_side_effect) as mock_exists, \
             patch('builtins.open', mock_open(read_data=existing_content)) as mock_file:
            
            config = self.logrotate_module.LogrotateConfig(self.mock_module)
            result = config.apply()
            
            # Assertions
            self.assertTrue(result['changed'])
            self.assertEqual(result['enabled_state'], True)
            self.assertFalse(result['config_file'].endswith('.disabled'))

    def test_validation_missing_paths(self):
        """Test validation when paths are missing for new configuration."""
        # Setup
        self._setup_module_params(paths=None)
        
        # Mock file doesn't exist
        with patch('os.path.exists', return_value=False):
            
            config = self.logrotate_module.LogrotateConfig(self.mock_module)
            
            # Should fail during validation
            with self.assertRaises(Exception) as context:
                config.apply()
            
            # Verify fail_json was called
            self.assertIn('fail_json called', str(context.exception))

    def test_validation_size_and_maxsize_exclusive(self):
        """Test validation when both size and maxsize are specified."""
        # Setup
        self._setup_module_params(size='100M', maxsize='200M')
        
        # Mock file doesn't exist
        with patch('os.path.exists', return_value=False):
            
            config = self.logrotate_module.LogrotateConfig(self.mock_module)
            
            # Should fail during validation
            with self.assertRaises(Exception) as context:
                config.apply()
            
            # Verify fail_json was called
            self.assertIn('fail_json called', str(context.exception))

    def test_check_mode(self):
        """Test that no changes are made in check mode."""
        # Setup
        self._setup_module_params()
        self.mock_module.check_mode = True
        
        # Mock file operations
        with patch('os.path.exists', return_value=False) as mock_exists, \
             patch('os.makedirs') as mock_makedirs, \
             patch('builtins.open', mock_open()) as mock_file:
            
            config = self.logrotate_module.LogrotateConfig(self.mock_module)
            result = config.apply()
            
            # Assertions
            self.assertTrue(result['changed'])  # Would change in real mode
            mock_file.assert_not_called()  # No file operations in check mode
            mock_makedirs.assert_called_once()  # Directory creation still happens

    def test_backup_configuration(self):
        """Test backing up configuration before changes."""
        # Setup
        self._setup_module_params(backup=True, rotate_count=14)
        
        existing_content = """/var/log/test/*.log {
    daily
    rotate 7
}"""
        
        # Mock file operations
        with patch('os.path.exists', return_value=True) as mock_exists, \
             patch('builtins.open', mock_open(read_data=existing_content)) as mock_file, \
             patch('os.makedirs') as mock_makedirs, \
             patch('os.remove') as mock_remove, \
             patch('os.chmod') as mock_chmod:
            
            config = self.logrotate_module.LogrotateConfig(self.mock_module)
            result = config.apply()
            
            # Assertions
            self.assertTrue(result['changed'])
            mock_makedirs.assert_called()

    def test_generate_config_with_scripts(self):
        """Test generating configuration with pre/post scripts."""
        # Setup
        self._setup_module_params(
            prerotate="echo 'Pre-rotation'",
            postrotate=["systemctl reload test", "logger 'Rotation done'"],
            firstaction="echo 'First action'",
            lastaction="echo 'Last action'"
        )
        
        # Mock file operations
        with patch('os.path.exists', return_value=False) as mock_exists, \
             patch('os.makedirs') as mock_makedirs, \
             patch('builtins.open', mock_open()) as mock_file, \
             patch('os.chmod') as mock_chmod:
            
            config = self.logrotate_module.LogrotateConfig(self.mock_module)
            result = config.apply()
            
            # Assertions
            content = result['config_content']
            self.assertIn('prerotate', content)
            self.assertIn('postrotate', content)
            self.assertIn('firstaction', content)
            self.assertIn('lastaction', content)
            self.assertIn('systemctl reload test', content)
            self.assertIn("echo 'Pre-rotation'", content)

    def test_compression_methods(self):
        """Test different compression methods."""
        compression_methods = ['gzip', 'bzip2', 'xz', 'zstd', 'lzma', 'lz4']
        
        for method in compression_methods:
            with self.subTest(method=method):
                # Setup
                self._setup_module_params(compression_method=method)
                
                # Mock file operations
                with patch('os.path.exists', return_value=False) as mock_exists, \
                     patch('os.makedirs') as mock_makedirs, \
                     patch('builtins.open', mock_open()) as mock_file, \
                     patch('os.chmod') as mock_chmod:
                    
                    config = self.logrotate_module.LogrotateConfig(self.mock_module)
                    result = config.apply()
                    
                    # Assertions
                    content = result['config_content']
                    if method != 'gzip':
                        self.assertIn(f'compresscmd /usr/bin/{method}', content)
                        self.assertIn(f'uncompresscmd /usr/bin/{method}', content)

    def test_size_based_rotation(self):
        """Test size-based rotation configuration."""
        # Setup
        self._setup_module_params(
            size='100M',
            rotation_period='daily'  # Should be overridden by size
        )
        
        # Mock file operations
        with patch('os.path.exists', return_value=False) as mock_exists, \
             patch('os.makedirs') as mock_makedirs, \
             patch('builtins.open', mock_open()) as mock_file, \
             patch('os.chmod') as mock_chmod:
            
            config = self.logrotate_module.LogrotateConfig(self.mock_module)
            result = config.apply()
            
            # Assertions
            content = result['config_content']
            self.assertIn('size 100M', content)
            self.assertNotIn('daily', content)  # Should not include daily when size is specified

    def test_logrotate_not_installed(self):
        """Test error when logrotate is not installed."""
        # Setup
        self._setup_module_params()
        self.mock_module.get_bin_path.return_value = None
        
        # Should fail when calling main()
        with self.assertRaises(Exception) as context:
            self.logrotate_module.main()
        
        # Verify fail_json was called
        self.assertIn('fail_json called', str(context.exception))

    def test_parse_existing_config_paths(self):
        """Test parsing paths from existing configuration."""
        # Setup - no paths provided, but config exists
        self._setup_module_params(paths=None)
        
        existing_content = """/var/log/app1/*.log
/var/log/app2/error.log {
    daily
    rotate 7
    compress
}"""
        
        # Mock file exists
        with patch('os.path.exists', return_value=True) as mock_exists, \
             patch('builtins.open', mock_open(read_data=existing_content)) as mock_file, \
             patch('os.makedirs') as mock_makedirs, \
             patch('os.remove') as mock_remove, \
             patch('os.chmod') as mock_chmod:
            
            config = self.logrotate_module.LogrotateConfig(self.mock_module)
            
            # This should parse paths from existing content
            result = config.apply()
            
            # Assertions
            self.assertTrue(result['changed'])  # Always changes when we re-write
            content = result['config_content']
            self.assertIn('/var/log/app1/*.log', content)
            self.assertIn('/var/log/app2/error.log', content)


if __name__ == '__main__':
    unittest.main()