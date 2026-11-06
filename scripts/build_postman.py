#!/usr/bin/env python3
"""Генерирует коллекцию Postman (v2.1) и шаблон окружения из data/api-bugs.json.

Каждый дефект превращается в запрос с проверками ожидаемого поведения: после исправления
все проверки должны проходить. Запуск: python3 scripts/build_postman.py
"""
import json, pathlib, re

ROOT = pathlib.Path(__file__).resolve().parent.parent
bugs = json.loads((ROOT / "data/api-bugs.json").read_text())
checks = {c["id"]: c for c in json.loads((ROOT / "data/api-checks.json").read_text())}
FOLDERS = [("kits", "Наборы · kits"), ("delivery", "Доставка · fast-delivery"), ("orders", "Корзина · orders")]


def folder_of(area):
    return "orders" if area.startswith("orders") else area


def url_of(b):
    p = b["path"]
    p = p.replace("/kits/id/", "/kits/{{kitId}}/")
    if p.endswith("/orders/id"):
        p = p[: -len("id")] + "{{orderId}}"
    if b["id"] == "Б1-10":
        p = "/api/v1/orders/"
    return "{{baseUrl}}" + p


def tests_for(b):
    es = b["expected_status"] or 200
    lines = [f'pm.test("Статус ответа: {es}", function () {{ pm.response.to.have.status({es}); }});']
    if es >= 400 and b["area"] != "delivery":
        lines.append('pm.test("Ответ — JSON с кодом и сообщением", function () { const j = pm.response.json(); pm.expect(j).to.have.property("code"); pm.expect(j).to.have.property("message"); });')
    if "isItPossibleToDeliver=\"false\"" in b["expected"]:
        lines.append('pm.test("Доставка невозможна", function () { pm.expect(pm.response.text()).to.include(\'isItPossibleToDeliver="false"\'); });')
    return lines


def item(b):
    headers = []
    if b["content_type"] and "заголовк" not in b["title"].lower():
        headers.append({"key": "Content-Type", "value": "application/json" if b["content_type"] == "JSON" else "application/xml"})
    if b["area"].startswith("orders"):
        headers.append({"key": "Authorization", "value": "Bearer {{token}}"})
    req = {"method": b["method"], "header": headers, "url": {"raw": url_of(b)},
           "description": f"Ожидаемо: {b['expected_status']}. Фактически (дефект): {b['actual_status']}.\n\n{b['title']}"}
    if b["request_body"]:
        req["body"] = {"mode": "raw", "raw": b["request_body"], "options": {"raw": {"language": "json" if b["content_type"] == "JSON" else "xml"}}}
    label = checks.get(b["check"], {}).get("title") or b["title"]
    return {"name": f"[{b['id']}] " + re.sub(r"\s+", " ", label)[:90],
            "request": req, "event": [{"listen": "test", "script": {"type": "text/javascript", "exec": tests_for(b)}}]}


setup = {"name": "00 Подготовка (для корзины)", "item": [
    {"name": "Создать пользователя", "request": {"method": "POST", "header": [{"key": "Content-Type", "value": "application/json"}], "url": {"raw": "{{baseUrl}}/api/v1/users"},
     "body": {"mode": "raw", "raw": json.dumps({"firstName": "Имя", "email": "user@example.com", "phone": "+70000000000", "comment": "ОК", "address": "г. Город, ул. Улица, д. 1"}, ensure_ascii=False, indent=2), "options": {"raw": {"language": "json"}}}},
     "event": [{"listen": "test", "script": {"type": "text/javascript", "exec": ["// Сохраните токен из ответа в переменную коллекции token (формат ответа смотрите в документации API)."]}}]},
    {"name": "Создать корзину", "request": {"method": "POST", "header": [{"key": "Content-Type", "value": "application/json"}, {"key": "Authorization", "value": "Bearer {{token}}"}], "url": {"raw": "{{baseUrl}}/api/v1/orders"},
     "body": {"mode": "raw", "raw": json.dumps({"productsList": [{"id": 1, "quantity": 1}]}, indent=2), "options": {"raw": {"language": "json"}}}},
     "event": [{"listen": "test", "script": {"type": "text/javascript", "exec": ["pm.test('Корзина создана', function () { pm.response.to.have.status(200); });", "pm.collectionVariables.set('orderId', pm.response.json().id);"]}}]},
]}
coll = {
    "info": {"name": "Яндекс Прилавок API — регрессия дефектов", "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
             "description": "Каждый запрос воспроизводит дефект и проверяет ожидаемое поведение по требованиям. Перед запуском заполните baseUrl и token в окружении."},
    "variable": [{"key": "kitId", "value": "7"}, {"key": "orderId", "value": ""}],
    "item": [setup] + [{"name": title, "item": [item(b) for b in bugs if folder_of(b["area"]) == key]} for key, title in FOLDERS],
}
(ROOT / "postman").mkdir(exist_ok=True)
(ROOT / "postman/prilavok-api-regression.postman_collection.json").write_text(json.dumps(coll, ensure_ascii=False, indent=2))
env = {"name": "Прилавок — шаблон окружения", "values": [{"key": "baseUrl", "value": "", "type": "default", "enabled": True}, {"key": "token", "value": "", "type": "secret", "enabled": True}], "_postman_variable_scope": "environment"}
(ROOT / "postman/environment.template.json").write_text(json.dumps(env, ensure_ascii=False, indent=2))
print("OK:", sum(len(f["item"]) for f in coll["item"][1:]), "запросов")
