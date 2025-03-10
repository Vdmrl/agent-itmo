# ИТМО агентский бот API
API-сервис для ответов на вопросы об Университете ИТМО с использованием LLM (OpenAI) и поиском (tavily) по различным источникам.
Приложение написано на FastAPI, разворачивается при помощи docker-compose.

Победитель мегашколы ИТМО

Источники для поиска информации:
- itmo.ru
- abit.itmo.ru
- news.itmo.ru
- itmo.ru/ru/ratings/ratings.htm
- nanojournal.ifmo.ru/university_itmo
- wp.wiki-wiki.ru/wp

## Сборка
Для запуска выполните команду:

```bash
docker-compose up -d
```
Она соберёт Docker-образ, а затем запустит контейнер.

После успешного запуска контейнера приложение будет доступно на http://localhost:8008.

## Проверка работы
Отправьте POST-запрос на эндпоинт /api/request. Например, используйте curl:

```bash
curl --location --request POST 'http://localhost:8080/api/request' \
--header 'Content-Type: application/json' \
--data-raw '{
  "query": "В каком городе находится главный кампус Университета ИТМО?\n1. Москва\n2. Санкт-Петербург\n3. Екатеринбург\n4. Нижний Новгород",
  "id": 1
}'
```
В ответ вы получите JSON вида:

```json
{
  "id": 1,
  "answer": 1,
  "reasoning": "Из информации на сайте",
  "sources": [
    "https://itmo.ru/ru/",
    "https://abit.itmo.ru/"
  ]
}
```

id будет соответствовать тому, что вы отправили в запросе,
answer (в базовой версии) всегда будет 5.


Чтобы остановить сервис, выполните:

```bash
docker-compose down
```
