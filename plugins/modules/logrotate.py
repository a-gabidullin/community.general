#!/usr/bin/python
# Copyright (c) 2026 Aleksandr Gabidullin <qualittv@gmail.com>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

DOCUMENTATION = r"""
module: logrotate
version_added: 12.3.0
short_description: Manage logrotate configurations
description:
  - Manage logrotate configuration files and settings.
  - Create, update, or remove logrotate configurations for applications and services.
author: "Aleksandr Gabidullin (@a-gabidullin)"
requirements:
  - logrotate >= 3.8.0
attributes:
  check_mode:
    support: full
  diff_mode:
    support: full
  platform:
    platforms: posix
    description: This module requires logrotate to be installed.
    support: full
options:
  name:
    description:
      - Name of the logrotate configuration.
      - This creates a file in O(config_dir) with this name.
    type: str
    required: true
    aliases: [config_name]
  state:
    description:
      - Whether the configuration should be present or absent.
    type: str
    choices: [present, absent]
    default: present
  config_dir:
    description:
      - Directory where logrotate configurations are stored.
      - Default is V(/etc/logrotate.d) for system-wide configurations.
      - Use V(~/.logrotate.d) for user-specific configurations.
    type: path
    default: /etc/logrotate.d
  paths:
    description:
      - List of log file paths or patterns to rotate.
      - Can include wildcards (e.g., V(/var/log/app/*.log)).
      - Required when creating a new configuration (O(state=present) and config file does not exist).
      - Optional when modifying existing configuration (e.g., to enable/disable).
    type: list
    elements: str
  rotation_period:
    description:
      - How often to rotate the logs.
    type: str
    choices: [daily, weekly, monthly, yearly]
    default: daily
  rotate_count:
    description:
      - Number of rotated log files to keep.
      - Set to V(0) to disable rotation (keep only current log).
      - Set to V(-1) to keep all rotated logs (not recommended).
    type: int
    default: 7
  compress:
    description:
      - Compress rotated log files.
    type: bool
    default: true
  compressoptions:
    description:
      - Options to pass to compression program.
      - For gzip, use V(-9) for best compression, V(-1) for fastest.
      - For xz, use V(-9) for best compression.
    type: str
  compression_method:
    description:
      - Compression method to use.
      - Requires logrotate 3.18.0 or later for V(xz) and V(zstd).
    type: str
    choices: [gzip, bzip2, xz, zstd, lzma, lz4]
    default: gzip
  delaycompress:
    description:
      - Postpone compression of the previous log file to the next rotation cycle.
      - Useful for applications that keep writing to the old log file for some time.
    type: bool
    default: false
  nodelaycompress:
    description:
      - Opposite of O(delaycompress). Ensure compression happens immediately.
      - Note that in logrotate, V(nodelaycompress) is the default behavior.
    type: bool
    default: false
  shred:
    description:
      - Use shred to securely delete rotated log files.
      - Uses V(shred -u) to overwrite files before deleting.
    type: bool
    default: false
  shredcycles:
    description:
      - Number of times to overwrite files when using O(shred=true).
    type: int
    default: 1
  missingok:
    description:
      - Do not issue an error if the log file is missing.
    type: bool
    default: true
  ifempty:
    description:
      - Rotate the log file even if it is empty.
      - Opposite of V(notifempty).
    type: bool
    default: false
  notifempty:
    description:
      - Do not rotate the log file if it is empty.
      - Opposite of V(ifempty).
    type: bool
    default: true
  create:
    description:
      - Create new log file with specified permissions after rotation.
      - Format is V(mode owner group) (e.g., V(0640 root adm)).
      - Set to V(null) or omit to use V(nocreate).
    type: str
  copytruncate:
    description:
      - Copy the log file and then truncate it in place.
      - Useful for applications that cannot be told to close their logfile.
    type: bool
    default: false
  copy:
    description:
      - Copy the log file but do not truncate the original.
      - Takes precedence over O(renamecopy) and O(copytruncate).
    type: bool
    default: false
  renamecopy:
    description:
      - Rename and copy the log file, leaving the original in place.
    type: bool
    default: false
  size:
    description:
      - Rotate log file when it grows bigger than specified size.
      - Format is V(number)[k|M|G] (e.g., V(100M), V(1G)).
      - Overrides O(rotation_period) when set.
    type: str
  minsize:
    description:
      - Rotate log file only if it has grown bigger than specified size.
      - Format is V(number)[k|M|G] (e.g., V(100M), V(1G)).
      - Used with time-based rotation to avoid rotating too small files.
    type: str
  maxsize:
    description:
      - Rotate log file when it grows bigger than specified size, but at most once per O(rotation_period).
      - Format is V(number)[k|M|G] (e.g., V(100M), V(1G)).
    type: str
  maxage:
    description:
      - Remove rotated logs older than specified number of days.
    type: int
  dateext:
    description:
      - Use date as extension for rotated files (YYYYMMDD instead of sequential numbers).
    type: bool
    default: false
  dateyesterday:
    description:
      - Use yesterday's date for O(dateext) instead of today's date.
      - Useful for rotating logs that span midnight.
    type: bool
    default: false
  dateformat:
    description:
      - Format for date extension.
      - Use with O(dateext=true).
      - Format specifiers are V(%Y) year, V(%m) month, V(%d) day, V(%s) seconds since epoch.
    type: str
    default: -%Y%m%d
  sharedscripts:
    description:
      - Run O(prerotate) and O(postrotate) scripts only once for all matching log files.
    type: bool
    default: false
  prerotate:
    description:
      - Commands to execute before rotating the log file.
      - Can be a single string or list of commands.
    type: raw
  postrotate:
    description:
      - Commands to execute after rotating the log file.
      - Can be a single string or list of commands.
    type: raw
  firstaction:
    description:
      - Commands to execute once before all log files that match the wildcard pattern are rotated.
    type: raw
  lastaction:
    description:
      - Commands to execute once after all log files that match the wildcard pattern are rotated.
    type: raw
  preremove:
    description:
      - Commands to execute before removing rotated log files.
    type: raw
  su:
    description:
      - Set user and group for rotated files.
      - Format is V(user group) (e.g., V(www-data adm)).
      - Set to V(null) or omit to not set user/group.
    type: str
  olddir:
    description:
      - Move rotated logs into specified directory.
    type: path
  createolddir:
    description:
      - Create O(olddir) directory if it does not exist.
    type: bool
    default: false
  noolddir:
    description:
      - Keep rotated logs in the same directory as the original log.
    type: bool
    default: false
  extension:
    description:
      - Extension to use for rotated log files (including dot).
      - Useful when O(compress=false).
    type: str
  mail:
    description:
      - Mail logs to specified address when removed.
      - Set to V(null) or omit to not mail logs.
    type: str
  mailfirst:
    description:
      - Mail just-created log file, not the about-to-expire one.
    type: bool
    default: false
  maillast:
    description:
      - Mail about-to-expire log file (default).
    type: bool
    default: true
  include:
    description:
      - Include additional configuration files from specified directory.
    type: path
  tabooext:
    description:
      - List of extensions that logrotate should not touch.
      - Default is V(.rpmorig .rpmsave .v .swp .rpmnew .cfsaved .rhn-cfg-tmp-*).
      - Set to V(null) or empty list to clear defaults.
    type: list
    elements: str
  enabled:
    description:
      - Whether the configuration should be enabled.
      - When V(false), adds V(.disabled) extension to the config file.
    type: bool
    default: true
  backup:
    description:
      - Make a backup of the logrotate config file before changing it.
    type: bool
    default: false
  backup_dir:
    description:
      - Directory to store backup files.
      - Default is same as O(config_dir) with V(.backup) suffix.
    type: path
  start:
    description:
      - Base number for rotated files.
      - For example, V(1) gives files .1, .2, and so on instead of .0, .1.
    type: int
    default: 0
  syslog:
    description:
      - Send logrotate messages to syslog.
    type: bool
    default: false
extends_documentation_fragment:
  - community.general.attributes
"""

