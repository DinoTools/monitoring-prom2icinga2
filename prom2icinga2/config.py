# SPDX-FileCopyrightText: PhiBo DinoTools (2025-)
# SPDX-License-Identifier: GPL-3.0-or-later

from dynaconf import Dynaconf
import yaml

g_check_configs = {}

settings = Dynaconf(
    settings_files=["config.toml"],
    secrets=[".secrets.toml"],
    merge_enabled=True,
)

def load_config(filename):
    global g_check_configs

    check_config = yaml.safe_load(open(filename))
    g_check_configs.update(check_config)
