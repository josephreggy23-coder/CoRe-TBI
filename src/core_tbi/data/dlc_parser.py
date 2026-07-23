from __future__ import annotations

from pathlib import Path
import re
import pandas as pd


def _normalise(name: object) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(name).lower()).strip("_")


def parse_dlc_csv(path: str | Path, metadata: dict | None = None, frame_rate: float | None = None) -> pd.DataFrame:
    """Parse common DLC multi-index or flattened exports into long pose rows."""
    path, metadata = Path(path), metadata or {}
    raw = pd.read_csv(path, header=[0, 1, 2])
    if not isinstance(raw.columns, pd.MultiIndex) or not any(_normalise(x) in {"x", "y", "likelihood"} for x in raw.columns.get_level_values(-1)):
        raw = pd.read_csv(path)
        records = []
        for col in raw.columns:
            match = re.match(r"(.+?)[_\- ](x|y|z|likelihood)$", _normalise(col))
            if match:
                records.append((match.group(1), match.group(2), col))
        pieces = []
        for bodypart in sorted({x[0] for x in records}):
            subset = {coord: col for bp, coord, col in records if bp == bodypart}
            frame = pd.DataFrame({"frame": raw.index, "bodypart": bodypart, **{k: raw[v] for k, v in subset.items()}})
            pieces.append(frame)
        long = pd.concat(pieces, ignore_index=True) if pieces else pd.DataFrame(columns=["frame", "bodypart", "x", "y", "likelihood"])
    else:
        scorer, bodyparts, coords = raw.columns.get_level_values(0), raw.columns.get_level_values(1), raw.columns.get_level_values(2)
        pieces = []
        for bp in sorted(set(bodyparts)):
            cols = { _normalise(c): raw[(s, b, c)] for s, b, c in zip(scorer, bodyparts, coords, strict=True) if b == bp and _normalise(c) in {"x", "y", "z", "likelihood"}}
            if cols:
                pieces.append(pd.DataFrame({"frame": raw.index, "bodypart": _normalise(bp), **cols}))
        long = pd.concat(pieces, ignore_index=True)
    for column, value in metadata.items():
        long[column] = value
    long["time_seconds"] = long["frame"] / frame_rate if frame_rate else pd.NA
    for column in ["dataset_id", "animal_id", "session_id", "video_id", "condition", "injury_status", "timepoint", "days_post_injury", "task", "sex", "speed", "camera_view"]:
        if column not in long:
            long[column] = metadata.get(column, pd.NA)
    return long.drop_duplicates(subset=["frame", "bodypart"]).reset_index(drop=True)
