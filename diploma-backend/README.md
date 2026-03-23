# Megano Backend

## Быстрый запуск

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py loaddata catalog_demo
python manage.py loaddata accounts_demo_users
python manage.py runserver
```

## Демо-пользователи (fixtures)

Файл: `accounts/fixtures/accounts_demo_users.json`

- `admin` / `admin` — администратор (`is_staff=True`, `is_superuser=True`)
- `user` / `user` — обычный пользователь

## Проверка API тестами

```bash
python manage.py test accounts basket catalog orders payments
```

