from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

# Minimal publication-oriented defaults. No decorative styling.
plt.rcParams.update(
    {
        "figure.figsize": (7.2, 4.4),
        "figure.dpi": 120,
        "savefig.dpi": 200,
        "savefig.bbox": "tight",
        "font.size": 10,
        "axes.titlesize": 11,
        "axes.labelsize": 10,
        "legend.fontsize": 9,
        "axes.grid": True,
        "grid.alpha": 0.35,
        "lines.linewidth": 1.4,
    }
)


def save_figure(fig: plt.Figure, stem: Path) -> tuple[Path, Path]:
    """Write PNG and SVG next to stem (without suffix)."""
    stem.parent.mkdir(parents=True, exist_ok=True)
    png = stem.with_suffix(".png")
    svg = stem.with_suffix(".svg")
    fig.savefig(png)
    fig.savefig(svg)
    plt.close(fig)
    return png, svg
