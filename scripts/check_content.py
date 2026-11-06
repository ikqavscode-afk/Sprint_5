#!/usr/bin/env python3
"""Проверяет репозиторий на запретные слова и личные данные.

Ищет в текстовых файлах и внутри .docx/.xlsx: названия брендов и учебных платформ, внутренние адреса,
упоминания инструментов, настоящие почты и телефоны. Код возврата 1, если что-то найдено.
Запуск: python3 scripts/check_content.py
"""
import html
import os
import re
import sys
import zipfile

from config import ROOT

RULES = [
    ("бренд", re.compile(r"яндекс|yandex|mesto|\bYaM\b|YaMetro|ЯМ-", re.I)),
    ("учебная платформа", re.compile(r"учебн|практикум|praktikum|prakticum|воркшоп", re.I)),
    ("фирменные названия", re.compile(r"kittygram|foodgram|продуктовый помощник|stellar burgers", re.I)),
    ("внутренние адреса", re.compile(r"figma\.com|qa-faculty|qa-mesto|\.praktikum|\.prakticum", re.I)),
    ("упоминание ассистента", re.compile(r"cl[a]ude|anth[r]opic", re.I)),
    ("телефон", re.compile(r"\+7\d{10}|\b8\d{10}\b")),
]
EMAIL = re.compile(r"[\w.+-]+@([\w-]+\.[\w.-]+)")
SAFE_DOMAINS = {"example.com", "example.org", "b.c", "users.noreply.github.com"}
SAFE_PHONES = {"+70000000000"}
SKIP_DIRS = {".git", "__pycache__", "node_modules"}
SKIP_FILES = {"check_content.py"}  # содержит сами шаблоны поиска
TEXT_EXT = {".md", ".html", ".json", ".py", ".yml", ".yaml", ".js", ".css", ".txt", ".csv", ".cfg", ".toml"}
OFFICE_EXT = {".docx", ".xlsx"}


def scan_text(label, text, found):
    for n, line in enumerate(text.splitlines(), 1):
        for name, rx in RULES:
            for m in rx.finditer(line):
                if name == "телефон" and m.group(0) in SAFE_PHONES:
                    continue
                found.append((label, n, name, m.group(0)))
        for m in EMAIL.finditer(line):
            if m.group(1).lower().rstrip(".") not in SAFE_DOMAINS:
                found.append((label, n, "почта", m.group(0)))


def scan_office(path, found):
    label = os.path.relpath(path, ROOT)
    with zipfile.ZipFile(path) as z:
        for name in z.namelist():
            if name.endswith((".xml", ".rels")):
                xml = z.read(name).decode("utf8", "ignore")
                text = xml if name.endswith(".rels") else re.sub(r"<[^>]+>", " ", xml)  # в .rels адреса лежат в атрибутах
                scan_text(f"{label}:{name}", html.unescape(text), found)


def main():
    found = []
    for base, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for f in files:
            if f in SKIP_FILES:
                continue
            path = os.path.join(base, f)
            ext = os.path.splitext(f)[1].lower()
            if ext in TEXT_EXT:
                scan_text(os.path.relpath(path, ROOT), open(path, encoding="utf8", errors="ignore").read(), found)
            elif ext in OFFICE_EXT:
                scan_office(path, found)
    for label, n, name, word in found:
        print(f"{label}:{n}: [{name}] {word}")
    print(f"Проверка контента: найдено {len(found)}")
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main())
