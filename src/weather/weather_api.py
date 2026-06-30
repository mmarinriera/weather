import logging
from typing import Any

import requests

URL_FORECAST = "http://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&cnt={cnt}&appid={api_key}"
URL_GEO = "http://api.openweathermap.org/geo/1.0/direct?q={city_name},{country_code}&limit={limit}&appid={api_key}"
logger = logging.getLogger(__name__)


def _get_location_coordinates(city_name: str, country_code: str, api_key: str) -> tuple[float, float]:
    res = requests.get(url=URL_GEO.format(city_name=city_name, country_code=country_code, limit=1, api_key=api_key))
    data = res.json()
    lat = data[0]["lat"]
    lon = data[0]["lon"]
    logger.debug(f"{city_name},{country_code}: lat = {lat}, long = {lon}")

    return lat, lon


def query_weather_forecast(city: str, country: str, days: int, api_key: str) -> dict[str, Any]:
    cnt = days * 8
    lat, lon = _get_location_coordinates(city, country, api_key=api_key)
    res = requests.get(url=URL_FORECAST.format(lat=lat, lon=lon, cnt=cnt, api_key=api_key))
    data = res.json()
    return data
