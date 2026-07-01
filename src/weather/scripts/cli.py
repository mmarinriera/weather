import json
import logging
import sys
from datetime import datetime
from typing import Any

import click
from dotenv import dotenv_values
from rich.columns import Columns
from rich.console import Console
from rich.padding import Padding
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from weather import get_resource
from weather import get_version
from weather.weather_api import ForecastEntry
from weather.weather_api import OpenWeatherCurrent
from weather.weather_api import OpenWeatherForecast
from weather.weather_api import query_current_weather
from weather.weather_api import query_weather_forecast

DATE_OUT_FMT_DAILY = "%a %d %b %H:%M"
logger = logging.getLogger(__name__)
console = Console()
COLOR_PALETTE = [
    "deep_sky_blue2",
    "medium_purple1",
    "yellow",
    "orange_red1",
    "dark_cyan",
    "deep_pink3",
    "wheat1",
    "thistle1",
    "aquamarine1",
]


def _load_api_key() -> str:
    env: dict[str, str] = dotenv_values(".env")
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


def _render_entry(entry: OpenWeatherCurrent | ForecastEntry) -> Table:
    PAD = (1, 0)
    grid = Table.grid(expand=True)
    grid.add_column()
    grid.add_column()
    grid.add_column()
    grid.add_column()

    date_str = datetime.fromtimestamp(entry.dt).strftime(DATE_OUT_FMT_DAILY)
    date = Text(date_str, style=f"bold {COLOR_PALETTE[2]}")
    temp = Text(f"{entry.main.temp:.1f}º", style=COLOR_PALETTE[3])
    feeling = Text(f"{entry.main.feels_like:.1f}º", style=COLOR_PALETTE[3])
    weather_main = Text(f"{entry.weather[0].main}", style=f"bold {COLOR_PALETTE[5]}")
    description = Text(f"{entry.weather[0].description}", style=f"bold {COLOR_PALETTE[5]}")
    grid.add_row(Padding(date, PAD))
    grid.add_row(Padding(weather_main, PAD), Padding(description, PAD))
    grid.add_row("Temperature", temp, "Feels like", feeling)

    vol = Text(f"{100 * entry.rain.volume:.2f}mm", style=COLOR_PALETTE[0])

    if isinstance(entry, OpenWeatherCurrent):
        grid.add_row("Precipitation", vol)
    else:
        pop = Text(f"{100 * entry.pop:.2f}%", style=COLOR_PALETTE[0])
        grid.add_row("Precipitation", pop, vol)

    return grid


def _render_current(city: str, country: str, data: OpenWeatherCurrent) -> None:
    console.rule()
    console.print(Padding(f"[bold]Current Weather in {city}, {country}", pad=(1, 1)))
    console.rule()
    console.print(Panel(_render_entry(data), width=64))


def _render_forecast(city: str, country: str, data: OpenWeatherForecast) -> None:
    console.rule()
    console.print(Padding(f"[bold]Weather forecast for {city}, {country}", pad=(1, 1)))
    console.rule()
    console.print(Columns([Panel(_render_entry(entry), width=64) for entry in data.forecast]))


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
@click.pass_context
def weather(ctx: click.Context, debug_mode: bool) -> None:
    """Weather forecast app"""
    ctx.ensure_object(dict)

    if debug_mode:
        logger.setLevel(level=logging.DEBUG)

    ctx.obj["debug"] = debug_mode


@weather.command
@click.argument("city", type=str)
@click.argument("country", type=str)
@click.option("--dev", "dev_mode", is_flag=True, help="Bypass API call and use test data.")
def now(city: str, country: str, dev_mode: bool) -> None:
    """
    Show current weather for CITY, COUNTRY for the following DAYS.
    """
    if dev_mode:
        data = _get_test_data_current()
        _render_current("This is a test", "DEV", data)
        return

    api_key = _load_api_key()

    data = query_current_weather(city, country, api_key=api_key)

    _render_current(city, country, data)


@weather.command
@click.argument("city", type=str)
@click.argument("country", type=str)
@click.argument("days", type=int)
@click.option("--dev", "dev_mode", is_flag=True, help="Bypass API call and use test data.")
def forecast(city: str, country: str, days: int, dev_mode: bool) -> None:
    """
    Show daily weather forecast in 3h intervals for CITY, COUNTRY for the following DAYS.
    """
    if dev_mode:
        data = _get_test_data_forecast()
        _render_forecast("This is a test", "DEV", data)
        return

    api_key = _load_api_key()

    data = query_weather_forecast(city, country, days=days, api_key=api_key)

    _render_forecast(city, country, data)
