#!/usr/bin/env python3
"""Разбор API «Places»: стратегия, проверки, коллекция Postman и документы.

Источник — требования к API (регистрация, авторизация, добавление карточки места).
Генерирует: data/api-places.json, postman/places-api.postman_collection.json,
test-analysis/places-api.md, test-cases/places-api-checklist.md.
Запуск: python3 scripts/build_places.py
"""
import json

from config import ROOT, SITE

# ---------------- Контракт (по документации API)
ENDPOINTS = [
    {"id": "signup", "method": "POST", "path": "/api/signup", "title": "Регистрация пользователя", "auth": False,
     "fields": [
         {"field": "email", "type": "string", "required": True, "rule": "5–50 символов (вся строка); английские буквы, цифры, «-», «.», «@»"},
         {"field": "password", "type": "string", "required": True, "rule": "8–20 символов; минимум: заглавная, строчная, цифра, спецсимвол"}],
     "success": {"status": 201, "body": "data: _id, email, name, about, avatar"},
     "errors": [[400, "Не передан обязательный параметр"], [400, "Почта введена некорректно"], [400, "Пароль введен некорректно"],
                [409, "Пользователь с таким email уже существует"], [500, "Внутренняя ошибка сервера"]]},
    {"id": "signin", "method": "POST", "path": "/api/signin", "title": "Авторизация пользователя", "auth": False,
     "fields": [
         {"field": "email", "type": "string", "required": True, "rule": "почта, указанная при регистрации"},
         {"field": "password", "type": "string", "required": True, "rule": "пароль пользователя"}],
     "success": {"status": 200, "body": "data: _id, email, name, about, avatar; token (JWT)"},
     "errors": [[400, "Не передан обязательный параметр"], [400, "Почта введена некорректно"], [401, "Неправильные почта или пароль"], [404, "Пользователь не найден"]]},
    {"id": "cards", "method": "POST", "path": "/api/cards", "title": "Добавление карточки места", "auth": True,
     "fields": [
         {"field": "name", "type": "string", "required": True, "rule": "2–30 символов"},
         {"field": "link", "type": "string", "required": True, "rule": "валидный URL изображения"}],
     "success": {"status": 201, "body": "data: _id, name, link, owner, likes[], createdAt"},
     "errors": [[400, "Отсутствует наименование"], [400, "Отсутствует ссылка на изображение"], [400, "Наименование введено некорректно"],
                [400, "Ссылка введена некорректно"], [401, "Требуется авторизация"]]},
]

STRATEGY = [
    ["Регистрация пользователя", "Комбинации email и пароля: пустые поля, формат, длина, допустимые символы, валидные данные", "Классы эквивалентности, граничные значения, негативные сценарии"],
    ["Авторизация пользователя", "Вход с корректными и некорректными данными, пустыми полями, несуществующим пользователем", "Таблица принятия решений, классы эквивалентности"],
    ["Обработка токена", "Отсутствие токена, недействительный токен, успешная авторизация", "Позитивные и негативные сценарии"],
    ["Добавление карточки места", "Поля name и link: пустые, короткие, длинные, неверный URL, корректные значения", "Классы эквивалентности, граничные значения"],
    ["Ответы сервера", "Структура и типы полей успешного ответа, коды состояния", "Позитивные и негативные сценарии"],
    ["Обработка ошибок", "Сообщения при валидации, отсутствии параметров, неверных данных, неавторизованном доступе", "Таблица принятия решений, негативные сценарии"],
]

# Два варианта ожидаемых результатов для входа: в материалах они расходились.
DECISION = {
    "columns": ["Email валиден", "Пароль валиден", "Пользователь существует"],
    "variants": [
        {"id": "A", "title": "Вариант A: любая ошибка данных даёт 401",
         "rows": [[1, 1, 1, "200", "Успешная авторизация, token"],
                  [1, 1, 0, "404", "Пользователь не найден"],
                  [1, 0, 1, "401", "Неправильные почта или пароль"],
                  [1, 0, 0, "401", "Неправильные почта или пароль"],
                  [0, 1, 1, "401", "Неправильные почта или пароль"],
                  [0, 1, 0, "401", "Неправильные почта или пароль"],
                  [0, 0, 1, "401", "Неправильные почта или пароль"],
                  [0, 0, 0, "401", "Неправильные почта или пароль"]]},
        {"id": "B", "title": "Вариант B: формат email проверяется отдельно (по документации)",
         "rows": [[1, 1, 1, "200", "Успешная авторизация, token"],
                  [1, 0, 1, "401", "Неправильные почта или пароль"],
                  [0, 1, 1, "400", "Почта введена некорректно"],
                  [0, 0, 1, "401", "Неправильные почта или пароль"],
                  [1, 1, 0, "404", "Пользователь не найден"],
                  [0, 1, 0, "404", "Пользователь не найден"],
                  [0, 0, 0, "404", "Пользователь не найден"]]}],
    "diff": "Расхождения: некорректный email у существующего пользователя (401 или 400) и сочетания с несуществующим пользователем (401 или 404).",
}

