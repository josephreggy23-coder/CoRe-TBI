from __future__ import annotations

from pathlib import Path
import hashlib
import json
import requests


FIGSHARE_ARTICLES = {"alma": 17212856}


def fetch_figshare_inventory(dataset_id: str, destination: str | Path = "data/raw") -> dict:
    """Retrieve only official Figshare metadata, not data files.

    This intentionally inventories the article before a user chooses to download
    files. File checksums and links are saved so that later acquisition is
    traceable and raw data are never overwritten.
    """
    if dataset_id not in FIGSHARE_ARTICLES:
        raise ValueError(f"No official Figshare adapter for {dataset_id!r}")
    response = requests.get(f"https://api.figshare.com/v2/articles/{FIGSHARE_ARTICLES[dataset_id]}", timeout=30)
    response.raise_for_status()
    metadata = response.json()
    root = Path(destination) / dataset_id
    root.mkdir(parents=True, exist_ok=True)
    record = {
        "dataset_id": dataset_id, "source": metadata.get("url_public_api"), "title": metadata.get("title"),
        "doi": metadata.get("doi"), "license": metadata.get("license"),
        "files": [{key: item.get(key) for key in ("id", "name", "size", "supplied_md5", "download_url")} for item in metadata.get("files", [])],
    }
    (root / "official_figshare_inventory.json").write_text(json.dumps(record, indent=2), encoding="utf-8")
    return record


def download_figshare_file(dataset_id: str, file_id: int, destination: str | Path = "data/raw") -> Path:
    """Download one explicitly selected official file and verify its checksum."""
    record = fetch_figshare_inventory(dataset_id, destination)
    file = next((item for item in record["files"] if item["id"] == file_id), None)
    if not file:
        raise ValueError(f"File ID {file_id} is not in the official {dataset_id} inventory.")
    target = Path(destination) / dataset_id / file["name"]
    if target.exists():
        raise FileExistsError(f"Refusing to overwrite raw data: {target}")
    response = requests.get(file["download_url"], stream=True, timeout=60); response.raise_for_status()
    digest = hashlib.md5()
    with target.open("xb") as handle:
        for chunk in response.iter_content(chunk_size=1024 * 1024):
            if chunk:
                handle.write(chunk); digest.update(chunk)
    if file.get("supplied_md5") and digest.hexdigest() != file["supplied_md5"]:
        target.unlink(missing_ok=True)
        raise ValueError("Checksum failed; incomplete file removed.")
    return target
