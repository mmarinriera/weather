import json
import logging
import sys
from typing import Any

import click
from dotenv import dotenv_values

from weather import console
from weather import get_resource
from weather import get_version
from weather.weather_api import OpenWeatherCurrent
from weather.weather_api import OpenWeatherForecast
from weather.weather_api import query_current_weather
from weather.weather_api import query_weather_forecast

logger = logging.getLogger(__name__)


def _load_api_key() -> str:
    env: dict[str, str | None] = dotenv_values(".env")
    api_key = env.get("OPENWEATHER_API_KEY")
    if api_key is None:
        logger.critical("API key not found")
        sys.exit(1)
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


def print_version(ctx: click.Context, _: Any, value: Any) -> None:
    """Click print version."""
    if not value or ctx.resilient_parsing:
        return
    click.echo(get_version())
    ctx.exit()


@click.group(context_settings=dict(help_option_names=["-h", "--help"]))
@click.option(
    "-v",
    "--version",
    is_flag=True,
    help="Print version and exit.",
    callback=print_version,
    expose_value=False,
    is_eager=True,
)
@click.option(
    "-d",
    "--debug",
    "debug_mode",
    is_flag=True,
    help="Enable debug mode.",
)
@click.option("--dev", "dev_mode", is_flag=True, help="Bypass API call and use test data.")
@click.pass_context
def weather(ctx: click.Context, debug_mode: bool, dev_mode: bool) -> None:
    """Weather forecast app"""
    ctx.ensure_object(dict)

    if debug_mode:
        logger.setLevel(level=logging.DEBUG)

    ctx.obj["debug"] = debug_mode
    ctx.obj["dev_mode"] = dev_mode

    if not dev_mode:
        ctx.obj["api_key"] = _load_api_key()


@weather.command
@click.argument("city", type=str)
@click.argument("country", type=str)
@click.pass_context
def now(ctx: click.Context, city: str, country: str) -> None:
    """
    Show current weather for CITY, COUNTRY for the following DAYS.
    """
    if ctx.obj["dev_mode"]:
        data = _get_test_data_current()
        console.render_current("This is a test", "DEV", data)
        return

    data = query_current_weather(city, country, api_key=ctx.obj["api_key"])
    console.render_current(city, country, data)


@weather.command
@click.argument("city", type=str)
@click.argument("country", type=str)
@click.argument("days", type=int)
@click.pass_context
def forecast(ctx: click.Context, city: str, country: str, days: int) -> None:
    """
    Show daily weather forecast in 3h intervals for CITY, COUNTRY for the following DAYS.
    """
    if ctx.obj["dev_mode"]:
        data = _get_test_data_forecast()
        console.render_forecast("This is a test", "DEV", data)
        return

    api_key = _load_api_key()

    data = query_weather_forecast(city, country, days=days, api_key=api_key)
    console.render_forecast(city, country, data)
