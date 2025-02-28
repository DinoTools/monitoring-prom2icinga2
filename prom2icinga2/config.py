# SPDX-FileCopyrightText: PhiBo DinoTools (2025-)
# SPDX-License-Identifier: GPL-3.0-or-later

import os
from pathlib import Path
from typing import Optional

from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict
import yaml

try:
    import toml
    has_toml = True
except ImportError:
    has_toml = False


g_check_configs = {}

settings: Optional["Settings"] = None


class Icinga2Settings(BaseModel):
    url: str = "https://localhost:5665/"
    username: Optional[str] = None
    password: Optional[str] = None

    ssl_verify: bool = True


class PrometheusSettings(BaseModel):
    url: str


class Settings(BaseSettings):
    icinga2: Icinga2Settings
    prometheus: PrometheusSettings

    model_config = SettingsConfigDict(env_prefix="PROM2ICINGA2__", env_nested_delimiter="__")


def load_config():
    global g_check_configs
    global settings

    settings_filename = os.getenv("PROM2ICINGA2_CONFIG")
    settings_data = {}
    if isinstance(settings_filename, str):
        settings_file = Path(settings_filename)
        if not settings_file.exists():
            raise Exception(f"Config file {settings_file} not found")

        if settings_file.suffix == ".toml":
            if not has_toml:
                raise Exception(f"Try to load config from toml file {settings_file}. But toml support not installed")
            settings_data = toml.load(settings_file.open())
        elif settings_file.suffix in (".yaml", ".yml"):
            settings_data = yaml.safe_load(settings_file.open())
        else:
            raise Exception(f"Unknown config file type {settings_file}")
    settings = Settings(**settings_data)

    check_config_filename = os.getenv("PROM2ICINGA2_CHECK_CONFIG")
    if check_config_filename is None:
        raise Exception("PROM2ICINGA2_CHECK_CONFIG not set")
    check_config_file = Path(check_config_filename)
    if not check_config_file.exists():
        raise Exception(f"Config file {check_config_file} not found")

    check_config = yaml.safe_load(check_config_file.open())
    g_check_configs.update(check_config)
