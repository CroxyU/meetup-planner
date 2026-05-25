"""Утилиты для построения сетки календаря месяца."""
import calendar
from datetime import date


def month_grid(year: int, month: int) -> list[tuple[date, bool]]:
    """
    Возвращает список (день, is_current_month).
    Сетка начинается с понедельника (ISO).
    """
    cal = calendar.Calendar(firstweekday=0)  # понедельник
    today = date.today()
    cells: list[tuple[date, bool]] = []

    for week in cal.monthdatescalendar(year, month):
        for d in week:
            cells.append((d, d.month == month))

    return cells


def format_dates_ru(days: list[date]) -> str:
    months = (
        "января", "февраля", "марта", "апреля", "мая", "июня",
        "июля", "августа", "сентября", "октября", "ноября", "декабря",
    )
    parts = [f"{d.day} {months[d.month - 1]}" for d in sorted(days)]
    if len(parts) == 1:
        return parts[0]
    if len(parts) == 2:
        return f"{parts[0]} и {parts[1]}"
    return ", ".join(parts[:-1]) + f" и {parts[-1]}"
