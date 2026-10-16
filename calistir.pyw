"""Sağ tık menüsünün çağırdığı giriş noktası (pythonw ile, konsol penceresi açmadan)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from toonme_karakter.uygulama import main  # noqa: E402

raise SystemExit(main(sys.argv[1:]))
