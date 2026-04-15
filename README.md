# 🛒 Django E-commerce Backend

Backend для интернет-магазина с каталогом товаров, корзиной и системой заказов.

Проект демонстрирует навыки разработки backend-приложений на Django и построения бизнес-логики e-commerce системы.

---

## ⚙️ Стек технологий

* Python
* Django
* Django ORM
* SQLite / PostgreSQL
* Fixtures

---

## 🔥 Основной функционал

* Каталог товаров
* Детальная страница товара
* Корзина
* Оформление заказа
* Личный кабинет
* История заказов
* Административная панель Django Admin

---

## 🧠 Что реализовано

* Работа с моделями и связями
* Каталог, корзина и заказы
* Базовая логика оплаты
* Фикстуры для тестовых данных
* Разделение проекта на приложения

---

## 🚀 Быстрый запуск

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py loaddata catalog_demo
python manage.py loaddata accounts_demo_users
python manage.py runserver
```

---

## 🔐 Демо-доступ

* admin / admin
* user / user

---

## 📌 О проекте

Учебный проект backend интернет-магазина, реализующий основные принципы построения e-commerce систем.
