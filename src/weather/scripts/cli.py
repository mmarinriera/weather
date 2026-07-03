import json
import logging
from typing import Annotated

import typer
from dotenv import dotenv_values

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


def _load_api_key() -> str:
    env: dict[str, str | None] = dotenv_values(".env")
    api_key = env.get("OPENWEATHER_API_KEY")
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
def now(ctx: typer.Context, city: str, country: str) -> None:
    """
    Show current weather for CITY, COUNTRY.
    """
    if ctx.obj["dev_mode"]:
        data = _get_test_data_current()
        console.render_current("This is a test", "DEV", data)
        return

    data = query_current_weather(city, country, api_key=ctx.obj["api_key"])
    console.render_current(city, country, data)


@weather.command()
def forecast(
    ctx: typer.Context,
    city: str,
    country: str,
    hours: Annotated[int, typer.Argument()] = 24,
    days: Annotated[int | None, typer.Option("--days", "-d", help="Forecast range in days.")] = None,
) -> None:
    """
    Show daily weather forecast in 3h intervals for CITY, COUNTRY for the following HOURS.

    Use option --days DAYS to define the forecast range in days. Supersedes hours.
    """
    if ctx.obj["dev_mode"]:
        data = _get_test_data_forecast()
        console.render_forecast("This is a test", "DEV", data)
        return

    if days is None and hours / 24 > MAX_DAYS_FORECAST:
        logger.warning(
            f"Maximum forecast is {MAX_DAYS_FORECAST} days. Capping query to {MAX_DAYS_FORECAST} days ({MAX_DAYS_FORECAST * 24}h)."
        )
        hours = MAX_DAYS_FORECAST * 24

    if days is not None and days > MAX_DAYS_FORECAST:
        logger.warning(f"Maximum forecast is {MAX_DAYS_FORECAST} days. Capping query to {MAX_DAYS_FORECAST} days.")
        days = MAX_DAYS_FORECAST

    hours = days * 24 if days is not None else hours

    data = query_weather_forecast(city, country, hours=hours, api_key=ctx.obj["api_key"])
    console.render_forecast(city, country, data)
