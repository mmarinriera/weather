import json
import logging
from datetime import datetime
import sys
from typing import Any

import click
from dotenv import dotenv_values
from rich.console import Console
from rich.table import Table
from rich.text import Text

from weather import get_resource
from weather import get_version
from weather.weather_api import query_weather_forecast

DATE_OUT_FMT_DAILY = "%a %d %b %H:%M"
logger = logging.getLogger(__name__)
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


def _to_celsius(temp: float) -> float:
    return temp - 273.15


def _load_api_key() -> str:
    env:dict[str,str] = dotenv_values(".env")
    api_key = env.get("OPENWEATHER_API_KEY")
    if api_key is None:
        logger.critical("API key not found")
        sys.exit(1)
    return api_key


def _get_test_data() -> dict[str, Any]:
    test_file = get_resource("example_3h_5d_forecast.json")
    with open(test_file) as f:
        data = json.load(f)
    return data


def _pretty_print_daily_forecast(city: str, country: str, data: dict[str, Any]) -> None:

    table = Table(title=f"Daily forecast for {city}, {country}", title_justify="left")
    table.add_column("Date", justify="right")
    table.add_column("Temp.", justify="right")
    table.add_column("Feels like", justify="right")
    table.add_column("Precipitation (%)", justify="right")
    table.add_column("Weather", justify="right")

    for entry in data["list"]:
        date_str = datetime.fromtimestamp(int(entry["dt"])).strftime(DATE_OUT_FMT_DAILY)
        date = Text(date_str, style=COLOR_PALETTE[2])
        temp = Text(f"{_to_celsius(entry['main']['temp']):.2f}", style=COLOR_PALETTE[3])
        feeling = Text(f"{_to_celsius(entry['main']['feels_like']):.2f}", style=COLOR_PALETTE[3])
        pop = Text(f"{100 * entry['pop']:.2f}%", style=COLOR_PALETTE[0])
        description = Text(f"{entry['weather'][0]['main']}", style=COLOR_PALETTE[5])

        table.add_row(
            date,
            temp,
            feeling,
            pop,
            description,
        )

    console = Console()
    console.print(table)


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
@click.argument("days", type=int)
@click.option("--dev", "dev_mode", is_flag=True, help="Bypass API call and use test data.")
def forecast(city: str, country: str, days: int, dev_mode: bool) -> None:
    """
    Show daily weather forecast in 3h intervals for CITY, COUNTRY for the following DAYS.
    """
    if dev_mode:
        data = _get_test_data()
        _pretty_print_daily_forecast("This is a test", "DEV", data)
        return

    api_key = _load_api_key()

    data = query_weather_forecast(city, country, days=days, api_key=api_key)

    _pretty_print_daily_forecast(city, country, data)
