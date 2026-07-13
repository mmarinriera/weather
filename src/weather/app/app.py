import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict

from weather.weather_api import ForecastEntry
from weather.weather_api import query_current_weather
from weather.weather_api import query_weather_forecast

logger = logging.getLogger(__name__)

MAX_HOURS = 5 * 24

DATE_OUT_FMT = "%a %d %b"
TIME_OUT_FMT = "%H:%Mh"

ABS_PATH = Path(__file__)


class Settings(BaseSettings):
    OPENWEATHER_API_KEY: str
    WEATHER_LOCATION_CITY: str = "Munich"
    WEATHER_LOCATION_COUNTRY: str = "DE"
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
app = FastAPI()
app.mount("/static", StaticFiles(directory=ABS_PATH.with_name("static")), name="static")
templates = Jinja2Templates(directory=ABS_PATH.with_name("templates"))


@app.get("/weather", response_class=HTMLResponse)
async def current(
    request: Request, city: str = settings.WEATHER_LOCATION_CITY, country: str = settings.WEATHER_LOCATION_COUNTRY
) -> HTMLResponse:
    current_weather = query_current_weather(city, country, api_key=settings.OPENWEATHER_API_KEY)
    forecast = query_weather_forecast(city=city, country=country, hours=MAX_HOURS, api_key=settings.OPENWEATHER_API_KEY)

    grouped: dict[str, list[ForecastEntry]] = {}
    for time_point in forecast.forecast:
        if not grouped.get(time_point.day):
            grouped[time_point.day] = []
        grouped[time_point.day].append(time_point)

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"city": city, "current": current_weather, "forecast": grouped},
    )
