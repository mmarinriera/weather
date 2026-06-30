import json
import logging
from datetime import datetime
from typing import Any

import click
from rich.console import Console
from rich.table import Table
from rich.text import Text

from waf import get_resource
from waf import get_version

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

def _to_celsius(temp:float)->float:
    return temp -273.15

def _get_weather_data() -> dict[str, Any]:
    test_file = get_resource("example_3h_5d_forecast.json")
    with open(test_file) as f:
        data = json.load(f)
    return data


def _pretty_print_daily_forecast(location: str, data: dict[str, Any]) -> None:

    table = Table(title=f"Daily forecast for {location}", title_justify="left")
    table.add_column("Date", justify="right")
    table.add_column("Temp.", justify="right")
    table.add_column("Feels like", justify="right")
    table.add_column("Precipitation (%)", justify="right")
    table.add_column("Weather", justify="right")

    for entry in data["list"]:
        date_str = datetime.fromtimestamp(int(entry["dt"])).strftime(DATE_OUT_FMT_DAILY)
        date = Text(date_str, style=COLOR_PALETTE[2])
        temp = Text(f"{_to_celsius(entry["main"]["temp"]):.2f}", style=COLOR_PALETTE[3])
        feeling = Text(f"{_to_celsius(entry["main"]["feels_like"]):.2f}", style=COLOR_PALETTE[3])
        pop = Text(f"{100*entry['pop']:.2f}%", style=COLOR_PALETTE[0])
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
@click.argument("location", type=str)
@click.argument("days", type=int)
def forecast(location: str, days: int) -> None:
    """
    Show daily weather forecast for LOCATION for the current day and DAYS following days.
    """
    data = _get_weather_data()

    _pretty_print_daily_forecast(location, data)
