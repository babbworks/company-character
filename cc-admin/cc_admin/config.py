from pathlib import Path
import yaml


_CONFIG_FILE = Path(__file__).parent.parent / ".cc-admin.yml"


def load_admin_config() -> dict:
    with open(_CONFIG_FILE) as f:
        return yaml.safe_load(f)


def load_state(admin_config: dict) -> dict:
    state_path = Path(_CONFIG_FILE.parent / admin_config["state_path"])
    section_map_file = state_path / "section-map.yml"
    with open(section_map_file) as f:
        return yaml.safe_load(f)


def dist_path(admin_config: dict) -> Path:
    return Path(_CONFIG_FILE.parent / admin_config["dist_path"])


def cli_path(admin_config: dict) -> Path:
    return Path(_CONFIG_FILE.parent / admin_config["cli_path"])


def state_path(admin_config: dict) -> Path:
    return Path(_CONFIG_FILE.parent / admin_config["state_path"])


def overrides_path() -> Path:
    return Path(__file__).parent.parent / "overrides"
