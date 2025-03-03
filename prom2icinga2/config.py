# SPDX-FileCopyrightText: PhiBo DinoTools (2025-)
# SPDX-License-Identifier: GPL-3.0-or-later

import os
from pathlib import Path
from typing import Dict, Optional

from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict
import yaml

try:
    import toml
    has_toml = True
except ImportError:
    has_toml = False


g_check_configs: Dict[str, "CheckConfig"] = {}

settings: Optional["Settings"] = None


class CheckConfig(BaseModel):
    group_label_name: Optional[str] = None
    long_output: Optional[str] = None
    values: Dict[str, "CheckValueConfig"] = {}


class CheckValueConfig(BaseModel):
    query: str
    condition: Optional[str] = None
    warning: Optional[str] = None
    critical: Optional[str] = None


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

    check_file_config = yaml.safe_load(check_config_file.open())
    if not isinstance(check_file_config, dict):
        raise Exception(f"The base config in '{check_config_file}' must be of type dict")

    for check_name, check_config in check_file_config.items():
        g_check_configs[check_name] = CheckConfig.model_validate(check_config)
