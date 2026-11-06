"""Central project paths. Import these instead of hard-coding locations."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
RAW = DATA / "raw"
BOC = RAW / "boc"
FRED = RAW / "fred"
YAHOO = RAW / "yahoo"
PROCESSED = DATA / "processed"
RESULTS = ROOT / "results"
TABLES = RESULTS / "tables"
FIGURES = RESULTS / "figures"
