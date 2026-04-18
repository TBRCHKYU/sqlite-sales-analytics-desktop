"""
Единая подгонка размеров и позиции окон под размер экрана.
"""
from __future__ import annotations

import tkinter as tk

try:
    from screeninfo import get_monitors
except ImportError:
    get_monitors = None

DEFAULT_SCREEN_W = 1024
DEFAULT_SCREEN_H = 768
DEFAULT_MARGIN_RATIO = 0.92


def get_screen_size():
    """
    Возвращает (width, height) основного монитора.
    При ошибке или пустом списке — fallback.
    """
    if get_monitors is None:
        return DEFAULT_SCREEN_W, DEFAULT_SCREEN_H
    try:
        monitors = get_monitors()
        if not monitors:
            return DEFAULT_SCREEN_W, DEFAULT_SCREEN_H
        m = monitors[0]
        return int(m.width), int(m.height)
    except Exception:
        return DEFAULT_SCREEN_W, DEFAULT_SCREEN_H


def fit_size(desired_w: int, desired_h: int, screen_w: int | None = None,
             screen_h: int | None = None, margin_ratio: float = DEFAULT_MARGIN_RATIO):
    """
    Вписывает желаемый размер в долю экрана (с отступами).
    """
    if screen_w is None or screen_h is None:
        screen_w, screen_h = get_screen_size()
    max_w = max(320, int(screen_w * margin_ratio))
    max_h = max(240, int(screen_h * margin_ratio))
    w = min(max(1, desired_w), max_w)
    h = min(max(1, desired_h), max_h)
    return w, h


def place_geometry(widget: tk.Misc, desired_w: int, desired_h: int,
                   margin_ratio: float = DEFAULT_MARGIN_RATIO,
                   min_w: int | None = None, min_h: int | None = None):
    """
    Устанавливает geometry WxH+X+Y по центру экрана с учётом fit_size.
    Для Tk/Toplevel.
    """
    screen_w, screen_h = get_screen_size()
    w, h = fit_size(desired_w, desired_h, screen_w, screen_h, margin_ratio)
    x = max(0, (screen_w - w) // 2)
    y = max(0, (screen_h - h) // 2)
    widget.geometry(f"{w}x{h}+{x}+{y}")
    if min_w is not None and min_h is not None:
        mw = max(200, min(min_w, w))
        mh = max(150, min(min_h, h))
        try:
            widget.minsize(mw, mh)
        except tk.TclError:
            pass
    elif hasattr(widget, "minsize"):
        try:
            widget.minsize(min(400, w), min(300, h))
        except tk.TclError:
            pass


def place_geometry_as_pair(widget: tk.Misc, desired_w: int, desired_h: int,
                           side: str = "left",
                           margin_ratio: float = DEFAULT_MARGIN_RATIO):
    """Позиционирует окно в левой или правой половине экрана (в паре с соседним окном)."""
    pos = "L" if side in ("left", "L") else "R"
    w, h, x, y = geometry_for_side_panel(pos, desired_w, desired_h, margin_ratio)
    widget.geometry(f"{w}x{h}+{x}+{y}")
    try:
        widget.minsize(min(400, w), min(300, h))
    except tk.TclError:
        pass


def place_geometry_as_trio(widget: tk.Misc, desired_w: int, desired_h: int,
                            pos: str = "center",
                            margin_ratio: float = DEFAULT_MARGIN_RATIO,
                            gap: int = 8):
    """Позиционирует окно как одну из трёх панелей (left/center/right)."""
    screen_w, screen_h = get_screen_size()
    max_each = max(200, int((screen_w * margin_ratio - gap * 2) / 3))
    w = min(max(200, desired_w), max_each)
    h = min(max(200, desired_h), max(200, int(screen_h * margin_ratio)))
    y = max(0, (screen_h - h) // 2)
    total = w * 3 + gap * 2
    x0 = max(0, (screen_w - total) // 2)
    offsets = {"left": 0, "center": w + gap, "right": 2 * (w + gap)}
    x = x0 + offsets.get(pos, 0)
    widget.geometry(f"{w}x{h}+{x}+{y}")
    try:
        widget.minsize(min(300, w), min(200, h))
    except tk.TclError:
        pass


def geometry_for_side_panel(pos: str, desired_w: int = 800, desired_h: int = 600,
                            margin_ratio: float = DEFAULT_MARGIN_RATIO, gap: int = 8):
    """
    Для двух панелей L/R (как в items_window): возвращает (w, h, x, y) для левой или правой.
    pos — 'L' или 'R'.
    """
    screen_w, screen_h = get_screen_size()
    max_each = max(280, int((screen_w * margin_ratio - gap) / 2))
    w = min(desired_w, max_each)
    h = min(desired_h, max(200, int(screen_h * margin_ratio)))
    w = max(280, w)
    h = max(200, h)
    y = max(0, (screen_h - h) // 2)
    total = w * 2 + gap
    x0 = max(0, (screen_w - total) // 2)
    if pos == "L":
        x = x0
    else:
        x = x0 + w + gap
    return w, h, x, y
