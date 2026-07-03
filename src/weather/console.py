import itertools
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

DATE_OUT_FMT = "%a %d %b"
TIME_OUT_FMT = "%H:%M"
ENTRY_PANEL_WIDTH = 48
WEATHER_EMOJIS = {
    "Thunderstorm": "🌩️",
    "Drizzle": "🌧️",
    "Rain": "🌧️",
    "Snow": "🌨️",
    "Clear": "☀️",
    "Clouds": "☁️",
    "801": "⛅️",
}

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
    PAD = (0, 0, 1, 0)
    grid = Table.grid(expand=True)
    grid.add_column()
    grid.add_column()

    date_str = datetime.fromtimestamp(entry.dt).strftime(TIME_OUT_FMT)
    date = Text(date_str, style=f"bold {COLOR_PALETTE[2]}")
    weather_emoji = WEATHER_EMOJIS.get(entry.weather[0].main, "")
    description = Text(f"{weather_emoji} {entry.weather[0].description}", style=f"bold {COLOR_PALETTE[5]}")
    grid.add_row(Padding(date, PAD), Padding(description, PAD))

    temp = Text(f"{entry.main.temp:.1f}º", style=COLOR_PALETTE[3])
    feeling = Text(f"{entry.main.feels_like:.1f}º", style=COLOR_PALETTE[3])
    grid.add_row("Temperature", temp)
    grid.add_row("Feels like", feeling)

    if isinstance(entry, ForecastEntry):
        pop = Text(f"{100 * entry.pop:.2f}%", style=COLOR_PALETTE[0])
        grid.add_row("Precipitation", pop)

    rain_vol = Text(f"{100 * entry.rain.volume:.2f}mm", style=COLOR_PALETTE[0])
    snow_vol = Text(f"{100 * entry.snow.volume:.2f}mm", style=COLOR_PALETTE[0])

    if entry.rain.volume > 0.0:
        grid.add_row("🌧️ Rain", rain_vol)
    if entry.snow.volume > 0.0:
        grid.add_row("🌨️ Snow", snow_vol)

    return grid


def _group_entries_by_day(data: OpenWeatherForecast) -> None:
    # Forecast entries are already sorted by date
    for date, group in itertools.groupby(data.forecast, key=lambda d: datetime.fromtimestamp(d.dt).date()):
        console.rule(title=f"[bold] {date.strftime(DATE_OUT_FMT)}", align="left")
        console.print(
            Padding(
                Columns([Panel(_render_entry(entry), width=ENTRY_PANEL_WIDTH) for entry in group]),
                pad=(1, 0, 1, 0),
            ),
        )


def render_current(city: str, country: str, data: OpenWeatherCurrent) -> None:
    date = datetime.fromtimestamp(data.dt).strftime(DATE_OUT_FMT)
    title = f"[bold]Current Weather in {city}, {country}, {date}"
    console.print(Padding(Panel(title), pad=(1, 0, 1, 0)))
    console.print(Panel(_render_entry(data), width=64))


def render_forecast(city: str, country: str, data: OpenWeatherForecast) -> None:
    title = f"[bold]Weather forecast for {city}, {country}"
    console.print(Padding(Panel(title), pad=(1, 0, 1, 0)))
    _group_entries_by_day(data)
