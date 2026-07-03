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
logger = logging.getLogger(__name__)

DATE_OUT_FMT = "%a %d %b"
TIME_OUT_FMT = "%H:%Mh"
ENTRY_PANEL_WIDTH = 32
WEATHER_EMOJIS = {
    "Thunderstorm": "🌩️",
    "Drizzle": "🌧️",
    "Rain": "🌧️",
    "Snow": "🌨️",
    "Clear": "☀️",
    "Clouds": "☁️",
    "801": "⛅️",
}

WEATHER_COLORS = {
    "Thunderstorm": "#0091ff",
    "Drizzle": "#4890fe",
    "Rain": "#006eff",
    "Snow": "#16efff",
    "Clear": "#ffb915",
    "Clouds": "#b6b6b6",
}

TEMP_COLORS = {
    0: "#202ffe",
    10: "#00a6ff",
    15: "#31f9f9",
    22: "#5fdb3c",
    26: "#ffdd00",
    30: "#ff6f00",
    40: "#ff4000",
}


def _get_temp_color(temp: float) -> str:
    temp_brackets = list(TEMP_COLORS.keys())
    if temp <= temp_brackets[0]:
        return TEMP_COLORS[temp_brackets[0]]

    for lower, upper in itertools.pairwise(temp_brackets):
        if lower < temp <= upper:
            return TEMP_COLORS[upper]

    return TEMP_COLORS[temp_brackets[-1]]


def _render_entry(entry: OpenWeatherCurrent | ForecastEntry) -> Panel:
    grid = Table.grid(expand=True)
    grid.add_column()
    grid.add_column()

    weather_category = entry.weather[0].main
    weather_color = WEATHER_COLORS.get(weather_category, "")
    weather_emoji = WEATHER_EMOJIS.get(weather_category, "")

    time_str = datetime.fromtimestamp(entry.dt).strftime(TIME_OUT_FMT)
    time = Text(time_str, style="bold")
    description = Text(f"{weather_emoji} {entry.weather[0].description}", style=f"bold {weather_color}")
    grid.add_row(Padding(description, (1, 0, 1, 0)))

    temp_color = _get_temp_color(entry.main.temp)
    temp = Text(f"{entry.main.temp:.1f}º", style=_get_temp_color(entry.main.temp))
    feeling = Text(f"{entry.main.feels_like:.1f}º", style=_get_temp_color(entry.main.feels_like))
    grid.add_row("Temperature", temp)
    grid.add_row("Feels like", feeling)

    rain_vol_hourly = entry.rain.volume
    snow_vol_hourly = entry.snow.volume

    if isinstance(entry, ForecastEntry):
        pop = Text(f"{100 * entry.pop:.2f}%", style=WEATHER_COLORS["Rain"])
        grid.add_row("Precipitation", pop)
        # Forecast rain and snow measures are accumulated for the last 3h
        rain_vol_hourly /= 3
        snow_vol_hourly /= 3

    rain_vol = Text(f"{100 * rain_vol_hourly:.2f}mm/h", style=WEATHER_COLORS["Rain"])
    snow_vol = Text(f"{100 * snow_vol_hourly:.2f}mm/h", style=WEATHER_COLORS["Snow"])

    if rain_vol_hourly > 0.0:
        grid.add_row("🌧️ Rain", rain_vol)
    if snow_vol_hourly > 0.0:
        grid.add_row("🌨️ Snow", snow_vol)

    return Panel(grid, width=ENTRY_PANEL_WIDTH, title=time, title_align="left", border_style=temp_color)


def _group_entries_by_day(data: OpenWeatherForecast) -> None:
    # Forecast entries are already sorted by date
    for date, group in itertools.groupby(data.forecast, key=lambda d: datetime.fromtimestamp(d.dt).date()):
        console.rule(title=f"[bold] {date.strftime(DATE_OUT_FMT)}", align="left", style="")
        console.print(
            Padding(
                Columns([_render_entry(entry) for entry in group]),
                pad=(1, 0, 1, 0),
            ),
        )


def render_current(city: str, country: str, data: OpenWeatherCurrent) -> None:
    date = datetime.fromtimestamp(data.dt).strftime(DATE_OUT_FMT)
    title = f"[bold]Current Weather in {city}, {country}, {date}"
    console.print(Padding(Panel(title), pad=(1, 0, 1, 0)))
    console.print(_render_entry(data), width=ENTRY_PANEL_WIDTH)


def render_forecast(city: str, country: str, data: OpenWeatherForecast) -> None:
    title = f"[bold]Weather forecast for {city}, {country}"
    console.print(Padding(Panel(title), pad=(1, 0, 1, 0)))
    _group_entries_by_day(data)
