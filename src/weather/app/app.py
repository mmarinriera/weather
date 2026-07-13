import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from weather.weather_api import ForecastEntry
from weather.weather_api import query_current_weather
from weather.weather_api import query_weather_forecast

logger = logging.getLogger(__name__)

MAX_HOURS = 5 * 24

DATE_OUT_FMT = "%a %d %b"
TIME_OUT_FMT = "%H:%Mh"

ABS_PATH = Path(__file__)

app = FastAPI()
app.mount("/static", StaticFiles(directory=ABS_PATH.with_name("static")), name="static")
templates = Jinja2Templates(directory=ABS_PATH.with_name("templates"))


def _load_api_key() -> str:
    load_dotenv(".env")
    api_key = os.getenv("OPENWEATHER_API_KEY")
    if api_key is None:
        logger.critical("API key not found")
        raise ValueError
    return api_key


@app.get("/weather", response_class=HTMLResponse)
async def current(request: Request, city: str, country: str) -> HTMLResponse:
    api_key = _load_api_key()
    current_weather = query_current_weather(city, country, api_key=api_key)
    forecast = query_weather_forecast(city=city, country=country, hours=MAX_HOURS, api_key=api_key)

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
