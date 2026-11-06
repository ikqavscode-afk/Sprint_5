#!/usr/bin/env python3
"""Копирует данные, скриншоты и файлы для сайта GitHub Pages в docs/."""
import pathlib, shutil

ROOT = pathlib.Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
for sub in ("data", "media", "files"):
    (DOCS / sub).mkdir(parents=True, exist_ok=True)
for f in (ROOT / "data").glob("api-*.json"):
    shutil.copy(f, DOCS / "data" / f.name)
for f in (ROOT / "bug-reports" / "screenshots").glob("*"):
    shutil.copy(f, DOCS / "media" / f.name)
for f in list((ROOT / "postman").glob("*.json")) + [ROOT / "api" / "openapi-tested.yaml"]:
    shutil.copy(f, DOCS / "files" / f.name)
print("sync ok")
