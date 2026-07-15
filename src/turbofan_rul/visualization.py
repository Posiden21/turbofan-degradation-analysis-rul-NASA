"""SVG chart writers for portfolio-friendly RUL outputs."""

from __future__ import annotations

from pathlib import Path


def write_rul_trend_svg(path: Path, rows: list[dict[str, object]]) -> None:
    width, height = 960, 520
    margin_left, margin_right, margin_top, margin_bottom = 70, 40, 54, 64
    plot_w = width - margin_left - margin_right
    plot_h = height - margin_top - margin_bottom

    max_cycle = max(int(row["cycle"]) for row in rows)
    max_rul = max(int(row["rul"]) for row in rows)
    units = sorted({int(row["unit"]) for row in rows})
    colors = ["#3B82F6", "#F97316", "#22C55E", "#E11D48", "#8B5CF6", "#06B6D4"]

    def x_scale(cycle: int) -> float:
        return margin_left + (cycle / max_cycle) * plot_w

    def y_scale(rul: int) -> float:
        return margin_top + plot_h - (rul / max_rul) * plot_h if max_rul else margin_top + plot_h

    lines = [
        _svg_header(width, height),
        f'<rect width="{width}" height="{height}" fill="#111827"/>',
        f'<rect x="{margin_left}" y="{margin_top}" width="{plot_w}" height="{plot_h}" fill="#172033" stroke="#374151"/>',
        _text(30, 34, "Remaining Useful Life Trend", size=24, weight=700),
        _text(30, 500, "Operating cycle", size=14, fill="#CBD5E1"),
        _rotated_text(20, 330, "Remaining useful life", size=14, fill="#CBD5E1"),
    ]

    for threshold, color, label in [(2, "#EF4444", "critical"), (5, "#F59E0B", "warning")]:
        y = y_scale(threshold)
        lines.append(f'<line x1="{margin_left}" y1="{y:.1f}" x2="{margin_left + plot_w}" y2="{y:.1f}" stroke="{color}" stroke-dasharray="6 5" opacity="0.8"/>')
        lines.append(_text(margin_left + plot_w - 92, y - 8, label, size=12, fill=color))

    for tick in range(0, max_cycle + 1):
        x = x_scale(tick)
        lines.append(f'<line x1="{x:.1f}" y1="{margin_top + plot_h}" x2="{x:.1f}" y2="{margin_top + plot_h + 6}" stroke="#64748B"/>')
        lines.append(_text(x - 4, margin_top + plot_h + 24, str(tick), size=11, fill="#94A3B8"))

    for tick in range(0, max_rul + 1):
        y = y_scale(tick)
        lines.append(f'<line x1="{margin_left - 6}" y1="{y:.1f}" x2="{margin_left}" y2="{y:.1f}" stroke="#64748B"/>')
        lines.append(_text(margin_left - 34, y + 4, str(tick), size=11, fill="#94A3B8"))

    for index, unit in enumerate(units):
        unit_rows = sorted([row for row in rows if int(row["unit"]) == unit], key=lambda row: int(row["cycle"]))
        points = " ".join(f'{x_scale(int(row["cycle"])):.1f},{y_scale(int(row["rul"])):.1f}' for row in unit_rows)
        color = colors[index % len(colors)]
        lines.append(f'<polyline points="{points}" fill="none" stroke="{color}" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>')
        last = unit_rows[-1]
        lines.append(_text(x_scale(int(last["cycle"])) + 8, y_scale(int(last["rul"])) + 4, f"Engine {unit}", size=12, fill=color))

    lines.append("</svg>")
    path.write_text("\n".join(lines), encoding="utf-8")


def write_risk_bar_svg(path: Path, scores: list[dict[str, object]]) -> None:
    width, height = 960, 460
    margin_left, margin_right, margin_top, margin_bottom = 76, 40, 62, 78
    plot_w = width - margin_left - margin_right
    plot_h = height - margin_top - margin_bottom
    max_health = max(float(score["health_index"]) for score in scores)
    bar_gap = 24
    bar_w = (plot_w - bar_gap * (len(scores) - 1)) / len(scores)

    risk_colors = {"critical": "#EF4444", "warning": "#F59E0B", "monitor": "#22C55E"}
    lines = [
        _svg_header(width, height),
        f'<rect width="{width}" height="{height}" fill="#111827"/>',
        f'<rect x="{margin_left}" y="{margin_top}" width="{plot_w}" height="{plot_h}" fill="#172033" stroke="#374151"/>',
        _text(30, 38, "Latest Engine Health Risk", size=24, weight=700),
        _text(30, 438, "Higher health index indicates stronger degradation signal", size=13, fill="#CBD5E1"),
    ]

    for index, score in enumerate(scores):
        x = margin_left + index * (bar_w + bar_gap)
        value = float(score["health_index"])
        bar_h = (value / max_health) * (plot_h - 20)
        y = margin_top + plot_h - bar_h
        color = risk_colors.get(str(score["risk_band"]), "#94A3B8")
        lines.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_w:.1f}" height="{bar_h:.1f}" rx="4" fill="{color}"/>')
        lines.append(_text(x + bar_w / 2 - 18, y - 10, f"{value:.1f}", size=13, fill="#F8FAFC", weight=700))
        lines.append(_text(x + bar_w / 2 - 28, margin_top + plot_h + 26, f"Engine {score['unit']}", size=12, fill="#CBD5E1"))
        lines.append(_text(x + bar_w / 2 - 22, margin_top + plot_h + 46, f"RUL {score['remaining_useful_life']}", size=11, fill="#94A3B8"))

    lines.append("</svg>")
    path.write_text("\n".join(lines), encoding="utf-8")


def _svg_header(width: int, height: int) -> str:
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">'


def _text(x: float, y: float, text: str, *, size: int, fill: str = "#F8FAFC", weight: int = 400) -> str:
    return f'<text x="{x:.1f}" y="{y:.1f}" fill="{fill}" font-family="Arial, Helvetica, sans-serif" font-size="{size}" font-weight="{weight}">{text}</text>'


def _rotated_text(x: float, y: float, text: str, *, size: int, fill: str) -> str:
    return f'<text x="{x:.1f}" y="{y:.1f}" fill="{fill}" font-family="Arial, Helvetica, sans-serif" font-size="{size}" transform="rotate(-90 {x:.1f} {y:.1f})">{text}</text>'