GRAY = [
    ["GZ-P1", "Длина email", "В документации длина считается для всей строки (5–50). В примерах из материалов считалась длина части до «@».", "Что именно ограничено: вся строка или часть до «@»?", "Принято: вся строка. Границы строятся по общей длине."],
    ["GZ-P2", "Пустое значение или отсутствие поля", "Сообщение для пустой строки в email, password, name не определено: «Не передан обязательный параметр» или «…некорректно».", "Одинаково ли обрабатываются пустая строка и отсутствие поля?", "Проверяется только код ответа (400)."],
    ["GZ-P3", "Вход: некорректный формат email", "Документация даёт 400 «Почта введена некорректно», а в одном из вариантов таблицы принят 401.", "Проверяется ли формат email при входе?", "Принято по документации: 400."],
    ["GZ-P4", "Вход: несуществующий пользователь", "Один вариант таблицы даёт 404 для любых данных, другой смешивает 401 и 404.", "Какой код при несуществующем пользователе и неверном пароле?", "Принято: 404 для корректных данных."],
    ["GZ-P5", "Допустимые спецсимволы пароля", "Дан пример «!@#$%^&*()», полный список не определён; кириллица не описана.", "Какие символы допустимы?", "Кириллица считается недопустимой."],
    ["GZ-P6", "Пробелы в названии места", "Пробел до или после названия: обрезается ли, входит ли в длину?", "Применяется ли trim?", "Проверка не включена в чек-лист."],
    ["GZ-P7", "Формат ссылки", "Не определены допустимые схемы (http, ftp), проверка доступности изображения.", "Что считается валидным URL?", "Проверяется формат «https://…»."],
    ["GZ-P8", "Токен", "Не указаны срок жизни и формат заголовка (с префиксом Bearer или без).", "Как передавать токен?", "Заголовок Authorization со значением токена."],
    ["GZ-P9", "Ошибка 500 при регистрации", "Внутренняя ошибка описана в документации, условия её воспроизведения не указаны.", "Когда возвращается 500?", "Не проверяется."],
    ["GZ-P10", "Регистр email", "Считаются ли «A@example.com» и «a@example.com» одним пользователем?", "Нужна ли нормализация?", "Не проверяется."],
    ["GZ-P11", "Создание записи в БД", "Проверить сохранение пользователя в базе нельзя: нет доступа к БД и нет метода чтения.", "Есть ли метод получения пользователя?", "Пропущено (Skipped)."],
]

# ---------------- Генерация проверок
PW_OK = "Qq1@"
mk_pw = lambda n: PW_OK + "a" * (n - 4)
mk_name = lambda n: "Я" + "а" * (n - 1)
URL_OK = "https://example.com/image.jpg"
checks = []


def add(ep, group, title, body=None, status=200, message=None, auth="none", method="POST", path=None, note="", raw=None, email_len=None, email_var=False, pw_var=False, gz=None):
    checks.append({"id": f"PL-{len(checks) + 1:03d}", "ep": ep, "group": group, "title": title, "method": method,
                   "path": path or {"signup": "/api/signup", "signin": "/api/signin", "cards": "/api/cards", "common": "/api/signup"}[ep],
                   "auth": auth, "body": body, "raw": raw, "email_len": email_len, "email_var": email_var, "pw_var": pw_var,
                   "status": status, "message": message, "note": note, "gz": gz})


# регистрация
add("signup", "Позитивные", "Валидные email и пароль", {"email": "", "password": mk_pw(10)}, 201, email_len=20, email_var=True)
for n, st in [(4, 400), (5, 201), (6, 201), (10, 201), (49, 201), (50, 201), (51, 400)]:
    note = "нижняя граница: форматно невалидна при любой длине" if n == 4 else ""
    add("signup", "Позитивные" if st == 201 else "Негативные", f"Email: {n} симв.", {"email": "", "password": mk_pw(10)}, st,
        None if st == 201 else "Почта введена некорректно", email_len=n, note=note, gz="GZ-P1")
