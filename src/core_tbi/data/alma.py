from __future__ import annotations

from pathlib import Path
import re
import pandas as pd


def inventory_alma_workbook(path: str | Path) -> pd.DataFrame:
    """Describe the official ALMA source workbook without altering it.

    The published Figshare workbook contains source tables arranged by figure.
    This function documents that structure; it does not pretend those charts
    are a complete per-animal pose table.
    """
    path = Path(path)
    workbook = pd.ExcelFile(path)
    rows = []
    for sheet in workbook.sheet_names:
        table = pd.read_excel(path, sheet_name=sheet, header=None)
        nonempty_rows = int(table.dropna(how="all").shape[0])
        nonempty_columns = int(table.dropna(axis=1, how="all").shape[1])
        rows.append({"source_file": path.name, "sheet": sheet, "rows": nonempty_rows, "columns": nonempty_columns, "interpretation": "published figure/source-data table; inspect before analytical reshaping"})
    return pd.DataFrame(rows)


def _clean_column(value: object) -> str:
    if pd.isna(value):
        return ""
    text = re.sub(r"[^a-z0-9]+", "_", str(value).lower()).strip("_")
    return text.replace("no_frames", "n_frames")


def split_feature_blocks(raw: pd.DataFrame, header_row: int = 3) -> pd.DataFrame:
    """Extract repeated labelled feature blocks from an ALMA figure source table.

    The published workbook places one or more figure-specific feature matrices
    side by side. This reader preserves each source block and its row-level
    group. It never fabricates animal identifiers when the source table does
    not supply them.
    """
    headers = raw.iloc[header_row]
    starts = [index for index, value in enumerate(headers) if _clean_column(value) == "group"]
    blocks: list[pd.DataFrame] = []
    for number, start in enumerate(starts, start=1):
        end = next((candidate for candidate in starts if candidate > start), len(headers))
        labels = [_clean_column(value) for value in headers.iloc[start:end]]
        valid = [offset for offset, label in enumerate(labels) if label]
        if not valid:
            continue
        table = raw.iloc[header_row + 1 :, [start + offset for offset in valid]].copy()
        table.columns = [labels[offset] for offset in valid]
        table = table.dropna(how="all")
        if table.empty or "group" not in table:
            continue
        table["source_block"] = number
        table["source_row"] = table.index.astype(int)
        blocks.append(table)
    return pd.concat(blocks, ignore_index=True) if blocks else pd.DataFrame()


def extract_alma_feature_cycles(path: str | Path, sheet: str = "Figure_2_Panel_G") -> pd.DataFrame:
    """Create a provenance-rich feature-mode table from a published source sheet."""
    path = Path(path)
    raw = pd.read_excel(path, sheet_name=sheet, header=None)
    features = split_feature_blocks(raw)
    if features.empty:
        raise ValueError(f"No labelled feature blocks found in {sheet!r}.")
    features.insert(0, "dataset_id", "alma")
    features.insert(1, "source_file", path.name)
    features.insert(2, "source_sheet", sheet)
    features.insert(3, "observation_id", [f"alma_{sheet}_{idx:05d}" for idx in range(len(features))])
    features["animal_id"] = pd.NA
    features["session_id"] = pd.NA
    features["timepoint"] = features["group"].astype("string")
    features["condition"] = pd.NA
    features["identity_status"] = "not_available_in_published_source_table"
    return features
