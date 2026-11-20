import os

from src.api_client import APIClient
from src.db_manager import DBManager


def main() -> None:
    """Основная логика: сбор данных из API и загрузка их в БД."""
    # Список стран для мониторинга (минимум 4 по заданию)
    countries_to_monitor = [
        "Germany",
        "France",
        "United Kingdom",
        "Spain",
        "Italy",
        "Poland",
        "Netherlands",
        "Belgium",
        "Switzerland",
        "Austria",
        "Portugal",
        "Sweden",
    ]

    api_client = APIClient()

    db_manager = DBManager(
        dbname=os.getenv("DB_NAME", "coursework_db"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "postgres"),
        host=os.getenv("DB_HOST", "localhost"),
    )

    try:
        print("Создание таблиц...")
        db_manager.create_tables()

        print("Получение данных о странах...")
        countries_data = []
        for country_name in countries_to_monitor:
            try:
                bounds = api_client.get_country_bounds(country_name)
                countries_data.append({"name": country_name, "bounds": bounds})
                print(f"Границы для {country_name} получены.")
            except Exception as e:
                print(f"Ошибка при получении границ для {country_name}: {e}")

        if countries_data:
            db_manager.insert_countries(countries_data)
            print("Данные о странах сохранены в БД.")

        db_manager.clear_aeroplanes()
        print("Получение данных о самолетах...")
        for country in countries_data:
            name = country["name"]
            bounds = country["bounds"]

            try:
                country_id = db_manager.get_country_id_by_name(name)
                if not country_id:
                    print(f"ID для страны {name} не найден в БД. Пропуск.")
                    continue

                aircraft_data = api_client.get_aircraft_in_bounds(
                    lat_min=bounds["lat_min"],
                    lon_min=bounds["lon_min"],
                    lat_max=bounds["lat_max"],
                    lon_max=bounds["lon_max"],
                )

                if aircraft_data:
                    count = len(aircraft_data)
                    print(f"Найдено {count} самолетов над {name}. Сохранение...")
                    db_manager.insert_aeroplanes(aircraft_data, country_id)
                else:
                    print(f"Самолеты над {name} не найдены или API недоступен.")

            except Exception as e:
                print(f"Ошибка при обработке данных для {name}: {e}")

        print("Работа завершена.")

    except Exception as e:
        print(f"Критическая ошибка: {e}")
    finally:
        db_manager.close()


if __name__ == "__main__":
    main()
