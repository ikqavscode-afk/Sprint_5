"""Общие настройки скриптов: адреса и пути.

Любое переименование репозитория или сайта делается здесь один раз.
"""
import os
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
REPO = os.environ.get("GITHUB_REPOSITORY", "ikqavscode-afk/Sprint_5")
SITE = "https://ikqavscode-afk.github.io/Sprint_5/"
COMMON_REPO_URL = "https://github.com/ikqavscode-afk/qa-test-documentation"
RAW_SCREENSHOTS = f"https://raw.githubusercontent.com/{REPO}/main/bug-reports/screenshots/"
