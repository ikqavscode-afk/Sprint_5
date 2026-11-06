#!/usr/bin/env python3
"""Создаёт метки и GitHub Issues из data/api-bugs.json.

  python3 scripts/create_issues.py            # сухой прогон: только печатает, что будет создано
  python3 scripts/create_issues.py --apply    # создать метки и Issues в репозитории

Повторный запуск безопасен: уже созданные Issues пропускаются.
Запускается кнопкой в GitHub Actions (workflow "Setup issues") или локально через GitHub CLI.
"""
import json, os, pathlib, re, subprocess, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
REPO = os.environ.get("GITHUB_REPOSITORY", "ikqavscode-afk/Sprint_5")
RAW = f"https://raw.githubusercontent.com/{REPO}/main/bug-reports/screenshots/"
apply = "--apply" in sys.argv
CLS = {"validation-missing": "200 вместо 4xx", "unhandled-500": "500 вместо 400", "incomplete-response": "неполное тело", "wrong-status": "неверный код"}


def run(cmd):
    if apply:
        subprocess.run(cmd, check=True)
    else:
        print("DRY-RUN:", " ".join(cmd[:6]), "...")


def body(b):
    parts = [f"**ID:** `{b['id']}` · **Запрос:** `{b['method']} {b['path']}` · **Ожидали:** {b['expected_status']} · **Получили:** {b['actual_status']}",
             f"**Класс:** {CLS[b['class']]} · **Серьёзность:** {b['severity']}"]
    if b["setup"]:
        parts += ["### Подготовка"] + [f"- {s}" for s in b["setup"]]
    if b["request_body"]:
        parts += ["### Тело запроса", f"```{'xml' if b['content_type'] == 'XML' else 'json'}\n{b['request_body']}\n```"]
    parts += ["### Ожидаемый результат", f"```text\n{b['expected']}\n```", "### Фактический результат", f"```text\n{b['actual']}\n```"]
    if b.get("screenshot"):
        parts += ["### Скриншот", f"![{b['id']}]({RAW}{b['screenshot']})"]
    return "\n\n".join(parts)


def main():
    labels = re.findall(r'name: "([^"]+)", color: "(\w+)", description: "([^"]*)"', (ROOT / ".github/labels.yml").read_text())
    for n, c, d in labels:
        run(["gh", "label", "create", n, "--color", c, "--description", d, "--force", "--repo", REPO])
    existing = set()
    if apply:
        out = subprocess.run(["gh", "issue", "list", "--repo", REPO, "--state", "all", "--limit", "500", "--json", "title"], check=True, capture_output=True, text=True).stdout
        existing = {i["title"] for i in json.loads(out)}
    for b in json.loads((ROOT / "data/api-bugs.json").read_text()):
        title = f"[{b['id']}] {b['method']} {b['path']}: {CLS[b['class']]}"
        if title in existing:
            print("уже есть, пропуск:", b["id"])
            continue
        cmd = ["gh", "issue", "create", "--repo", REPO, "--title", title, "--body", body(b)]
        for l in ["bug", f"class: {b['class']}", f"severity: {b['severity']}", f"area: {b['area']}", "status: open"]:
            cmd += ["--label", l]
        run(cmd)
    print("Готово." if apply else "Это был сухой прогон. Добавьте --apply, чтобы создать Issues.")


if __name__ == "__main__":
    main()
