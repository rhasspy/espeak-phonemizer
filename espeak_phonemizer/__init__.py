from pathlib import Path

_DIR = Path(__file__).parent
__version__ = (_DIR / "VERSION").read_text().strip()
