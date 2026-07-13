import logging
import sys
from datetime import datetime
from datetime import time

import requests
from pydantic import AliasChoices
from pydantic import BaseModel
from pydantic import Field

URL_CURRENT = "https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=metric"
URL_FORECAST = (
    "http://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&cnt={cnt}&appid={api_key}&units=metric"
)
URL_GEO = "http://api.openweathermap.org/geo/1.0/direct?q={city_name},{country_code}&limit={limit}&appid={api_key}"
logger = logging.getLogger(__name__)

DATE_OUT_FMT = "%a %d %b"
TIME_OUT_FMT = "%H:%Mh"


class LocationData(BaseModel):
    name: str
    country: str
    timezone: int
    sunrise: int
    sunset: int


class WeatherMainData(BaseModel):
    temp: float
    feels_like: float
    temp_min: float
    temp_max: float
    pressure: float = Field(alias="grnd_level")
    humidity: float


class WeatherDescription(BaseModel):
    id: int
    main: str
    description: str
    icon: str


class CloudsData(BaseModel):
    all: float


class WindData(BaseModel):
    speed: float
    deg: float
    gust: float


class RainData(BaseModel):
    volume: float = Field(alias=AliasChoices("3h", "1h"), default=0.0)


class SnowData(BaseModel):
    volume: float = Field(alias=AliasChoices("3h", "1h"), default=0.0)


class ForecastEntry(BaseModel):
    dt: int
    main: WeatherMainData
    weather: list[WeatherDescription]
    clouds: CloudsData
    wind: WindData
    rain: RainData = RainData()
    snow: SnowData = SnowData()
    pop: float

    @property
    def day(self) -> str:
        return datetime.fromtimestamp(self.dt).strftime(DATE_OUT_FMT)

    @property
    def time(self) -> str:
        return datetime.fromtimestamp(self.dt).strftime(TIME_OUT_FMT)


class OpenWeatherCurrent(BaseModel):
    dt: int
    main: WeatherMainData
    weather: list[WeatherDescription]
    clouds: CloudsData
    wind: WindData
    rain: RainData = RainData()
    snow: SnowData = SnowData()
    timezone: int

    @property
    def day(self) -> str:
        return datetime.fromtimestamp(self.dt).strftime(DATE_OUT_FMT)

    @property
    def time(self) -> str:
        return datetime.fromtimestamp(self.dt).strftime(TIME_OUT_FMT)


class OpenWeatherForecast(BaseModel):
    cnt: int
    forecast: list[ForecastEntry] = Field(alias="list")
    city: LocationData


def _check_api_status_code(res: requests.Response) -> None:
    if res.status_code == 200:
        return

    data = res.json()

    if res.status_code < 400:
        logger.warning(f"API response code {res.status_code}: '{data['message']}'.")
        return

    if res.status_code >= 400:
        logger.critical(f"API response code {res.status_code}: '{data['message']}'. Aborting.")
        sys.exit(1)


def _get_location_coordinates(city_name: str, country_code: str, api_key: str) -> tuple[float, float]:
    res = requests.get(url=URL_GEO.format(city_name=city_name, country_code=country_code, limit=1, api_key=api_key))
    _check_api_status_code(res)
    data = res.json()
    lat = data[0]["lat"]
    lon = data[0]["lon"]
    logger.debug(f"{city_name},{country_code}: lat = {lat}, long = {lon}")

    return lat, lon


def _next_timepoint(t: time) -> time:
    """OpenWeather API returns forecast at fixed 3h intervals, from 2h to 23h within the same day"""
    next_hour = (((t.hour - 2) // 3 + 1) * 3 + 2) % 24
    return time(next_hour)


def _get_n_time_points_from_hours(hours: int) -> int:
    """Compute the number of time points to query, considering the time leading to the next time point."""
    logger.debug(f"hours {hours}")
    current_time = datetime.now().time()
    next_forecast_timepoint = _next_timepoint(current_time)
    logger.debug(f"current hour {current_time}; next timepoint {next_forecast_timepoint}")
    n_time_points = (hours - (next_forecast_timepoint.hour - current_time.hour)) // 3 + 1
    logger.debug(f"n timepoints {n_time_points}.")
    return n_time_points


def query_current_weather(city: str, country: str, api_key: str) -> OpenWeatherCurrent:
    lat, lon = _get_location_coordinates(city, country, api_key=api_key)
    res = requests.get(url=URL_CURRENT.format(lat=lat, lon=lon, api_key=api_key))
    _check_api_status_code(res)
    data: OpenWeatherCurrent = OpenWeatherCurrent.model_validate(res.json())
    return data


def query_weather_forecast(city: str, country: str, hours: int, api_key: str) -> OpenWeatherForecast:
    n_time_points = _get_n_time_points_from_hours(hours)
    lat, lon = _get_location_coordinates(city, country, api_key=api_key)
    res = requests.get(url=URL_FORECAST.format(lat=lat, lon=lon, cnt=n_time_points, api_key=api_key))
    _check_api_status_code(res)

    data: OpenWeatherForecast = OpenWeatherForecast.model_validate(res.json())
    return data