add("signup", "Негативные", "Email с недопустимыми символами", {"email": "te()st@exam!ple.com", "password": mk_pw(10)}, 400, "Почта введена некорректно")
add("signup", "Негативные", "Пустой email", {"email": "", "password": mk_pw(10)}, 400, gz="GZ-P2")
add("signup", "Негативные", "Нет поля email", {"password": mk_pw(10)}, 400, "Не передан обязательный параметр")
add("signup", "Негативные", "Нет поля password", {"email": "user@example.com"}, 400, "Не передан обязательный параметр")
for n, st in [(7, 400), (8, 201), (9, 201), (19, 201), (20, 201), (21, 400)]:
    add("signup", "Позитивные" if st == 201 else "Негативные", f"Пароль: {n} симв.", {"email": "", "password": mk_pw(n)}, st,
        None if st == 201 else "Пароль введен некорректно", email_len=20, email_var=False)
for title, pw in [("Пустой пароль", ""), ("Пароль без заглавной буквы", "qq1@aaaaaa"), ("Пароль без строчной буквы", "QQ1@AAAAAA"),
                  ("Пароль без цифры", "Qqq@aaaaaa"), ("Пароль без спецсимвола", "Qq1aaaaaaa"), ("Пароль с кириллицей", "QЩ1@aaaaaa")]:
    add("signup", "Негативные", title, {"email": "", "password": pw}, 400, None if title in ("Пустой пароль", "Пароль с кириллицей") else "Пароль введен некорректно",
        email_len=20, gz="GZ-P2" if title == "Пустой пароль" else ("GZ-P5" if "кириллицей" in title else None))
add("signup", "Негативные", "Повторная регистрация того же email", {"email": "{{regEmail}}", "password": mk_pw(10)}, 409, "Пользователь с таким email уже существует")
# вход
add("signin", "Позитивные", "Вход с валидными данными (сохраняет token)", {"email": "{{regEmail}}", "password": "{{regPass}}"}, 200)
add("signin", "Негативные", "Нет поля email", {"password": "{{regPass}}"}, 400, "Не передан обязательный параметр")
add("signin", "Негативные", "Нет поля password", {"email": "{{regEmail}}"}, 400, "Не передан обязательный параметр")
add("signin", "Негативные", "Некорректный формат email", {"email": "te()st@exam!ple.com", "password": "{{regPass}}"}, 400, "Почта введена некорректно", gz="GZ-P3")
add("signin", "Негативные", "Неверный пароль существующего пользователя", {"email": "{{regEmail}}", "password": "Wrong1@aaaa"}, 401, "Неправильные почта или пароль")
add("signin", "Негативные", "Несуществующий пользователь", {"email": "nouser.0000@example.com", "password": "Qq1@aaaaaa"}, 404, "Пользователь не найден", gz="GZ-P4")
# карточки
add("cards", "Позитивные", "Валидные name и link", {"name": "Смурфленд", "link": URL_OK}, 201, auth="token")
for n, st in [(1, 400), (2, 201), (3, 201), (29, 201), (30, 201), (31, 400)]:
    add("cards", "Позитивные" if st == 201 else "Негативные", f"Название: {n} симв.", {"name": mk_name(n), "link": URL_OK}, st,
        None if st == 201 else "Наименование введено некорректно", auth="token")
add("cards", "Негативные", "Пустое название", {"name": "", "link": URL_OK}, 400, auth="token", gz="GZ-P2")
add("cards", "Негативные", "Нет поля name", {"link": URL_OK}, 400, "Отсутствует наименование", auth="token")
add("cards", "Негативные", "Нет поля link", {"name": "Смурфленд"}, 400, "Отсутствует ссылка на изображение", auth="token")
add("cards", "Негативные", "Невалидная ссылка", {"name": "Смурфленд", "link": "RandomText"}, 400, "Ссылка введена некорректно", auth="token", gz="GZ-P7")
add("cards", "Негативные", "Пустая ссылка", {"name": "Смурфленд", "link": ""}, 400, auth="token", gz="GZ-P2")
add("cards", "Негативные", "Нет токена авторизации", {"name": "Смурфленд", "link": URL_OK}, 401, "Требуется авторизация", auth="none")
add("cards", "Негативные", "Некорректный токен", {"name": "Смурфленд", "link": URL_OK}, 401, "Требуется авторизация", auth="bad", gz="GZ-P8")
# общие
add("common", "Негативные", "Невалидный JSON в теле", None, 400, raw='{"email": "user@example.com", "password": ', path="/api/signup")
add("common", "Негативные", "Метод GET вместо POST для регистрации", None, 405, method="GET", path="/api/signup", note="код 405 не описан в документации")
add("common", "Негативные", "Метод PUT вместо POST для входа", None, 405, method="PUT", path="/api/signin", note="код 405 не описан в документации")

