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
        cls.test_dir = tempfile.mkdtemp()
        cls.mock_ansible_basic = Mock()
        cls.mock_ansible_basic.AnsibleModule = Mock()
        cls.mock_converters = Mock()
        cls.mock_converters.to_native = lambda x: str(x)
        cls.patcher_basic = patch.dict('sys.modules', {
            'ansible.module_utils.basic': cls.mock_ansible_basic,
            'ansible.module_utils.common.text.converters': cls.mock_converters
        })
        cls.patcher_basic.start()

    @classmethod
    def tearDownClass(cls):
        """Clean up after all tests."""
        cls.patcher_basic.stop()
        if os.path.exists(cls.test_dir):
            shutil.rmtree(cls.test_dir)

    def setUp(self):
        """Set up test fixtures."""
        self.mock_ansible_basic.AnsibleModule.reset_mock()
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
        self.config_dir = os.path.join(self.test_dir, "logrotate.d")
        os.makedirs(self.config_dir, exist_ok=True)
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


        for module_name in list(sys.modules.keys()):
            if 'logrotate' in module_name or 'ansible_collections.community.general.plugins.modules' in module_name:
                del sys.modules[module_name]
        try:
            from ansible_collections.community.general.plugins.modules import logrotate as logrotate_module
            self.logrotate_module = logrotate_module
        except ImportError:

            import logrotate as logrotate_module
            self.logrotate_module = logrotate_module

    def tearDown(self):
        """Clean up after test."""
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
        self._setup_module_params()
        with patch('os.path.exists', return_value=False) as mock_exists, \
             patch('os.makedirs') as mock_makedirs, \
             patch('builtins.open', mock_open()) as mock_file, \
             patch('os.chmod') as mock_chmod:
            config = self.logrotate_module.LogrotateConfig(self.mock_module)
            result = config.apply()
            self.assertTrue(result['changed'])
            self.assertIn('config_file', result)
            self.assertIn('config_content', result)
            self.assertEqual(result['enabled_state'], True)
            mock_file.assert_called_once()
            mock_chmod.assert_called_once()

    def test_update_existing_configuration(self):
        """Test updating an existing logrotate configuration."""
        self._setup_module_params(rotate_count=14)
        existing_content = """/var/log/test/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
}"""
        with patch('os.path.exists', return_value=True) as mock_exists, \
             patch('builtins.open', mock_open(read_data=existing_content)) as mock_file, \
             patch('os.remove') as mock_remove, \
             patch('os.chmod') as mock_chmod:
            config = self.logrotate_module.LogrotateConfig(self.mock_module)
            result = config.apply()
            self.assertTrue(result['changed'])
            self.assertIn('14', result['config_content'])
            self.assertTrue(mock_remove.called)
            mock_file.assert_called()
            mock_chmod.assert_called_once()

    def test_remove_configuration(self):
        """Test removing a logrotate configuration."""
        self._setup_module_params(state='absent')
        config_path = os.path.join(self.config_dir, 'test')
        disabled_path = config_path + '.disabled'
        def exists_side_effect(path):
            if path == config_path or path == disabled_path:
                return True
            return False
        with patch('os.path.exists', side_effect=exists_side_effect) as mock_exists, \
             patch('os.remove') as mock_remove:
            config = self.logrotate_module.LogrotateConfig(self.mock_module)
            result = config.apply()
            self.assertTrue(result['changed'])
            self.assertTrue(mock_remove.called)

    def test_disable_configuration(self):
        """Test disabling a logrotate configuration."""

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
        with patch('os.path.exists', side_effect=exists_side_effect) as mock_exists, \
             patch('builtins.open', mock_open(read_data=existing_content)) as mock_file, \
             patch('os.remove') as mock_remove, \
             patch('os.chmod') as mock_chmod, \
             patch('os.makedirs') as mock_makedirs:
            mock_file_write = mock_open()
            with patch('builtins.open', mock_file_write):
                config = self.logrotate_module.LogrotateConfig(self.mock_module)
                result = config.apply()
            self.assertTrue(result['changed'])
            self.assertEqual(result['enabled_state'], False)
            self.assertTrue(result['config_file'].endswith('.disabled'))

    def test_enable_configuration(self):
        """Test enabling a disabled logrotate configuration."""
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
        with patch('os.path.exists', side_effect=exists_side_effect) as mock_exists, \
             patch('builtins.open', mock_open(read_data=existing_content)) as mock_file, \
             patch('os.remove') as mock_remove, \
             patch('os.chmod') as mock_chmod, \
             patch('os.makedirs') as mock_makedirs:
            self.mock_module.atomic_move = Mock()
            config = self.logrotate_module.LogrotateConfig(self.mock_module)
            result = config.apply()
            self.assertTrue(result['changed'])
            self.assertEqual(result['enabled_state'], True)
            self.assertFalse(result['config_file'].endswith('.disabled'))

    def test_validation_missing_paths(self):
        """Test validation when paths are missing for new configuration."""
        self._setup_module_params(paths=None)
        with patch('os.path.exists', return_value=False):
            config = self.logrotate_module.LogrotateConfig(self.mock_module)
            with self.assertRaises(Exception) as context:
                config.apply()
            self.assertIn('fail_json called', str(context.exception))

    def test_validation_size_and_maxsize_exclusive(self):
        """Test validation when both size and maxsize are specified."""
        self._setup_module_params(size='100M', maxsize='200M')
        with patch('os.path.exists', return_value=False):
            config = self.logrotate_module.LogrotateConfig(self.mock_module)
            with self.assertRaises(Exception) as context:
                config.apply()
            self.assertIn('fail_json called', str(context.exception))

    def test_check_mode(self):
        """Test that no changes are made in check mode."""
        self._setup_module_params()
        self.mock_module.check_mode = True
        with patch('os.path.exists', return_value=False) as mock_exists, \
             patch('os.makedirs') as mock_makedirs, \
             patch('builtins.open', mock_open()) as mock_file:
            config = self.logrotate_module.LogrotateConfig(self.mock_module)
            result = config.apply()
            self.assertTrue(result['changed'])
            mock_file.assert_not_called()
            mock_makedirs.assert_called_once()

    def test_backup_configuration(self):
        """Test backing up configuration before changes."""
        self._setup_module_params(backup=True, rotate_count=14)
        existing_content = """/var/log/test/*.log {
    daily
    rotate 7
}"""

        with patch('os.path.exists', return_value=True) as mock_exists, \
             patch('builtins.open', mock_open(read_data=existing_content)) as mock_file, \
             patch('os.makedirs') as mock_makedirs, \
             patch('os.remove') as mock_remove, \
             patch('os.chmod') as mock_chmod:
            config = self.logrotate_module.LogrotateConfig(self.mock_module)
            result = config.apply()
            self.assertTrue(result['changed'])
            mock_makedirs.assert_called()

    def test_generate_config_with_scripts(self):
        """Test generating configuration with pre/post scripts."""
        self._setup_module_params(
            prerotate="echo 'Pre-rotation'",
            postrotate=["systemctl reload test", "logger 'Rotation done'"],
            firstaction="echo 'First action'",
            lastaction="echo 'Last action'"
        )
        with patch('os.path.exists', return_value=False) as mock_exists, \
             patch('os.makedirs') as mock_makedirs, \
             patch('builtins.open', mock_open()) as mock_file, \
             patch('os.chmod') as mock_chmod:
            config = self.logrotate_module.LogrotateConfig(self.mock_module)
            result = config.apply()
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
                self._setup_module_params(compression_method=method)
                with patch('os.path.exists', return_value=False) as mock_exists, \
                     patch('os.makedirs') as mock_makedirs, \
                     patch('builtins.open', mock_open()) as mock_file, \
                     patch('os.chmod') as mock_chmod:
                    config = self.logrotate_module.LogrotateConfig(self.mock_module)
                    result = config.apply()
                    content = result['config_content']
                    if method != 'gzip':
                        self.assertIn(f'compresscmd /usr/bin/{method}', content)
                        self.assertIn(f'uncompresscmd /usr/bin/{method}', content)

    def test_size_based_rotation(self):
        """Test size-based rotation configuration."""
        self._setup_module_params(
            size='100M',
            rotation_period='daily'
        )
        with patch('os.path.exists', return_value=False) as mock_exists, \
             patch('os.makedirs') as mock_makedirs, \
             patch('builtins.open', mock_open()) as mock_file, \
             patch('os.chmod') as mock_chmod:
            config = self.logrotate_module.LogrotateConfig(self.mock_module)
            result = config.apply()
            content = result['config_content']
            self.assertIn('size 100M', content)
            self.assertNotIn('daily', content)

    def test_logrotate_not_installed(self):
        """Test error when logrotate is not installed."""
        self._setup_module_params()
        self.mock_module.get_bin_path.return_value = None
        with self.assertRaises(Exception) as context:
            self.logrotate_module.main()
        self.assertIn('fail_json called', str(context.exception))

    def test_parse_existing_config_paths(self):
        """Test parsing paths from existing configuration."""
        self._setup_module_params(paths=None)
        existing_content = """/var/log/app1/*.log
{
    daily
    rotate 7
    compress
}"""

        with patch('os.path.exists', return_value=True) as mock_exists:
            mock_file_read = mock_open(read_data=existing_content)
            with patch('builtins.open', mock_file_read), \
                 patch('os.makedirs') as mock_makedirs, \
                 patch('os.remove') as mock_remove, \
                 patch('os.chmod') as mock_chmod:
                config = self.logrotate_module.LogrotateConfig(self.mock_module)
                result = config.apply()
                self.assertTrue(result['changed'])
                self.assertIn('/var/log/app1/*.log', result['config_content'])

    def test_compressoptions_parameter(self):
        """Test compressoptions parameter."""
        self._setup_module_params(compressoptions="-9")
        with patch('os.path.exists', return_value=False) as mock_exists, \
             patch('os.makedirs') as mock_makedirs, \
             patch('builtins.open', mock_open()) as mock_file, \
             patch('os.chmod') as mock_chmod:
            config = self.logrotate_module.LogrotateConfig(self.mock_module)
            result = config.apply()
            content = result['config_content']
            self.assertIn('compressoptions -9', content)
            self.assertTrue(result['changed'])

    def test_nodelaycompress_parameter(self):
        """Test nodelaycompress parameter."""
        self._setup_module_params(nodelaycompress=True)
        with patch('os.path.exists', return_value=False) as mock_exists, \
             patch('os.makedirs') as mock_makedirs, \
             patch('builtins.open', mock_open()) as mock_file, \
             patch('os.chmod') as mock_chmod:
            config = self.logrotate_module.LogrotateConfig(self.mock_module)
            result = config.apply()
            content = result['config_content']
            self.assertIn('nodelaycompress', content)
            self.assertTrue(result['changed'])

    def test_shred_and_shredcycles_parameters(self):
        """Test shred and shredcycles parameters."""
        self._setup_module_params(shred=True, shredcycles=3)
        with patch('os.path.exists', return_value=False) as mock_exists, \
             patch('os.makedirs') as mock_makedirs, \
             patch('builtins.open', mock_open()) as mock_file, \
             patch('os.chmod') as mock_chmod:
            config = self.logrotate_module.LogrotateConfig(self.mock_module)
            result = config.apply()
            content = result['config_content']
            self.assertIn('shred', content)
            self.assertIn('shredcycles 3', content)
            self.assertTrue(result['changed'])

    def test_copy_parameter(self):
        """Test copy parameter."""
        self._setup_module_params(copy=True, copytruncate=False)
        with patch('os.path.exists', return_value=False) as mock_exists, \
             patch('os.makedirs') as mock_makedirs, \
             patch('builtins.open', mock_open()) as mock_file, \
             patch('os.chmod') as mock_chmod:
            config = self.logrotate_module.LogrotateConfig(self.mock_module)
            result = config.apply()
            content = result['config_content']
            self.assertIn('copy', content)
            self.assertNotIn('copytruncate', content)
            self.assertTrue(result['changed'])

    def test_renamecopy_parameter(self):
        """Test renamecopy parameter."""
        self._setup_module_params(renamecopy=True)
        with patch('os.path.exists', return_value=False) as mock_exists, \
             patch('os.makedirs') as mock_makedirs, \
             patch('builtins.open', mock_open()) as mock_file, \
             patch('os.chmod') as mock_chmod:
            config = self.logrotate_module.LogrotateConfig(self.mock_module)
            result = config.apply()
            content = result['config_content']
            self.assertIn('renamecopy', content)
            self.assertTrue(result['changed'])

    def test_minsize_parameter(self):
        """Test minsize parameter."""
        self._setup_module_params(minsize="100k")
        with patch('os.path.exists', return_value=False) as mock_exists, \
             patch('os.makedirs') as mock_makedirs, \
             patch('builtins.open', mock_open()) as mock_file, \
             patch('os.chmod') as mock_chmod:
            config = self.logrotate_module.LogrotateConfig(self.mock_module)
            result = config.apply()
            content = result['config_content']
            self.assertIn('minsize 100k', content)
            self.assertTrue(result['changed'])

    def test_dateyesterday_parameter(self):
        """Test dateyesterday parameter."""
        self._setup_module_params(dateext=True, dateyesterday=True)
        with patch('os.path.exists', return_value=False) as mock_exists, \
             patch('os.makedirs') as mock_makedirs, \
             patch('builtins.open', mock_open()) as mock_file, \
             patch('os.chmod') as mock_chmod:
            config = self.logrotate_module.LogrotateConfig(self.mock_module)
            result = config.apply()
            content = result['config_content']
            self.assertIn('dateext', content)
            self.assertIn('dateyesterday', content)
            self.assertTrue(result['changed'])

    def test_createolddir_parameter(self):
        """Test createolddir parameter."""
        self._setup_module_params(olddir="/var/log/archives", createolddir=True)
        with patch('os.path.exists', return_value=False) as mock_exists, \
             patch('os.makedirs') as mock_makedirs, \
             patch('builtins.open', mock_open()) as mock_file, \
             patch('os.chmod') as mock_chmod:
            config = self.logrotate_module.LogrotateConfig(self.mock_module)
            result = config.apply()
            content = result['config_content']
            self.assertIn('olddir /var/log/archives', content)
            self.assertIn('createolddir', content)
            self.assertTrue(result['changed'])

    def test_start_parameter(self):
        """Test start parameter."""
        self._setup_module_params(start=1)
        with patch('os.path.exists', return_value=False) as mock_exists, \
             patch('os.makedirs') as mock_makedirs, \
             patch('builtins.open', mock_open()) as mock_file, \
             patch('os.chmod') as mock_chmod:
            config = self.logrotate_module.LogrotateConfig(self.mock_module)
            result = config.apply()
            content = result['config_content']
            self.assertIn('start 1', content)
            self.assertTrue(result['changed'])

    def test_syslog_parameter(self):
        """Test syslog parameter."""
        self._setup_module_params(syslog=True)
        with patch('os.path.exists', return_value=False) as mock_exists, \
             patch('os.makedirs') as mock_makedirs, \
             patch('builtins.open', mock_open()) as mock_file, \
             patch('os.chmod') as mock_chmod:
            config = self.logrotate_module.LogrotateConfig(self.mock_module)
            result = config.apply()
            content = result['config_content']
            self.assertIn('syslog', content)
            self.assertTrue(result['changed'])

    def test_validation_copy_and_copytruncate_exclusive(self):
        """Test validation when both copy and copytruncate are specified."""
        self._setup_module_params(copy=True, copytruncate=True)
        with patch('os.path.exists', return_value=False):
            config = self.logrotate_module.LogrotateConfig(self.mock_module)
            with self.assertRaises(Exception) as context:
                config.apply()
            self.assertIn('fail_json called', str(context.exception))

    def test_validation_copy_and_renamecopy_exclusive(self):
        """Test validation when both copy and renamecopy are specified."""
        self._setup_module_params(copy=True, renamecopy=True)
        with patch('os.path.exists', return_value=False):
            config = self.logrotate_module.LogrotateConfig(self.mock_module)
            with self.assertRaises(Exception) as context:
                config.apply()
            self.assertIn('fail_json called', str(context.exception))

    def test_validation_shredcycles_positive(self):
        """Test validation when shredcycles is not positive."""
        self._setup_module_params(shredcycles=0)
        with patch('os.path.exists', return_value=False):
            config = self.logrotate_module.LogrotateConfig(self.mock_module)
            with self.assertRaises(Exception) as context:
                config.apply()
            self.assertIn('fail_json called', str(context.exception))

    def test_validation_start_non_negative(self):
        """Test validation when start is negative."""
        self._setup_module_params(start=-1)
        with patch('os.path.exists', return_value=False):
            config = self.logrotate_module.LogrotateConfig(self.mock_module)
            with self.assertRaises(Exception) as context:
                config.apply()
            self.assertIn('fail_json called', str(context.exception))

    def test_all_new_parameters_together(self):
        """Test all new parameters together in one configuration."""

        self._setup_module_params(
            compressoptions="-9",
            nodelaycompress=True,
            shred=True,
            shredcycles=3,
            copy=True,
            minsize="100k",
            dateext=True,
            dateyesterday=True,
            olddir="/var/log/archives",
            createolddir=True,
            start=1,
            syslog=True,
            renamecopy=False,
            copytruncate=False,
            delaycompress=False,
        )


        with patch('os.path.exists', return_value=False) as mock_exists, \
             patch('os.makedirs') as mock_makedirs, \
             patch('builtins.open', mock_open()) as mock_file, \
             patch('os.chmod') as mock_chmod:

            config = self.logrotate_module.LogrotateConfig(self.mock_module)
            result = config.apply()
            content = result['config_content']
            self.assertTrue(result['changed'])

            self.assertIn('compressoptions -9', content)
            self.assertIn('nodelaycompress', content)
            self.assertIn('shred', content)
            self.assertIn('shredcycles 3', content)
            self.assertIn('copy', content)
            self.assertIn('minsize 100k', content)
            self.assertIn('dateext', content)
            self.assertIn('dateyesterday', content)
            self.assertIn('olddir /var/log/archives', content)
            self.assertIn('createolddir', content)
            self.assertIn('start 1', content)
            self.assertIn('syslog', content)


            lines = [line.strip() for line in content.split('\n')]
            self.assertNotIn('copytruncate', lines)
            self.assertNotIn('renamecopy', lines)
            self.assertNotIn('delaycompress', lines)

    def test_parameter_interactions(self):
        """Test interactions between related parameters."""

        self._setup_module_params(delaycompress=True, nodelaycompress=True)

        with patch('os.path.exists', return_value=False):
            with patch('builtins.open', mock_open()):
                config = self.logrotate_module.LogrotateConfig(self.mock_module)

                with self.assertRaises(Exception) as context:
                    config.apply()

                self.assertIn('fail_json called', str(context.exception))

        self._setup_module_params(olddir="/var/log/archives", noolddir=True)

        with patch('os.path.exists', return_value=False):
            config = self.logrotate_module.LogrotateConfig(self.mock_module)

            with self.assertRaises(Exception) as context:
                config.apply()

            self.assertIn('fail_json called', str(context.exception))

    def test_size_format_validation(self):
        """Test validation of size format parameters."""

        valid_sizes = ["100k", "100M", "1G", "10", "500K", "2M", "3G"]

        for size in valid_sizes:
            with self.subTest(valid_size=size):
                self._setup_module_params(size=size)

                with patch('os.path.exists', return_value=False) as mock_exists, \
                     patch('os.makedirs') as mock_makedirs, \
                     patch('builtins.open', mock_open()) as mock_file, \
                     patch('os.chmod') as mock_chmod, \
                     patch('os.remove') as mock_remove:

                    config = self.logrotate_module.LogrotateConfig(self.mock_module)

                    try:
                        result = config.apply()
                        self.assertIn(f'size {size}', result['config_content'])
                    except Exception as e:
                        self.fail(f"Valid size format {size} should not fail: {e}")

        invalid_sizes = ["100kb", "M100", "1.5G", "abc", "100 MB"]

        for size in invalid_sizes:
            with self.subTest(invalid_size=size):
                self._setup_module_params(size=size)

                with patch('os.path.exists', return_value=False):
                    config = self.logrotate_module.LogrotateConfig(self.mock_module)

                    with self.assertRaises(Exception) as context:
                        config.apply()

                    self.assertIn('fail_json called', str(context.exception))


if __name__ == '__main__':
    unittest.main()
