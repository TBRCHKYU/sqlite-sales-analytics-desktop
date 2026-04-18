"""
Централизованный модуль применения современного минималистичного дизайна.
Поскольку ttk.Style является глобальным объектом, достаточно вызвать
apply_theme() один раз — и все последующие окна автоматически наследуют стили.
"""
from __future__ import annotations
from tkinter import ttk


# ─────────────────────────────────── colour helpers ──────────────────────────

def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    h = hex_color.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def _rgb_to_hex(r: float, g: float, b: float) -> str:
    return "#{:02X}{:02X}{:02X}".format(
        max(0, min(255, int(r))),
        max(0, min(255, int(g))),
        max(0, min(255, int(b))),
    )


def _mix(c1: str, c2: str, t: float) -> str:
    """Линейная смесь: t=1 → c1, t=0 → c2."""
    r1, g1, b1 = _hex_to_rgb(c1)
    r2, g2, b2 = _hex_to_rgb(c2)
    return _rgb_to_hex(
        r1 * t + r2 * (1 - t),
        g1 * t + g2 * (1 - t),
        b1 * t + b2 * (1 - t),
    )


def _lighten(c: str, amount: float = 0.12) -> str:
    return _mix("#FFFFFF", c, 1 - amount)


def _darken(c: str, amount: float = 0.12) -> str:
    r, g, b = _hex_to_rgb(c)
    return _rgb_to_hex(r * (1 - amount), g * (1 - amount), b * (1 - amount))


def _is_dark(c: str) -> bool:
    r, g, b = _hex_to_rgb(c)
    return (0.299 * r + 0.587 * g + 0.114 * b) / 255 < 0.5


def _btn_fg(btn_bg: str) -> str:
    return "#FFFFFF" if _is_dark(btn_bg) else "#111111"


# ─────────────────────────────────── main entry ──────────────────────────────

