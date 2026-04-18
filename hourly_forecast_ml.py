"""
Почасовой прогноз сумм (продажи/закупки) с признаками дня недели, часа, режима работы и лагов.
Обучение: HistGradientBoostingRegressor; валидация — отложенные последние test_days календарных дней.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

import numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error

DEFAULT_FORECAST_SETTINGS: dict[str, Any] = {
    "default_open_hour": 9,
    "default_close_hour": 21,
    "per_dow_hours": None,
}

MIN_UNIQUE_DATES = 14
MIN_TRAIN_ROWS = 48


def default_forecast_settings() -> dict[str, Any]:
    return {
        "default_open_hour": int(DEFAULT_FORECAST_SETTINGS["default_open_hour"]),
        "default_close_hour": int(DEFAULT_FORECAST_SETTINGS["default_close_hour"]),
        "per_dow_hours": DEFAULT_FORECAST_SETTINGS["per_dow_hours"],
    }


def is_hour_open_for_dow(dow: int, hour: int, settings: dict[str, Any]) -> bool:
    """dow: понедельник=0 … воскресенье=6. Часы работы [open, close)."""
    per = settings.get("per_dow_hours") or {}
    key = str(dow)
    if key in per and isinstance(per[key], dict):
        o = int(per[key].get("open", settings.get("default_open_hour", 9)))
        c = int(per[key].get("close", settings.get("default_close_hour", 21)))
    else:
        o = int(settings.get("default_open_hour", 9))
        c = int(settings.get("default_close_hour", 21))
    if o < c:
        return o <= hour < c
    return False


def rows_to_totals_map(hourly_rows: list[dict]) -> dict[tuple[str, int], float]:
    m: dict[tuple[str, int], float] = {}
    for r in hourly_rows:
        key = (str(r["calendar_date"]), int(r["hour"]))
        m[key] = float(r.get("total", 0) or 0)
    return m


def check_time_degeneracy(hourly_rows: list[dict]) -> bool:
    """True, если все ненулевые суммы приходятся на один и тот же час (часто 0 — только дата)."""
    hours_with_sales = {int(r["hour"]) for r in hourly_rows if float(r.get("total", 0) or 0) > 0}
    if not hours_with_sales:
        return False
    return len(hours_with_sales) == 1 and 0 in hours_with_sales


def _parse(d: str) -> datetime:
    return datetime.strptime(d, "%Y-%m-%d")


def _fmt(d: datetime) -> str:
    return d.strftime("%Y-%m-%d")


def _daterange(d0: datetime, d1: datetime):
    d = d0
    while d <= d1:
        yield d
        d += timedelta(days=1)


def build_panel(
    start_date: str,
    end_date: str,
    totals: dict[tuple[str, int], float],
    forecast_settings: dict[str, Any],
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    d0, d1 = _parse(start_date), _parse(end_date)
    for d in _daterange(d0, d1):
        ds = _fmt(d)
        dow = d.weekday()
        for hour in range(24):
            y = float(totals.get((ds, hour), 0.0))
            is_op = is_hour_open_for_dow(dow, hour, forecast_settings)
            records.append(
                {
                    "date": ds,
                    "hour": hour,
                    "dow": dow,
                    "is_open": 1 if is_op else 0,
                    "y": y,
                }
            )
    for i, rec in enumerate(records):
        rec["y_lag_24"] = float(records[i - 24]["y"]) if i >= 24 else 0.0
        rec["y_lag_168"] = float(records[i - 168]["y"]) if i >= 168 else 0.0
    return records


def run_hourly_forecast(
    hourly_rows: list[dict],
    forecast_settings: dict[str, Any] | None,
    *,
    period_start: str,
    period_end: str,
    test_days: int = 14,
    forecast_target_date: str | None = None,
) -> dict[str, Any]:
    """
    hourly_rows: список из get_hourly_sales_totals.
    period_start, period_end: границы периода (YYYY-MM-DD), совпадают с запросом к БД.
    forecast_target_date: дата прогноза; по умолчанию — следующий день после period_end.
    """
    settings = forecast_settings if forecast_settings is not None else default_forecast_settings()

    if not hourly_rows:
        return {"ok": False, "error": "Нет почасовых данных за выбранный период."}

    degenerate = check_time_degeneracy(hourly_rows)

    totals = rows_to_totals_map(hourly_rows)
    unique_dates = sorted({str(r["calendar_date"]) for r in hourly_rows})
    if len(unique_dates) < MIN_UNIQUE_DATES:
        return {
            "ok": False,
            "error": (
                f"Недостаточно календарных дней с операциями: нужно не меньше {MIN_UNIQUE_DATES}, "
                f"получено {len(unique_dates)}. Расширьте период истории."
            ),
        }

    panel = build_panel(period_start, period_end, totals, settings)
    if len(panel) < MIN_TRAIN_ROWS:
        return {
            "ok": False,
            "error": f"Недостаточно точек панели (дата×час): нужно ≥{MIN_TRAIN_ROWS}, получено {len(panel)}.",
        }

    dates_sorted = sorted({rec["date"] for rec in panel})
    if test_days >= len(dates_sorted):
        test_days = max(1, len(dates_sorted) // 5)
    test_date_set = set(dates_sorted[-test_days:])
    train_mask = np.array([rec["date"] not in test_date_set for rec in panel], dtype=bool)
    test_mask = ~train_mask

    if train_mask.sum() < MIN_TRAIN_ROWS:
        return {
            "ok": False,
            "error": "После отложенной выборки слишком мало обучающих строк. Уменьшите число тестовых дней или расширьте период.",
        }

    X_cols = ["hour", "dow", "is_open", "y_lag_24", "y_lag_168"]
    X = np.array([[rec[c] for c in X_cols] for rec in panel], dtype=float)
    y = np.array([rec["y"] for rec in panel], dtype=float)

    model = HistGradientBoostingRegressor(
        max_depth=6,
        max_iter=150,
        learning_rate=0.08,
        random_state=42,
    )
    model.fit(X[train_mask], y[train_mask])

    y_pred_test = model.predict(X[test_mask])
    y_true_test = y[test_mask]
    test_mae = float(mean_absolute_error(y_true_test, y_pred_test))
    test_rmse = float(np.sqrt(mean_squared_error(y_true_test, y_pred_test)))

    last_data_date = _parse(period_end)
    if forecast_target_date:
        target = _parse(forecast_target_date)
    else:
        target = last_data_date + timedelta(days=1)

    target_str = _fmt(target)
    dow_t = target.weekday()

    hourly_out: list[dict[str, Any]] = []
    day_total_open = 0.0
    for hour in range(24):
        d_lag1 = target - timedelta(days=1)
        d_lag7 = target - timedelta(days=7)
        y_lag_24 = float(totals.get((_fmt(d_lag1), hour), 0.0))
        y_lag_168 = float(totals.get((_fmt(d_lag7), hour), 0.0))
        is_op = is_hour_open_for_dow(dow_t, hour, settings)
        x = np.array([[hour, dow_t, 1 if is_op else 0, y_lag_24, y_lag_168]], dtype=float)
        pred = float(max(0.0, model.predict(x)[0]))
        hourly_out.append(
            {
                "hour": hour,
                "predicted": pred,
                "is_open": bool(is_op),
            }
        )
        if is_op:
            day_total_open += pred

    return {
        "ok": True,
        "degenerate_time_warning": degenerate,
        "degenerate_time_message": (
            "Все ненулевые суммы попадают в 00:00 — проверьте, что в поле created_at сохраняется время сделки."
            if degenerate
            else None
        ),
        "test_mae": test_mae,
        "test_rmse": test_rmse,
        "forecast_date": target_str,
        "day_total_open_hours": day_total_open,
        "hourly_forecast": hourly_out,
        "train_rows": int(train_mask.sum()),
        "test_rows": int(test_mask.sum()),
        "test_days_used": int(len(test_date_set)),
        "period_start": period_start,
        "period_end": period_end,
    }
