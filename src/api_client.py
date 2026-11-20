import time
from typing import Any, Dict, List

import requests


class APIClient:
    """Клиент для взаимодействия с внешними API (OpenSky и Nominatim)."""

    def __init__(self) -> None:
        """Создает HTTP-сессию с корректным User-Agent."""
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": (
                    "MaksimObroskov-Coursework3/1.0 "
                    "(maksim.obroskov@student.ru)"
                ),
                "Accept-Language": "en",
            }
        )

    def get_country_bounds(self, country_name: str) -> Dict[str, float]:
        """
        Получает границы страны (bounding box) через Nominatim API.

        :param country_name: Название страны на английском языке.
        :return: Словарь с ключами 'lat_min', 'lat_max', 'lon_min', 'lon_max'.
        """
        url = "https://nominatim.openstreetmap.org/search"
        params = {"q": country_name, "format": "json", "limit": 1, "addressdetails": 1}
        # Пауза 1 сек между запросами — требование политики Nominatim
        time.sleep(1)
        response = self.session.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()

        if not data:
            raise ValueError(f"Страна '{country_name}' не найдена.")

        # Nominatim возвращает boundingbox: [min_lat, max_lat, min_lon, max_lon]
        bbox = data[0].get("boundingbox")
        if not bbox:
            raise ValueError(f"Не удалось получить границы для страны '{country_name}'.")

        return {
            "lat_min": float(bbox[0]),
            "lat_max": float(bbox[1]),
            "lon_min": float(bbox[2]),
            "lon_max": float(bbox[3]),
        }

    def get_aircraft_in_bounds(
        self, lat_min: float, lon_min: float, lat_max: float, lon_max: float
    ) -> List[List[Any]]:
        """
        Получает список самолетов в заданных границах через OpenSky API.

        :param lat_min: Минимальная широта.
        :param lon_min: Минимальная долгота.
        :param lat_max: Максимальная широта.
        :param lon_max: Максимальная долгота.
        :return: Список списков с данными о самолетах (states).
        """
        url = "https://opensky-network.org/api/states/all"
        params = {
            "lamin": lat_min,
            "lamax": lat_max,
            "lomin": lon_min,
            "lomax": lon_max,
        }
        response = self.session.get(url, params=params, timeout=60)
        response.raise_for_status()
        data = response.json()

        # OpenSky возвращает {'time': ..., 'states': [[...], [...]]}
        if not data or not data.get("states"):
            return []

        return data["states"]
