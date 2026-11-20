# Coursework 3: Search DB

Курсовой проект по интеграции OpenSky Network API и PostgreSQL для мониторинга воздушных судов над выбранными странами.

## Установка

1. Установите зависимости через Poetry:
   poetry install
2. Создайте базу данных coursework_db в PostgreSQL (через pgAdmin или psql).
3. Задайте пароль пользователя postgres в переменной окружения или передавайте при запуске.
Запуск
$env:DB_PASSWORD="ваш_пароль"; poetry run python main.py

Структура проекта
src/api_client.py — клиент для запросов к Nominatim и OpenSky API.
src/db_manager.py — менеджер базы данных PostgreSQL.
main.py — точка входа, оркестрация сбора и сохранения данных.

Автор
Maxim Obroskov

Лицензия
MIT License