EXAMPLES = r"""
- name: Configure log rotation for Nginx
  community.general.logrotate:
    name: nginx
    paths:
      - /var/log/nginx/*.log
    rotation_period: daily
    rotate_count: 14
    compress: true
    compressoptions: "-9"
    delaycompress: true
    missingok: true
    notifempty: true
    create: "0640 www-data adm"
    sharedscripts: true
    postrotate:
      - "[ -f /var/run/nginx.pid ] && kill -USR1 $(cat /var/run/nginx.pid)"
      - "echo 'Nginx logs rotated'"

- name: Configure size-based rotation for application logs
  community.general.logrotate:
    name: myapp
    paths:
      - /var/log/myapp/app.log
      - /var/log/myapp/debug.log
    size: 100M
    rotate_count: 10
    compress: true
    compressoptions: "-1"
    dateext: true
    dateyesterday: true
    dateformat: -%Y%m%d.%s
    missingok: true
    copytruncate: true

- name: Configure log rotation with secure deletion
  community.general.logrotate:
    name: secure-app
    paths:
      - /var/log/secure-app/*.log
    rotation_period: weekly
    rotate_count: 4
    shred: true
    shredcycles: 3
    compress: true
    compressoptions: "-9"

- name: Configure log rotation with custom start number
  community.general.logrotate:
    name: custom-start
    paths:
      - /var/log/custom/*.log
    rotation_period: monthly
    rotate_count: 6
    start: 1
    compress: true

- name: Configure log rotation with old directory
  community.general.logrotate:
    name: with-olddir
    paths:
      - /opt/app/logs/*.log
    rotation_period: weekly
    rotate_count: 4
    olddir: /var/log/archives
    createolddir: true
    compress: true
    compression_method: zstd

- name: Disable logrotate configuration
  community.general.logrotate:
    name: old-service
    enabled: false

- name: Remove logrotate configuration
  community.general.logrotate:
    name: deprecated-app
    state: absent

- name: Complex configuration with multiple scripts
  community.general.logrotate:
    name: complex-app
    paths:
      - /var/log/complex/*.log
    rotation_period: monthly
    rotate_count: 6
    compress: true
    delaycompress: false
    prerotate: |
      echo "Starting rotation for complex app"
      systemctl stop complex-app
    postrotate: |
      systemctl start complex-app
      echo "Rotation completed"
      logger -t logrotate "Complex app logs rotated"
    firstaction: "echo 'First action: Starting batch rotation'"
    lastaction: "echo 'Last action: Batch rotation complete'"

- name: User-specific logrotate configuration
  community.general.logrotate:
    name: myuser-apps
    config_dir: ~/.logrotate.d
    paths:
      - ~/app/*.log
      - ~/.cache/*/*.log
    rotation_period: daily
    rotate_count: 30
    compress: true
    su: "{{ ansible_user_id }} users"

- name: Configuration with copy instead of move
  community.general.logrotate:
    name: copy-config
    paths:
      - /var/log/copy-app/*.log
    rotation_period: daily
    rotate_count: 7
    copy: true

- name: Configuration with syslog notifications
  community.general.logrotate:
    name: syslog-config
    paths:
      - /var/log/syslog-app/*.log
    rotation_period: daily
    rotate_count: 14
    syslog: true
    compress: true

- name: Configuration without compression
  community.general.logrotate:
    name: nocompress-config
    paths:
      - /var/log/nocompress/*.log
    rotation_period: daily
    rotate_count: 7
    compress: false

- name: Configuration with custom taboo extensions
  community.general.logrotate:
    name: taboo-config
    paths:
      - /var/log/taboo/*.log
    rotation_period: daily
    rotate_count: 7
    tabooext: [".backup", ".tmp", ".temp"]
"""

