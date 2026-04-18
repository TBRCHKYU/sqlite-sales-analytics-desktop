"""
Рекомендации по количеству товара на день на основе истории продаж:
среднее число проданных единиц в тот же день недели за выбранный период (округление вверх).
"""
from __future__ import annotations

import math
from collections import defaultdict
from datetime import datetime
from typing import Any


def recommend_daily_stock_from_sales_rows(
    daily_rows: list[dict],
    target_date: str,
) -> dict[str, Any]:
    """
    daily_rows: элементы с ключами calendar_date (YYYY-MM-DD), item_name, units.
    target_date: дата, на которую нужна рекомендация (YYYY-MM-DD).

    Returns:
        ok, items: [{item_name, recommended_qty, sample_days}], target_date, target_weekday_ru, message
    """
    if not daily_rows:
        return {"ok": False, "error": "Нет данных о продажах по позициям за выбранный период."}

    try:
        target_dt = datetime.strptime(target_date, "%Y-%m-%d")
    except ValueError:
        return {"ok": False, "error": "Неверная дата цели (ожидается YYYY-MM-DD)."}

    target_dow = target_dt.weekday()
    by_item: dict[str, list[int]] = defaultdict(list)

    for r in daily_rows:
        try:
            d = datetime.strptime(str(r["calendar_date"]), "%Y-%m-%d")
        except ValueError:
            continue
        if d.weekday() != target_dow:
            continue
        name = str(r.get("item_name") or "").strip()
        if not name:
            continue
        u = int(r.get("units", 0) or 0)
        if u < 0:
            continue
        by_item[name].append(u)

    if not by_item:
        return {
            "ok": False,
            "error": "В периоде нет продаж в выбранный день недели — расширьте историю или смените дату.",
        }

    items: list[dict[str, Any]] = []
    for name, vals in by_item.items():
        avg = sum(vals) / len(vals)
        rec = max(0, int(math.ceil(avg)))
        items.append(
            {
                "item_name": name,
                "recommended_qty": rec,
                "sample_days": len(vals),
            }
        )
    items.sort(key=lambda x: (-x["recommended_qty"], x["item_name"]))

    return {
        "ok": True,
        "items": items,
        "target_date": target_date,
        "target_weekday_index": target_dow,
    }
