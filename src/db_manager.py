from typing import Dict, List, Optional, Tuple

import psycopg2
from psycopg2.extras import execute_values


class DBManager:
    """Менеджер для работы с базой данных PostgreSQL."""

    def __init__(
        self,
        dbname: str,
        user: str,
        password: str,
        host: str = "localhost",
        port: int = 5432,
    ) -> None:
        """
        Инициализация параметров подключения к БД.

        :param dbname: Имя базы данных.
        :param user: Имя пользователя.
        :param password: Пароль.
        :param host: Хост.
        :param port: Порт.
        """
        self.conn_params: Dict[str, object] = {
            "dbname": dbname,
            "user": user,
            "password": password,
            "host": host,
            "port": port,
        }
        self.connection: Optional[psycopg2.extensions.connection] = None

    def connect(self) -> None:
        """Устанавливает соединение с БД, если оно ещё не открыто."""
        if self.connection is None or self.connection.closed:
            self.connection = psycopg2.connect(**self.conn_params)
            self.connection.autocommit = True

    def close(self) -> None:
        """Закрывает соединение с БД."""
        if self.connection is not None and not self.connection.closed:
            self.connection.close()

    def create_tables(self) -> None:
        """Создает таблицы countries и aeroplanes, если их нет."""
        self.connect()
        with self.connection.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS countries (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(100) UNIQUE NOT NULL,
                    lat_min FLOAT,
                    lat_max FLOAT,
                    lon_min FLOAT,
                    lon_max FLOAT
                );
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS aeroplanes (
                    icao24 VARCHAR(10) NOT NULL,
                    callsign VARCHAR(20),
                    origin_country VARCHAR(100),
                    time_position BIGINT,
                    last_contact BIGINT,
                    longitude FLOAT,
                    latitude FLOAT,
                    baro_altitude FLOAT,
                    on_ground BOOLEAN,
                    velocity FLOAT,
                    true_track FLOAT,
                    vertical_rate FLOAT,
                    sensors INTEGER[],
                    geo_altitude FLOAT,
                    squawk VARCHAR(10),
                    spi BOOLEAN,
                    position_source INTEGER,
                    country_id INTEGER REFERENCES countries(id)
                );
            """)

    def clear_aeroplanes(self) -> None:
        """Удаляет все записи из таблицы aeroplanes (для чистой перезаливки)."""
        self.connect()
        with self.connection.cursor() as cur:
            cur.execute("DELETE FROM aeroplanes;")

    def insert_countries(self, countries_data: List[dict]) -> None:
        """
        Вставляет данные о странах в таблицу countries.

        :param countries_data: Список словарей с данными стран.
        """
        self.connect()
        with self.connection.cursor() as cur:
            for country in countries_data:
                cur.execute(
                    """
                    INSERT INTO countries (name, lat_min, lat_max, lon_min, lon_max)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (name) DO NOTHING;
                    """,
                    (
                        country["name"],
                        country["bounds"]["lat_min"],
                        country["bounds"]["lat_max"],
                        country["bounds"]["lon_min"],
                        country["bounds"]["lon_max"],
                    ),
                )

    def insert_aeroplanes(self, aeroplanes_data: List[list], country_id: int) -> None:
        """
        Вставляет данные о самолетах в таблицу aeroplanes.

        :param aeroplanes_data: Список списков с данными самолетов из OpenSky.
        :param country_id: ID страны наблюдения.
        """
        self.connect()
        values = [tuple(plane[:17]) + (country_id,) for plane in aeroplanes_data]
        if values:
            with self.connection.cursor() as cur:
                execute_values(
                    cur,
                    """
                    INSERT INTO aeroplanes (
                        icao24, callsign, origin_country, time_position, last_contact,
                        longitude, latitude, baro_altitude, on_ground, velocity,
                        true_track, vertical_rate, sensors, geo_altitude, squawk,
                        spi, position_source, country_id
                    ) VALUES %s
                    """,
                    values,
                )

    def get_country_id_by_name(self, country_name: str) -> Optional[int]:
        """
        Получает ID страны по её названию.

        :param country_name: Название страны.
        :return: ID страны или None, если страна не найдена.
        """
        self.connect()
        with self.connection.cursor() as cur:
            cur.execute("SELECT id FROM countries WHERE name = %s;", (country_name,))
            result = cur.fetchone()
            return result[0] if result else None

    def get_countries_and_aeroplanes_count(self) -> List[Tuple[str, int]]:
        """Получает список стран и количество самолетов в их воздушном пространстве."""
        self.connect()
        with self.connection.cursor() as cur:
            cur.execute("""
                SELECT c.name, COUNT(a.icao24)
                FROM countries c
                LEFT JOIN aeroplanes a ON c.id = a.country_id
                GROUP BY c.name
                ORDER BY COUNT(a.icao24) DESC;
            """)
            return cur.fetchall()

    def get_all_aeroplanes(self) -> List[Tuple]:
        """Получает список всех воздушных судов."""
        self.connect()
        with self.connection.cursor() as cur:
            cur.execute("SELECT * FROM aeroplanes;")
            return cur.fetchall()

    def get_avg_speed(self) -> float:
        """Получает среднюю скорость по всем самолетам (0.0, если данных нет)."""
        self.connect()
        with self.connection.cursor() as cur:
            cur.execute("""
                SELECT AVG(velocity) FROM aeroplanes WHERE velocity IS NOT NULL;
            """)
            result = cur.fetchone()
            return float(result[0]) if result and result[0] is not None else 0.0

    def get_aeroplanes_with_higher_speed(self) -> List[Tuple]:
        """Получает список самолетов со скоростью выше средней."""
        self.connect()
        with self.connection.cursor() as cur:
            cur.execute("""
                SELECT * FROM aeroplanes
                WHERE velocity > (
                    SELECT AVG(velocity) FROM aeroplanes WHERE velocity IS NOT NULL
                )
                AND velocity IS NOT NULL;
            """)
            return cur.fetchall()

    def get_aeroplanes_with_keyword(self, keyword: str) -> List[Tuple]:
        """
        Получает список самолетов, в позывном которых есть переданные символы.

        :param keyword: Ключевое слово для поиска в callsign.
        """
        self.connect()
        with self.connection.cursor() as cur:
            cur.execute(
                """
                SELECT * FROM aeroplanes
                WHERE callsign LIKE %s;
                """,
                (f"%{keyword}%",),
            )
            return cur.fetchall()