RETURN = r"""
config_file:
  description: Path to the created/updated logrotate configuration file.
  type: str
  returned: when O(state=present)
  sample: /etc/logrotate.d/nginx
config_content:
  description: The generated logrotate configuration content.
  type: str
  returned: when O(state=present)
  sample: |
    /var/log/nginx/*.log {
        daily
        rotate 14
        compress
        compressoptions -9
        delaycompress
        missingok
        notifempty
        create 0640 www-data adm
        sharedscripts
        postrotate
            [ -f /var/run/nginx.pid ] && kill -USR1 $(cat /var/run/nginx.pid)
            echo 'Nginx logs rotated'
        endscript
    }
backup_file:
  description: Path to the backup file if backup was created.
  type: str
  returned: when backup was created
  sample: /etc/logrotate.d/nginx.backup.20231201
enabled_state:
  description: Current enabled state of the configuration.
  type: bool
  returned: always
  sample: true
"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.common.text.converters import to_native

import os
import re
from datetime import datetime
from typing import Dict, Any, List, Optional


class LogrotateConfig:
    """Logrotate configuration manager."""

    def __init__(self, module: AnsibleModule) -> None:
        self.module = module
        self.params = module.params
        self.result: Dict[str, Any] = {
            "changed": False,
            "config_file": "",
            "config_content": "",
            "enabled_state": True,
        }

        self.config_dir = self._expand_path(self.params["config_dir"])
        self.config_name = self.params["name"]
        self.disabled_suffix = ".disabled"

        self.config_file = self._get_config_path(self.params["enabled"])

        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir, mode=0o755, exist_ok=True)

    def _expand_path(self, path: str) -> str:
        """Expand user and variables in path."""
        return os.path.expanduser(os.path.expandvars(path))

    def _get_config_path(self, enabled: bool) -> str:
        """Get config file path based on enabled state."""
        base_path = os.path.join(self.config_dir, self.config_name)
        if not enabled:
            return base_path + self.disabled_suffix
        return base_path

    def _validate_parameters(self) -> None:
        """Validate module parameters."""
        if self.params["state"] == "present":
            existing_content = self._read_existing_config(any_state=True)

            if not existing_content and not self.params.get("paths"):
                self.module.fail_json(
                    msg="'paths' parameter is required when creating a new configuration"
                )

            if self.params.get("size") and self.params.get("maxsize"):
                self.module.fail_json(
                    msg="'size' and 'maxsize' parameters are mutually exclusive"
                )

            if self.params.get("copy") and self.params.get("copytruncate"):
                self.module.fail_json(
                    msg="'copy' and 'copytruncate' are mutually exclusive"
                )

            if self.params.get("copy") and self.params.get("renamecopy"):
                self.module.fail_json(
                    msg="'copy' and 'renamecopy' are mutually exclusive"
                )

            if self.params.get("ifempty") and self.params.get("notifempty"):
                self.module.fail_json(
                    msg="'ifempty' and 'notifempty' are mutually exclusive"
                )

            if self.params.get("delaycompress") and self.params.get("nodelaycompress"):
                self.module.fail_json(
                    msg="'delaycompress' and 'nodelaycompress' are mutually exclusive"
                )

            if self.params.get("olddir") and self.params.get("noolddir"):
                self.module.fail_json(
                    msg="'olddir' and 'noolddir' are mutually exclusive"
                )

            comp_method = self.params.get("compression_method", "gzip")
            if comp_method not in ["gzip", "bzip2", "xz", "zstd", "lzma", "lz4"]:
                self.module.fail_json(
                    msg=f"Invalid compression method: {comp_method}"
                )

            if self.params.get("su"):
                su_parts = self.params["su"].split()
                if len(su_parts) != 2:
                    self.module.fail_json(
                        msg="'su' parameter must be in format 'user group'"
                    )

            if self.params.get("shredcycles", 1) < 1:
                self.module.fail_json(
                    msg="'shredcycles' must be a positive integer"
                )

            if self.params.get("start", 0) < 0:
                self.module.fail_json(
                    msg="'start' must be a non-negative integer"
                )

            for size_param in ["size", "minsize", "maxsize"]:
                if self.params.get(size_param):
                    if not re.match(r'^\d+[kMG]?$', self.params[size_param], re.I):
                        self.module.fail_json(
                            msg=f"'{size_param}' must be in format 'number[k|M|G]' (e.g., '100M', '1G')"
                        )

    def _read_existing_config(self, any_state: bool = False) -> Optional[str]:
        """Read existing configuration file.

        Args:
            any_state: If True, check both enabled and disabled versions.
                      If False, only check based on current enabled param.
        """
        if any_state:
            for suffix in ["", self.disabled_suffix]:
                config_path = os.path.join(self.config_dir, self.config_name + suffix)
                if os.path.exists(config_path):
                    self.result["enabled_state"] = (suffix == "")
                    try:
                        with open(config_path, "r") as f:
                            return f.read()
                    except Exception as e:
                        self.module.fail_json(
                            msg=f"Failed to read config file {config_path}: {to_native(e)}"
                        )
        else:
            config_path = self._get_config_path(self.params["enabled"])
            if os.path.exists(config_path):
                try:
                    with open(config_path, "r") as f:
                        return f.read()
                except Exception as e:
                    self.module.fail_json(
                        msg=f"Failed to read config file {config_path}: {to_native(e)}"
                    )

        return None

    def _generate_config_content(self) -> str:
        """Generate logrotate configuration content."""
        if not self.params.get("paths"):
            existing_content = self._read_existing_config(any_state=True)
            if existing_content:
                lines = existing_content.strip().split('\n')
                paths = []
                for line in lines:
                    line = line.strip()
                    if line and not line.startswith('#') and not line.startswith('{') and not line.startswith('}') and '/' in line:
                        if not any(keyword in line for keyword in [' ', '\t', 'daily', 'weekly', 'monthly', 'yearly', 'rotate', 'compress']):
                            paths.append(line)

                if paths:
                    self.params['paths'] = paths
                else:
                    self.params['paths'] = []
            else:
                self.module.fail_json(msg="Cannot generate configuration: no paths specified and no existing configuration found")

        lines = []

        paths = self.params["paths"]
        if isinstance(paths, str):
            paths = [paths]

        for path in paths:
            lines.append(self._expand_path(path))
        lines.append("{")
        lines.append("")

        if not self.params.get("size") and not self.params.get("maxsize"):
            lines.append(f"    {self.params['rotation_period']}")

        if self.params.get("size"):
            lines.append(f"    size {self.params['size']}")
        elif self.params.get("maxsize"):
            lines.append(f"    maxsize {self.params['maxsize']}")

        if self.params.get("minsize"):
            lines.append(f"    minsize {self.params['minsize']}")

        lines.append(f"    rotate {self.params['rotate_count']}")

        if self.params.get("start", 0) != 0:
            lines.append(f"    start {self.params['start']}")

        if self.params["compress"]:
            comp_method = self.params.get("compression_method", "gzip")
            if comp_method != "gzip":
                lines.append(f"    compresscmd /usr/bin/{comp_method}")
                if comp_method == "zstd":
                    lines.append(f"    uncompresscmd /usr/bin/{comp_method} -d")
                elif comp_method == "lz4":
                    lines.append(f"    uncompresscmd /usr/bin/{comp_method} -d")
                else:
                    lines.append(f"    uncompresscmd /usr/bin/{comp_method}un{comp_method}")
                lines.append(f"    compressext .{comp_method}")
            lines.append("    compress")

            if self.params.get("compressoptions"):
                lines.append(f"    compressoptions {self.params['compressoptions']}")
        else:
            lines.append("    nocompress")

        if self.params["delaycompress"]:
            lines.append("    delaycompress")
        elif self.params.get("nodelaycompress"):
            lines.append("    nodelaycompress")

        if self.params.get("shred"):
            lines.append("    shred")
            if self.params.get("shredcycles", 1) > 1:
                lines.append(f"    shredcycles {self.params['shredcycles']}")

        if not self.params["missingok"]:
            lines.append("    nomissingok")
        else:
            lines.append("    missingok")

        if self.params.get("ifempty"):
            lines.append("    ifempty")
        elif self.params.get("notifempty"):
            lines.append("    notifempty")

        if self.params.get("create"):
            lines.append(f"    create {self.params['create']}")

        if self.params.get("copy"):
            lines.append("    copy")
        elif self.params.get("renamecopy"):
            lines.append("    renamecopy")
        elif self.params.get("copytruncate"):
            lines.append("    copytruncate")

        if self.params.get("maxage"):
            lines.append(f"    maxage {self.params['maxage']}")

        if self.params["dateext"]:
            lines.append("    dateext")
            if self.params.get("dateyesterday"):
                lines.append("    dateyesterday")
            if self.params.get("dateformat"):
                lines.append(f"    dateformat {self.params['dateformat']}")

        if self.params.get("sharedscripts"):
            lines.append("    sharedscripts")

        if self.params.get("su"):
            lines.append(f"    su {self.params['su']}")

        if self.params.get("noolddir"):
            lines.append("    noolddir")
        elif self.params.get("olddir"):
            lines.append(f"    olddir {self._expand_path(self.params['olddir'])}")
            if self.params.get("createolddir"):
                lines.append("    createolddir")

        if self.params.get("extension"):
            lines.append(f"    extension {self.params['extension']}")

        if self.params.get("mail"):
            lines.append(f"    mail {self.params['mail']}")
            if self.params.get("mailfirst"):
                lines.append("    mailfirst")
            elif self.params.get("maillast"):
                lines.append("    maillast")

        if self.params.get("include"):
            lines.append(f"    include {self._expand_path(self.params['include'])}")

        if self.params.get("tabooext"):
            tabooext = self.params["tabooext"]
            if isinstance(tabooext, list):
                tabooext = " ".join(tabooext)
            if tabooext.strip():
                lines.append(f"    tabooext {tabooext}")

        if self.params.get("syslog"):
            lines.append("    syslog")

        scripts = {
            "prerotate": self.params.get("prerotate"),
            "postrotate": self.params.get("postrotate"),
            "firstaction": self.params.get("firstaction"),
            "lastaction": self.params.get("lastaction"),
            "preremove": self.params.get("preremove"),
        }

        for script_name, script_content in scripts.items():
            if script_content:
                lines.append(f"    {script_name}")
                if isinstance(script_content, list):
                    for line in script_content:
                        lines.append(f"        {line}")
                else:
                    for line in script_content.strip().split("\n"):
                        lines.append(f"        {line}")
                lines.append("    endscript")
                lines.append("")

        lines.append("}")

        return "\n".join(lines)

    def _backup_config(self, config_path: str) -> Optional[str]:
        """Create backup of existing configuration."""
        if not os.path.exists(config_path):
            return None

        if self.params.get("backup"):
            backup_dir = self.params.get("backup_dir") or os.path.join(self.config_dir, ".backup")
            os.makedirs(backup_dir, exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = os.path.join(
                backup_dir, f"{self.config_name}.backup.{timestamp}"
            )

            self.module.atomic_move(
                config_path,
                backup_file,
                unsafe_writes=False
            )
            self.result["backup_file"] = backup_file
            return backup_file

        return None

    def apply(self) -> Dict[str, Any]:
        """Apply logrotate configuration."""
        self._validate_parameters()
        state = self.params["state"]

        if state == "absent":
            for suffix in ["", self.disabled_suffix]:
                config_path = os.path.join(self.config_dir, self.config_name + suffix)
                if os.path.exists(config_path):
                    if not self.module.check_mode:
                        self._backup_config(config_path)
                        os.remove(config_path)
                    self.result["changed"] = True
                    self.result["config_file"] = config_path
                    break
            return self.result

        existing_content = self._read_existing_config(any_state=True)
        current_enabled = self.result.get("enabled_state", True)

        only_changing_enabled = (
            existing_content is not None and
            not self.params.get("paths") and
            self.params["enabled"] != current_enabled
        )

        if only_changing_enabled:
            old_path = self._get_config_path(not self.params["enabled"])
            new_path = self._get_config_path(self.params["enabled"])

            if os.path.exists(old_path) and not os.path.exists(new_path):
                self.result["changed"] = True
                if not self.module.check_mode:
                    self._backup_config(old_path)
                    self.module.atomic_move(old_path, new_path, unsafe_writes=False)

                self.result["config_file"] = new_path
                self.result["enabled_state"] = self.params["enabled"]

                try:
                    with open(new_path, "r") as f:
                        self.result["config_content"] = f.read()
                except:
                    self.result["config_content"] = existing_content

                return self.result

        new_content = self._generate_config_content()
        self.result["config_content"] = new_content
        self.result["config_file"] = self._get_config_path(self.params["enabled"])

        needs_update = False

        if existing_content is None:
            needs_update = True
        elif existing_content != new_content:
            needs_update = True
        elif self.params["enabled"] != current_enabled:
            needs_update = True

        if needs_update:
            self.result["changed"] = True

            if not self.module.check_mode:
                for suffix in ["", self.disabled_suffix]:
                    old_path = os.path.join(self.config_dir, self.config_name + suffix)
                    if os.path.exists(old_path):
                        self._backup_config(old_path)
                        os.remove(old_path)

                try:
                    with open(self.result["config_file"], "w") as f:
                        f.write(new_content)
                    os.chmod(self.result["config_file"], 0o644)
                except Exception as e:
                    self.module.fail_json(
                        msg=f"Failed to write config file {self.result['config_file']}: {to_native(e)}"
                    )

                if self.module.get_bin_path("logrotate"):
                    test_cmd = ["logrotate", "-d", self.result["config_file"]]
                    rc, stdout, stderr = self.module.run_command(test_cmd)
                    if rc != 0:
                        self.module.warn(
                            f"logrotate configuration test failed: {stderr}"
                        )

        self.result["enabled_state"] = self.params["enabled"]
        return self.result


def main() -> None:
    """Main function."""
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(type="str", required=True, aliases=["config_name"]),
            state=dict(type="str", default="present", choices=["present", "absent"]),
            config_dir=dict(type="path", default="/etc/logrotate.d"),
            paths=dict(type="list", elements="str"),
            rotation_period=dict(
                type="str",
                default="daily",
                choices=["daily", "weekly", "monthly", "yearly"],
            ),
            rotate_count=dict(type="int", default=7),
            compress=dict(type="bool", default=True),
            compressoptions=dict(type="str"),
            compression_method=dict(
                type="str",
                default="gzip",
                choices=["gzip", "bzip2", "xz", "zstd", "lzma", "lz4"],
            ),
            delaycompress=dict(type="bool", default=False),
            nodelaycompress=dict(type="bool", default=False),
            shred=dict(type="bool", default=False),
            shredcycles=dict(type="int", default=1),
            missingok=dict(type="bool", default=True),
            ifempty=dict(type="bool", default=False),
            notifempty=dict(type="bool", default=True),
            create=dict(type="str"),
            copytruncate=dict(type="bool", default=False),
            copy=dict(type="bool", default=False),
            renamecopy=dict(type="bool", default=False),
            size=dict(type="str"),
            minsize=dict(type="str"),
            maxsize=dict(type="str"),
            maxage=dict(type="int"),
            dateext=dict(type="bool", default=False),
            dateyesterday=dict(type="bool", default=False),
            dateformat=dict(type="str", default="-%Y%m%d"),
            sharedscripts=dict(type="bool", default=False),
            prerotate=dict(type="raw"),
            postrotate=dict(type="raw"),
            firstaction=dict(type="raw"),
            lastaction=dict(type="raw"),
            preremove=dict(type="raw"),
            su=dict(type="str"),
            olddir=dict(type="path"),
            createolddir=dict(type="bool", default=False),
            noolddir=dict(type="bool", default=False),
            extension=dict(type="str"),
            mail=dict(type="str"),
            mailfirst=dict(type="bool", default=False),
            maillast=dict(type="bool", default=True),
            include=dict(type="path"),
            tabooext=dict(type="list", elements="str"),
            enabled=dict(type="bool", default=True),
            backup=dict(type="bool", default=False),
            backup_dir=dict(type="path"),
            start=dict(type="int", default=0),
            syslog=dict(type="bool", default=False),
        ),
        supports_check_mode=True,
    )

    if not module.get_bin_path("logrotate"):
        module.fail_json(msg="logrotate is not installed or not in PATH")
    logrotate_config = LogrotateConfig(module)
    result = logrotate_config.apply()
    module.exit_json(**result)


if __name__ == "__main__":
    main()
