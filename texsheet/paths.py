from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parent.parent / "project"
CONFIG_PATH = PROJECT_DIR / "config.yaml"
TABLES_DIR = PROJECT_DIR / "tables"
FIGURES_DIR = PROJECT_DIR / "figures"
TABLES_DATA_DIR = PROJECT_DIR / "tables_data"


def project_path(relative_path):
    return PROJECT_DIR / relative_path
