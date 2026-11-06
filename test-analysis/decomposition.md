# Декомпозиция

```mermaid
mindmap
  root((API Прилавок))
    Наборы
      POST kits — создать
      DELETE kits — удалить
      POST kits/id/products
        productsList
        id продукта
        quantity
        лимит 30 продуктов
    Доставка Привезём быстро
      XML InputModel
        productsCount
        productsWeight
        deliveryTime
      рабочее время 07–21
      цена и срок
    Корзина
      GET orders/id — список
      PUT orders/id — добавить
      DELETE orders/id — удалить
      авторизация Bearer
    Общее
      коды 200, 400, 401, 404, 405, 409, 500
      формат ошибки code и message
      Content-Type
```

## Что проверяется в каждом запросе
1. **Метод и путь:** допустимый метод, существующий путь, наличие идентификатора.
2. **Заголовки:** Content-Type, Authorization.
3. **Тело:** формат (JSON или XML), обязательные поля, типы, диапазоны.
4. **Ответ:** код, тело, формат ошибки, отсутствие технических деталей.
5. **Состояние:** изменение данных (набор, корзина) корректно записано.