# ---------------- data
data = {"name": "Places API", "endpoints": ENDPOINTS, "strategy": STRATEGY, "decision": DECISION, "gray_zones": [
    {"id": g[0], "topic": g[1], "problem": g[2], "question": g[3], "assumption": g[4]} for g in GRAY], "checks": checks}
(ROOT / "data").mkdir(exist_ok=True)
(ROOT / "data/api-places.json").write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")


# ---------------- Postman
def mk_email_js():
    return ("function mk(total){const d='@b.c';const l=Math.max(total-d.length,0);const a='abcdefghijklmnopqrstuvwxyz';let s='';"
            "while(s.length<l)s+=a[Math.floor(Math.random()*26)];return s+d}")


def headers(c):
    h = [{"key": "Content-Type", "value": "application/json"}]
    if c["auth"] == "token":
        h.append({"key": "Authorization", "value": "{{token}}"})
    elif c["auth"] == "bad":
        h.append({"key": "Authorization", "value": "abc.def.ghi"})
    return h


def body_raw(c):
    if c["raw"] is not None:
        return c["raw"]
    if c["body"] is None:
        return None
    b = dict(c["body"])
    if c["email_len"] is not None:
        b["email"] = "{{email}}"
    return json.dumps(b, ensure_ascii=False, indent=2)


def tests(c):
    t = [f'pm.test("{c["id"]}: статус {c["status"]}", function () {{ pm.response.to.have.status({c["status"]}); }});']
    if c["message"]:
        t.append(f'pm.test("Сообщение: {c["message"]}", function () {{ pm.expect(pm.response.json().message).to.eql({json.dumps(c["message"], ensure_ascii=False)}); }});')
    if c["id"] == "PL-001":
        t.append('pm.test("Есть профиль пользователя", function () { const d = pm.response.json().data; pm.expect(d).to.have.property("_id"); pm.expect(d).to.have.property("email"); });')
        t.append('pm.collectionVariables.set("regEmail", pm.variables.get("email"));')
    if c["ep"] == "signin" and c["status"] == 200:
        t.append('pm.test("Есть token", function () { pm.expect(pm.response.json().token).to.be.a("string"); });')
        t.append('pm.collectionVariables.set("token", pm.response.json().token);')
    if c["ep"] == "cards" and c["status"] == 201:
        t.append('pm.test("Структура карточки", function () { const d = pm.response.json().data; pm.expect(d).to.include.keys("_id", "name", "link", "owner", "likes", "createdAt"); });')
    return t


def item(c):
    it = {"name": f"[{c['id']}] {c['title']}", "event": [{"listen": "test", "script": {"type": "text/javascript", "exec": tests(c)}}],
          "request": {"method": c["method"], "header": headers(c), "url": {"raw": "{{baseUrl}}" + c["path"]},
                      "description": (c["note"] + " " if c["note"] else "") + (f"Серая зона {c['gz']}." if c["gz"] else "")}}
    b = body_raw(c)
    if b is not None:
        it["request"]["body"] = {"mode": "raw", "raw": b, "options": {"raw": {"language": "json"}}}
    if c["email_len"] is not None:
        it["event"].insert(0, {"listen": "prerequest", "script": {"type": "text/javascript", "exec": [mk_email_js(), f'pm.variables.set("email", mk({c["email_len"]}));']}})
    return it


