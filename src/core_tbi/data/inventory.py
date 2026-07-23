from __future__ import annotations

from pathlib import Path
import pandas as pd


def inventory_directory(root: str | Path, output: str | Path | None = None) -> pd.DataFrame:
    """Inventory available files only; never infer absent metadata or formats."""
    root = Path(root)
    records = [{"path": str(p.relative_to(root)), "bytes": p.stat().st_size, "suffix": p.suffix.lower()}
               for p in root.rglob("*") if p.is_file()]
    table = pd.DataFrame(records, columns=["path", "bytes", "suffix"])
    if output:
        summary = f"<h1>Dataset inventory</h1><p>Root: {root}</p>" + table.to_html(index=False, escape=True)
        Path(output).parent.mkdir(parents=True, exist_ok=True)
        Path(output).write_text(summary, encoding="utf-8")
    return table
