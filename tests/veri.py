"""Test verisi: BlueStacks'teki gerçek ToonMe ekranlarından alınmış uiautomator dökümleri."""
from pathlib import Path

FIXTURES = Path(__file__).parent / "fixtures"


def F(ad: str) -> str:
    return (FIXTURES / ad).read_text(encoding="utf-8")
