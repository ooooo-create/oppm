import configparser
import os
from pathlib import Path
from typing import NamedTuple

from .exceptions import ConfigError

_default_config_path = Path.home() / ".oppmconfig"

_config_file_str = os.environ.get("OPPM_CONFIG_FILE", _default_config_path)

CONFIG_FILE = Path(_config_file_str)


class OPPMConfig(NamedTuple):
    root_dir: Path
    apps_dir: Path
    meta_file: Path
    shims_dir: Path


def save_config(config: OPPMConfig):
    try:
        _config = configparser.ConfigParser()
        _config["config"] = {
            "root_dir": str(config.root_dir.as_posix()),
            "apps_dir": str(config.apps_dir.as_posix()),
            "meta_file": str(config.meta_file.as_posix()),
            "shims_dir": str(config.shims_dir.as_posix()),
        }
        CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with CONFIG_FILE.open("w", encoding="utf-8") as configfile:
            _config.write(configfile)
    except Exception as e:
        raise ConfigError(f"Failed to save configuration: {e}") from e


def load_config():
    if not CONFIG_FILE.exists():
        raise ConfigError(f"Configuration file does not exist: {CONFIG_FILE}. Please run 'oppm init' first.")

    parser = configparser.ConfigParser()
    try:
        _ = parser.read(CONFIG_FILE, encoding="utf-8")
        config_section = parser["config"]
        root_dir = Path(config_section["root_dir"])
        apps_dir = Path(config_section["apps_dir"])
        meta_file = Path(config_section["meta_file"])
        shims_dir = Path(config_section["shims_dir"])
        config = OPPMConfig(root_dir, apps_dir, meta_file, shims_dir)
        return config
    except (FileNotFoundError, KeyError, configparser.Error) as e:
        raise ConfigError(f"Failed to load configuration: {e}. You may need to run 'oppm init' again.") from e


def update_config(config: OPPMConfig):
    return save_config(config)
