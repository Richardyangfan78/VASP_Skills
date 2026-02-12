"""Configuration management for VASP Skills."""

import os
import yaml
from pathlib import Path
from typing import Any, Optional


_DEFAULT_CONFIG_PATHS = [
    Path(__file__).parent.parent / "config.yaml",
    Path.home() / ".vasp_skills" / "config.yaml",
    Path("config.yaml"),
]


class Config:
    """Global configuration singleton for VASP Skills."""

    _instance: Optional["Config"] = None
    _data: dict

    def __new__(cls, config_path: Optional[str] = None):
        if cls._instance is None or config_path is not None:
            cls._instance = super().__new__(cls)
            cls._instance._data = cls._load(config_path)
        return cls._instance

    @staticmethod
    def _load(config_path: Optional[str] = None) -> dict:
        if config_path and os.path.isfile(config_path):
            with open(config_path) as f:
                return yaml.safe_load(f) or {}
        for p in _DEFAULT_CONFIG_PATHS:
            if p.is_file():
                with open(p) as f:
                    return yaml.safe_load(f) or {}
        return {}

    def get(self, key: str, default: Any = None) -> Any:
        """Get a config value using dot-notation keys (e.g. 'defaults.encut')."""
        keys = key.split(".")
        val = self._data
        for k in keys:
            if isinstance(val, dict):
                val = val.get(k)
            else:
                return default
            if val is None:
                return default
        return val

    def set(self, key: str, value: Any):
        """Set a config value using dot-notation keys."""
        keys = key.split(".")
        d = self._data
        for k in keys[:-1]:
            d = d.setdefault(k, {})
        d[keys[-1]] = value

    @property
    def potcar_dir(self) -> str:
        return os.path.expanduser(self.get("potcar_dir", "~/VASP_PP_LIB"))

    @property
    def vasp_cmd(self) -> str:
        return self.get("vasp_cmd", "mpirun -np 4 vasp_std")

    @property
    def defaults(self) -> dict:
        return self.get("defaults", {})

    def reload(self, config_path: Optional[str] = None):
        """Reload configuration from file."""
        self._data = self._load(config_path)