def apply_theme(style: ttk.Style, settings: dict) -> None:
    """
    Применяет современный плоский дизайн ко всем ttk-виджетам.
    Вызывать один раз при старте / после изменения настроек.
    """
    bg      = settings.get("background_color", "#F7F7F7")
    fg      = settings.get("text_color",       "#1A1A1A")
    accent  = settings.get("button_color",     "#1565C0")
    ff      = settings.get("font_family",      "Arial")
    fs      = int(settings.get("font_size",    12))

    a_fg     = _btn_fg(accent)
    a_hover  = _lighten(accent, 0.18)
    a_press  = _darken(accent, 0.14)
    bg_sub   = _darken(bg, 0.04) if not _is_dark(bg) else _lighten(bg, 0.06)
    bg_deep  = _darken(bg, 0.08) if not _is_dark(bg) else _lighten(bg, 0.12)
    border   = _darken(bg, 0.18) if not _is_dark(bg) else _lighten(bg, 0.22)
    muted_fg = _mix(fg, bg, 0.55)

    style.theme_use("clam")

    # ── глобальный базис ─────────────────────────────────────────────────────
    style.configure(".", font=(ff, fs), background=bg, foreground=fg,
                    relief="flat", borderwidth=0)

    # ── рамки ────────────────────────────────────────────────────────────────
    for name in ("TFrame", "Custom.TFrame"):
        style.configure(name, background=bg, relief="flat", borderwidth=0)

    # LabelFrame — тонкая линия, цветной заголовок
    style.configure("TLabelframe",
                    background=bg, relief="solid", borderwidth=1,
                    bordercolor=border)
    style.configure("TLabelframe.Label",
                    background=bg, foreground=fg,
                    font=(ff, fs, "bold"))
    style.configure("Custom.TLabelframe",
                    background=bg, relief="solid",
                    borderwidth=1, bordercolor=border)
    style.configure("Custom.TLabelframe.Label",
                    background=bg, foreground=fg,
                    font=(ff, fs, "bold"))

    # ── кнопки — плоские, акцентные ──────────────────────────────────────────
    _btn_opts = dict(
        background=accent, foreground=a_fg,
        relief="flat", borderwidth=0,
        font=(ff, fs),
        padding=(10, 6),
        focuscolor=accent,
    )
    style.configure("TButton", **_btn_opts)
    style.map("TButton",
              background=[("pressed", a_press), ("active", a_hover)],
              relief=[("pressed", "flat"), ("active", "flat")])

    for name in ("Date.TButton", "Accent.TButton"):
        style.configure(name, **{**_btn_opts, "padding": (8, 5)})
        style.map(name,
                  background=[("pressed", a_press), ("active", a_hover)],
                  relief=[("pressed", "flat"), ("active", "flat")])

    # ── Notebook ─────────────────────────────────────────────────────────────
    style.configure("TNotebook",
                    background=bg, borderwidth=0,
                    tabmargins=[0, 4, 0, 0])
    style.configure("TNotebook.Tab",
                    background=bg_sub, foreground=muted_fg,
                    padding=[14, 6], borderwidth=0,
                    font=(ff, fs))
    style.map("TNotebook.Tab",
              background=[("selected", accent), ("active", bg_deep)],
              foreground=[("selected", a_fg), ("active", fg)],
              font=[("selected", (ff, fs, "bold"))])

    # ── Treeview ─────────────────────────────────────────────────────────────
    style.configure("Treeview",
                    background=bg, foreground=fg,
                    fieldbackground=bg,
                    rowheight=26, borderwidth=0,
                    font=(ff, fs))
    style.configure("Treeview.Heading",
                    background=bg_sub, foreground=fg,
                    relief="flat", borderwidth=0,
                    font=(ff, fs, "bold"))
    style.map("Treeview",
              background=[("selected", accent)],
              foreground=[("selected", a_fg)])
    style.map("Treeview.Heading",
              background=[("active", bg_deep)])

    # ── Entry / Combobox ─────────────────────────────────────────────────────
    style.configure("TEntry",
                    fieldbackground=bg_sub, foreground=fg,
                    insertcolor=fg,
                    selectbackground=accent, selectforeground=a_fg,
                    relief="solid", borderwidth=1,
                    bordercolor=border, padding=(4, 3))
    style.configure("TCombobox",
                    fieldbackground=bg_sub, foreground=fg,
                    selectbackground=accent, selectforeground=a_fg,
                    relief="solid", borderwidth=1, padding=(4, 3))
    style.map("TCombobox",
              fieldbackground=[("readonly", bg_sub)],
              selectbackground=[("readonly", accent)])

    # ── Scrollbar — тонкая ───────────────────────────────────────────────────
    _sb = dict(troughcolor=bg_sub, background=border,
               borderwidth=0, arrowsize=12, relief="flat")
    style.configure("Vertical.TScrollbar", **_sb)
    style.configure("Horizontal.TScrollbar", **_sb)
    style.map("Vertical.TScrollbar",   background=[("active", a_hover)])
    style.map("Horizontal.TScrollbar", background=[("active", a_hover)])

    # ── метки ────────────────────────────────────────────────────────────────
    style.configure("Result.TLabel",
                    background=bg, foreground=fg, font=(ff, fs))
    style.configure("Muted.TLabel",
                    background=bg, foreground=muted_fg,
                    font=(ff, max(9, fs - 1)))
    style.configure("Title.TLabel",
                    background=bg, foreground=fg,
                    font=(ff, fs + 2, "bold"))
    style.configure("Hint.TLabel",
                    background=bg, foreground=muted_fg,
                    font=(ff, max(9, fs - 1)))

    # ── прочее ───────────────────────────────────────────────────────────────
    style.configure("TRadiobutton",
                    background=bg, foreground=fg, font=(ff, fs))
    style.configure("TSeparator", background=border)
    style.configure("TSpinbox",
                    fieldbackground=bg_sub, foreground=fg,
                    relief="solid", borderwidth=1)
