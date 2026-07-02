import logging
from datetime import datetime

from rich.columns import Columns
from rich.console import Console
from rich.padding import Padding
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from weather.weather_api import ForecastEntry
from weather.weather_api import OpenWeatherCurrent
from weather.weather_api import OpenWeatherForecast

console = Console()

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


def render_current(city: str, country: str, data: OpenWeatherCurrent) -> None:
    title = f"[bold]Current Weather in {city}, {country}"
    console.rule(title=title)
    console.print(Panel(_render_entry(data), width=64))


def render_forecast(city: str, country: str, data: OpenWeatherForecast) -> None:
    title = f"[bold]Weather forecast for {city}, {country}"
    console.rule(title=title)
    console.print(Columns([Panel(_render_entry(entry), width=64) for entry in data.forecast]))
