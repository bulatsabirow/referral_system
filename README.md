# Referral System FastAPI backend #

---

## Описание ##
Реферальная система позволяет привлекать новых клиентов с помощью рекомендаций уже 
существующих пользователей. 
Авторизованные пользователи могут создавать и удалять свои реферальные коды, 
ограничивая их срок действия. Новые пользователи могут регистрироваться, используя реферальный код.   
Кроме того, система позволяет получать реферальный код по email адресу реферера, 
а также получать информацию о рефералах по id реферера.  
Пути к документации:
- *OpenAPI* - `/docs/`
- *Redoc* - `/redoc/`

## Требования ##
1. [Python >= 3.10](https://www.python.org/downloads/)
2. [Poetry](https://pypi.org/project/poetry/)

## Запуск проекта ##
1. Вход в виртуальное окружение:
    `
    poetry shell 
    `
2. Установка зависимостей:
    `
    poetry install
    `
3. Поднятие PostgreSQL и Redis с помощью Docker:
    `
    docker-compose up -d
    `
4. Выполнение миграций:
    `
    alembic updrage head
    `
5. Инициализация линтера:
    `
    pre-commit install
    `
6. Запуск сервера для разработки на http://localhost:8000:
    `
    uvicorn main:app --reload
    `

## Обозначения символов в коммитах ##
- `+` - добавлено
- `-` - удалено
- `=` - изменено/улучшено
- `!` - исправлено