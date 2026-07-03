import json
import logging
import os
from datetime import datetime
from datetime import timedelta
from enum import Enum
from typing import Annotated

import typer
from dotenv import load_dotenv

from weather import console
from weather import get_resource
from weather import get_version
from weather.weather_api import OpenWeatherCurrent
from weather.weather_api import OpenWeatherForecast
from weather.weather_api import query_current_weather
from weather.weather_api import query_weather_forecast

MAX_DAYS_FORECAST = 5

weather = typer.Typer()

logger = logging.getLogger(__name__)


class ForecastPeriod(str, Enum):
    today = "today"
    tomorrow = "tomorrow"


def _load_api_key() -> str:
    load_dotenv(".env")
    api_key = os.getenv("OPENWEATHER_API_KEY")
    if api_key is None:
        logger.critical("API key not found")
        raise typer.Exit(1)
    return api_key


def _get_test_data_current() -> OpenWeatherCurrent:
    test_file = get_resource("example_current_weather.json")
    with open(test_file) as f:
        data: OpenWeatherCurrent = OpenWeatherCurrent.model_validate(json.load(f))
    return data


def _get_test_data_forecast() -> OpenWeatherForecast:
    test_file = get_resource("example_3h_5d_forecast.json")
    with open(test_file) as f:
        data: OpenWeatherForecast = OpenWeatherForecast.model_validate(json.load(f))
    return data


def _hours_until_end_of_today() -> float:
    current_time = datetime.now()
    time_delta = (
        datetime.combine(current_time.date() + timedelta(days=1), datetime.strptime("0000", "%H%M").time())
        - current_time
    )
    hours = time_delta.seconds / 3600
    return hours


def version_callback(value: bool) -> None:
    if value:
        print(get_version())
        raise typer.Exit()


@weather.callback()
def cli_callback(
    ctx: typer.Context,
    version: Annotated[
        bool, typer.Option("-v", "--version", callback=version_callback, is_eager=True, help="Show version and exit.")
    ] = False,
    debug_mode: Annotated[bool, typer.Option("-d", "--debug", help="Enable DEBUG logging.")] = False,
    dev_mode: Annotated[bool, typer.Option("--dev", help="Avoids using API and instead loads test data.")] = False,
) -> None:
    """Weather forecast app"""
    ctx.ensure_object(dict)

    if debug_mode:
        logger.setLevel(level=logging.DEBUG)

    ctx.obj["debug"] = debug_mode
    ctx.obj["dev_mode"] = dev_mode

    if not dev_mode:
        ctx.obj["api_key"] = _load_api_key()


@weather.command()
def now(
    ctx: typer.Context,
    city: str,
    country: str,
    pressure: Annotated[
        bool, typer.Option("--pressure", "-p", envvar="WEATHER_INCLUDE_PRESSURE", help="Include pressure.")
    ] = False,
    wind: Annotated[
        bool, typer.Option("--wind", "-w", envvar="WEATHER_INCLUDE_WIND", help="Include wind speed.")
    ] = False,
    humidity: Annotated[
        bool, typer.Option("--humidity", "-m", envvar="WEATHER_INCLUDE_HUMIDITY", help="Include humidity.")
    ] = False,
) -> None:
    """
    Show current weather for CITY, COUNTRY.
    """
    if ctx.obj["dev_mode"]:
        data = _get_test_data_current()
        console.render_current(
            "This is a test", "DEV", data, include_pressure=pressure, include_wind=wind, include_humidity=humidity
        )
        return

    data = query_current_weather(city, country, api_key=ctx.obj["api_key"])
    console.render_current(city, country, data, include_pressure=pressure, include_wind=wind, include_humidity=humidity)


@weather.command()
def forecast(
    ctx: typer.Context,
    city: str,
    country: str,
    period: Annotated[ForecastPeriod, typer.Argument(envvar="WEATHER_FORECAST_PERIOD")] = ForecastPeriod.today,
    days: Annotated[int | None, typer.Option("--days", "-d", help="Forecast period in days.")] = None,
    hours: Annotated[int | None, typer.Option("--hours", "-h", help="Forecast period in hours.")] = None,
    pressure: Annotated[
        bool, typer.Option("--pressure", "-p", envvar="WEATHER_INCLUDE_PRESSURE", help="Include pressure.")
    ] = False,
    wind: Annotated[
        bool, typer.Option("--wind", "-w", envvar="WEATHER_INCLUDE_WIND", help="Include wind speed.")
    ] = False,
    humidity: Annotated[
        bool, typer.Option("--humidity", "-m", envvar="WEATHER_INCLUDE_HUMIDITY", help="Include humidity.")
    ] = False,
) -> None:
    """
    Show daily weather forecast in 3h intervals for CITY, COUNTRY for the specified PERIOD from now.

    PERIOD can take either "today" or "tomorrow", setting the forecast period until the end of today or tomorrow, respectively.

    Alternatively, using the --days and/or --hours option can be used to precisely define the forecast period, superseding the PERIOD argument, if passed.

    If both --days and --hours values are passed, they will be added to define the forecast period.
    """
    if ctx.obj["dev_mode"]:
        data = _get_test_data_forecast()
        console.render_forecast(
            "This is a test", "DEV", data, include_pressure=pressure, include_wind=wind, include_humidity=humidity
        )
        return

    if days is not None or hours is not None:
        hours = hours if hours is not None else 0
        hours += days * 24 if days is not None else 0
    else:
        h_until_end_of_day = int(_hours_until_end_of_today())
        hours = h_until_end_of_day if period == ForecastPeriod.today else h_until_end_of_day + 24

    if hours / 24 > MAX_DAYS_FORECAST:
        logger.warning(
            f"Maximum forecast is {MAX_DAYS_FORECAST} days. Capping query to {MAX_DAYS_FORECAST} days ({MAX_DAYS_FORECAST * 24}h)."
        )
        hours = MAX_DAYS_FORECAST * 24

    data = query_weather_forecast(city, country, hours=hours, api_key=ctx.obj["api_key"])
    console.render_forecast(
        city, country, data, include_pressure=pressure, include_wind=wind, include_humidity=humidity
    )