FOLD = [("signup", "Регистрация · POST /api/signup"), ("signin", "Авторизация · POST /api/signin"), ("cards", "Карточки · POST /api/cards"), ("common", "Общие проверки")]
coll = {"info": {"name": "Places API — разбор", "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
                 "description": "Запускайте папки по порядку: сначала регистрация (создаёт пользователя), затем вход (сохраняет token), затем карточки. Укажите baseUrl в переменных коллекции."},
        "variable": [{"key": "baseUrl", "value": ""}, {"key": "regEmail", "value": ""}, {"key": "regPass", "value": mk_pw(10)}, {"key": "token", "value": ""}],
        "item": [{"name": n, "item": [item(c) for c in checks if c["ep"] == k]} for k, n in FOLD]}
(ROOT / "postman/places-api.postman_collection.json").write_text(json.dumps(coll, ensure_ascii=False, indent=2) + "\n")

# ---------------- Markdown
MSG = lambda c: f" · «{c['message']}»" if c["message"] else ""
md = ["# Разбор API: Places", "",
      "Дополнительный разбор к спринту 5: полный цикл тест-дизайна для API из трёх методов (регистрация, вход, добавление карточки места). "
      "Здесь отработаны стратегия, декомпозиция, техники и чек-лист. Данные: [`data/api-places.json`](../data/api-places.json), "
      "коллекция Postman: [`postman/places-api.postman_collection.json`](../postman/places-api.postman_collection.json), "
      f"интерактивная версия: [Разбор API]({SITE}places.html).", "",
      "## Контракт", "", "| Метод | Путь | Авторизация | Успех | Ошибки |", "|---|---|---|---|---|"]
for e in ENDPOINTS:
    md.append(f"| {e['method']} | `{e['path']}` | {'токен' if e['auth'] else 'нет'} | {e['success']['status']} | " + "; ".join(f"{s} {m}" for s, m in e["errors"]) + " |")
md += ["", "## Стратегия тестирования", "", "| Объект | Что проверяем | Техника |", "|---|---|---|"] + [f"| {a} | {b} | {c} |" for a, b, c in STRATEGY]
md += ["", "## Декомпозиция", "", "```mermaid", "mindmap", "  root((Places API))", "    Регистрация", "      Валидные данные", "      Email: длина и символы",
       "      Пароль: длина и состав", "      Нет обязательных полей", "      Повторная регистрация", "    Авторизация", "      Валидные данные",
       "      Неверный пароль", "      Несуществующий пользователь", "      Токен", "    Карточка места", "      Название 2–30", "      Ссылка на изображение",
       "      Нет токена", "    Общие", "      Невалидный JSON", "      Другие методы", "```", "",
       "## Классы эквивалентности и границы", "", "| Поле | Границы (вся строка) | Классы |", "|---|---|---|",
       "| email | 4 · **5** · 6 … 49 · **50** · 51 | пусто; валидный; недопустимые символы; нет поля |",
       "| password | 7 · **8** · 9 … 19 · **20** · 21 | пусто; без заглавной; без строчной; без цифры; без спецсимвола; кириллица |",
       "| name | 1 · **2** · 3 … 29 · **30** · 31 | пусто; валидное; нет поля |",
       "| link | n/a | валидный URL; пусто; не URL; нет поля |", "",
       "## Таблица принятия решений: вход", ""]
for v in DECISION["variants"]:
    md += [f"### {v['title']}", "", "| " + " | ".join(DECISION["columns"]) + " | Код | Результат |", "|---|---|---|---|---|"]
    md += [f"| {'Да' if r[0] else 'Нет'} | {'Да' if r[1] else 'Нет'} | {'Да' if r[2] else 'Нет'} | {r[3]} | {r[4]} |" for r in v["rows"]] + [""]
md += [DECISION["diff"], "", "## Серые зоны", "", "| ID | Тема | Проблема | Вопрос | Допущение |", "|---|---|---|---|---|"]
md += [f"| {g[0]} | {g[1]} | {g[2]} | {g[3]} | {g[4]} |" for g in GRAY]
(ROOT / "test-analysis/places-api.md").write_text("\n".join(md) + "\n")

cl = ["# Чек-лист: Places API", "", f"Всего проверок: **{len(checks)}**. Коллекция Postman содержит их все.", "", "| ID | Метод | Путь | Проверка | Ожидание | Серая зона |", "|---|---|---|---|---|---|"]
cl += [f"| {c['id']} | {c['method']} | `{c['path']}` | {c['title']} | {c['status']}{MSG(c)} | {c['gz'] or ''} |" for c in checks]
(ROOT / "test-cases/places-api-checklist.md").write_text("\n".join(cl) + "\n")
print("OK:", len(checks), "проверок")
